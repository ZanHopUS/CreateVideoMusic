"""Align supplied text within SRT cue windows; outputs remain unreviewed drafts."""
import argparse
import csv
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import sys
import time
import wave

ROOT = Path(__file__).resolve().parents[2]
LOCAL = ROOT / ".poc"
sys.path.insert(0, str(ROOT / "poc/lyrics"))
from evaluate import parse_srt
from transcribe import srt_time
from policy import classify, self_test

os.environ.update({"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1",
                   "HF_HUB_DISABLE_TELEMETRY": "1", "HF_HUB_DISABLE_IMPLICIT_TOKEN": "1",
                   "HF_HOME": str(LOCAL / "cache/huggingface-align"),
                   "NLTK_DATA": str(LOCAL / "cache/nltk"), "DO_NOT_TRACK": "1"})


def finite_json(value):
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {str(key): finite_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [finite_json(item) for item in value]
    return value


def save(path, value):
    path.write_text(json.dumps(finite_json(value), ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", choices=["vi-001", "en-001"], default="vi-001")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--limit-cues", type=int, help="Initial smoke only; omit for full reference")
    parser.add_argument("--run-id")
    parser.add_argument("--vi-loader", choices=["author", "standard"], default="author")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        import tempfile
        from vietnamese_loader import verify_source
        with tempfile.TemporaryDirectory() as temporary:
            changed_source = Path(temporary) / "model_handling.py"
            changed_source.write_text("raise AssertionError('must never execute')", encoding="utf-8")
            try:
                verify_source(changed_source)
            except RuntimeError:
                pass
            else:
                raise AssertionError("Changed author source was accepted")
        print("Changed-source rejection check passed")
        return
    import psutil

    run_id = args.run_id or (args.sample if args.limit_cues is None else f"{args.sample}-smoke-{args.limit_cues}")
    if not run_id or any(char not in "abcdefghijklmnopqrstuvwxyz0123456789-" for char in run_id):
        parser.error("Use a safe run ID containing lowercase letters, numbers or hyphens")
    directory = LOCAL / "evidence/poc-02" / run_id
    directory.mkdir(parents=True, exist_ok=True)
    available = psutil.virtual_memory().available
    if available < 3.25 * 1024**3:
        save(directory / "preflight.json", {"status": "deferred_low_available_ram",
            "available_bytes": available, "minimum_start_gib": 3.25,
            "reason": "Reserve headroom above the 2GiB system-available stop gate"})
        raise SystemExit(4)
    manifest = json.loads((LOCAL / "data/user" / f"{args.sample}.manifest.json").read_text(encoding="utf-8"))
    cues, warnings = parse_srt((LOCAL / "data/user" / f"{args.sample}.reference.srt").read_text(encoding="utf-8-sig"))
    excluded = {1, 2, 6, 9, 11, 12, 107, 108, 111} if args.sample == "en-001" else set()
    usable = [cue for cue in cues if cue["cue_id"] not in excluded]
    if args.limit_cues is not None:
        if args.limit_cues <= 0:
            parser.error("--limit-cues must be positive")
        usable = usable[:args.limit_cues]
    # Run one model and one cue at a time. Do not import the ASR/diarization stacks.
    import numpy as np
    import torch
    import nltk
    import whisperx

    torch.set_num_threads(4)
    torch.set_num_interop_threads(1)
    nltk.data.path = [str(LOCAL / "cache/nltk")]

    def forbid_download(*unused, **options):
        raise RuntimeError("Missing NLTK data; prepare offline tokenizer data before inference")
    nltk.download = forbid_download
    with wave.open(str(LOCAL / "data/user" / f"{args.sample}.16k.wav"), "rb") as source:
        if (source.getnchannels(), source.getsampwidth(), source.getframerate()) != (1, 2, 16000):
            raise ValueError("Prepared mono PCM16 16kHz audio is required")
        audio = np.frombuffer(source.readframes(source.getnframes()), dtype="<i2").astype(np.float32) / 32768
    duration = len(audio) / 16000
    if any(cue["end_s"] > duration + 0.02 for cue in usable):
        raise ValueError("Reference cue exceeds prepared audio")
    language = manifest["language"]
    model_info = json.loads((LOCAL / "evidence/poc-02" / f"model-{language}.json").read_text(encoding="utf-8"))
    began = time.perf_counter()
    loading_info = None
    if language == "vi" and args.vi_loader == "author":
        from vietnamese_loader import load
        model, metadata, loading_info = load(LOCAL / "models/align-vi")
        loader_name = "reviewed_hash_pinned_author_architecture"
    else:
        model, metadata = whisperx.load_align_model(language_code=language, device="cpu",
            model_name=str(LOCAL / "models" / f"align-{language}"), model_cache_only=True,
            model_dir=str(LOCAL / "cache/huggingface-align"))
        model.eval()
        loader_name = "whisperx_standard_huggingface"
    load_s = time.perf_counter() - began
    rows = []
    alignment_started = time.perf_counter()
    for cue in usable:
        started = time.perf_counter()
        raw, error = None, None
        try:
            with torch.inference_mode():
                raw = whisperx.align([{"start": cue["start_s"], "end": cue["end_s"], "text": cue["text"]}],
                    model, metadata, audio, "cpu", interpolate_method="ignore", return_char_alignments=True)
            words = raw["word_segments"]
        except Exception as exc:
            error = {"type": type(exc).__name__, "message": str(exc)}
            words = []
        decision = classify(cue, words)
        row = {"cue": cue, "decision": decision, "alignment": raw,
               "error": error, "alignment_s": time.perf_counter() - started,
               "fallback_timing_source": "user-provided SRT cue, not independently verified",
               "timing_source": "WhisperX forced alignment constrained to reference cue window"}
        rows.append(row)
        save(directory / "partial.json", rows)
        print(json.dumps({"cue_id": cue["cue_id"], "mode": decision["mode"],
                          "valid_units": decision["valid_units"], "expected_units": decision["expected_units"]}), flush=True)
    runtime_s = time.perf_counter() - alignment_started
    total = sum(row["decision"]["expected_units"] for row in rows)
    valid = sum(row["decision"]["valid_units"] for row in rows)
    summary = {"sample_id": args.sample, "run_id": run_id, "language": language,
        "source_audio_sha256": manifest["sha256"], "model": model_info,
        "prepared_audio_sha256": hashlib.sha256((LOCAL / "data/user" / f"{args.sample}.16k.wav").read_bytes()).hexdigest(),
        "reference_sha256": hashlib.sha256((LOCAL / "data/user" / f"{args.sample}.reference.srt").read_bytes()).hexdigest(),
        "versions": {package: importlib.metadata.version(package) for package in
            ["torch", "torchaudio", "whisperx", "transformers", "numpy"]},
        "device": "cpu", "torch_threads": 4, "model_load_s": load_s,
        "model_loader": loader_name, "model_loading_info": loading_info,
        "alignment_s": runtime_s, "processed_audio_s": duration, "rtf": runtime_s / duration,
        "reference_cue_count": len(cues), "attempted_cues": len(rows), "excluded_nonverbal_ids": sorted(excluded),
        "limited_smoke": args.limit_cues is not None, "parser_warnings": warnings,
        "interpolate_method": "ignore", "score_screening_cutoff_uncalibrated": 0.25,
        "expected_units": total, "structurally_valid_scored_units": valid,
        "structural_scored_coverage": valid / total if total else 0,
        "word_draft_cues": sum(row["decision"]["mode"] == "word_draft" for row in rows),
        "sentence_fallback_cues": sum(row["decision"]["mode"] == "sentence_fallback" for row in rows),
        "failed_cues": sum(row["error"] is not None for row in rows),
        "word_timing_accuracy": None, "sentence_timing_accuracy": None,
        "review_required": True, "reference_windows_constrain_result": True,
        "rows": rows}
    save(directory / "alignment.json", summary)
    events = []
    for row in rows:
        if row["decision"]["mode"] == "word_draft":
            events.extend((word["start"], word["end"], word["word"]) for word in row["decision"]["accepted_words"])
        else:
            cue = row["cue"]
            events.append((cue["start_s"], cue["end_s"], cue["text"]))
    (directory / "hybrid-draft.srt").write_text("\n\n".join(
        f"{index+1}\n{srt_time(start)} --> {srt_time(end)}\n{text}"
        for index, (start, end, text) in enumerate(events)) + "\n", encoding="utf-8")
    with (directory / "review.tsv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream, delimiter="\t")
        writer.writerow(["cue_id", "start_s", "end_s", "text", "mode", "valid_units", "expected_units", "issues", "reviewed"])
        for row in rows:
            cue, decision = row["cue"], row["decision"]
            writer.writerow([cue["cue_id"], cue["start_s"], cue["end_s"], cue["text"], decision["mode"],
                             decision["valid_units"], decision["expected_units"], ",".join(decision["issues"]), False])
    print(json.dumps({key: summary[key] for key in ("sample_id", "model_load_s", "alignment_s", "attempted_cues",
        "structural_scored_coverage", "word_draft_cues", "sentence_fallback_cues", "failed_cues")}), flush=True)
    if rows and summary["failed_cues"] == len(rows):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
