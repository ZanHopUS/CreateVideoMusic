"""Run local ASR on a user-provided development sample; no ground truth is assumed."""
import argparse
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
LOCAL = ROOT / ".poc"
os.environ.update({"HF_HUB_OFFLINE": "1", "HF_HUB_DISABLE_IMPLICIT_TOKEN": "1",
                   "HF_HUB_DISABLE_TELEMETRY": "1", "DO_NOT_TRACK": "1"})


def srt_time(seconds):
    total = round(seconds * 1000)
    milliseconds = total % 1000
    total //= 1000
    return f"{total // 3600:02}:{total // 60 % 60:02}:{total % 60:02},{milliseconds:03}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", default="vi-001")
    parser.add_argument("--model", choices=["small", "medium"], default="small")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--run-id")
    parser.add_argument("--no-vad", action="store_true")
    parser.add_argument("--max-seconds", type=float)
    args = parser.parse_args()
    if args.max_seconds is not None and not (0 < args.max_seconds <= 300):
        parser.error("PoC processing cap must be greater than zero and at most 300 seconds")
    if not args.sample or any(char not in "abcdefghijklmnopqrstuvwxyz0123456789-" for char in args.sample):
        parser.error("Use a sample ID containing lowercase letters, numbers or hyphens")
    manifest = json.loads((LOCAL / "data/user" / f"{args.sample}.manifest.json").read_text(encoding="utf-8"))
    source = LOCAL / "data/user" / f"{args.sample}.m4a"
    if hashlib.sha256(source.read_bytes()).hexdigest() != manifest["sha256"]:
        raise ValueError("Input audio differs from the recorded sample manifest")
    run_id = args.run_id or (args.sample if args.model == "small" else f"{args.sample}-{args.model}")
    if not run_id or any(char not in "abcdefghijklmnopqrstuvwxyz0123456789-" for char in run_id):
        parser.error("Use a safe run ID containing lowercase letters, numbers or hyphens")
    directory = LOCAL / "evidence/poc-01" / run_id
    directory.mkdir(parents=True, exist_ok=True)
    from faster_whisper import WhisperModel
    if args.seed is not None:
        import ctranslate2
        ctranslate2.set_random_seed(args.seed)

    started = time.perf_counter()
    model = WhisperModel(str(LOCAL / "models" / f"faster-whisper-{args.model}"), device="cpu",
                         compute_type="int8", cpu_threads=4, num_workers=1, local_files_only=True)
    load_seconds = time.perf_counter() - started
    inference_started = time.perf_counter()
    duration = manifest["duration_s"]
    audio_input = str(source)
    if args.max_seconds is not None and duration > args.max_seconds:
        from faster_whisper.audio import decode_audio
        audio_input = decode_audio(str(source), sampling_rate=16000)[:round(args.max_seconds * 16000)]
        duration = len(audio_input) / 16000
    segments, info = model.transcribe(audio_input, language=manifest["language"],
                                      beam_size=5, vad_filter=not args.no_vad,
                                      condition_on_previous_text=False, word_timestamps=False)
    rows = []
    for segment in segments:
        rows.append({"id": segment.id, "start_s": segment.start, "end_s": segment.end,
                     "text": segment.text.strip(), "avg_logprob": segment.avg_logprob,
                     "no_speech_prob": segment.no_speech_prob,
                     "timing_source": "ASR segment estimate; not forced alignment",
                     "reviewed": False})
        (directory / "segments.partial.json").write_text(
            json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"segments_received": len(rows), "source_position_s": segment.end}), flush=True)
    seconds = time.perf_counter() - inference_started
    issues = []
    for index, row in enumerate(rows):
        if not (0 <= row["start_s"] < row["end_s"] <= duration + 0.1):
            issues.append({"index": index, "issue": "segment outside source range"})
        if index and row["start_s"] < rows[index - 1]["end_s"] - 0.001:
            issues.append({"index": index, "issue": "overlapping segment times"})
    inventory_name = "model-inventory.json" if args.model == "small" else f"model-inventory-{args.model}.json"
    inventory = json.loads((LOCAL / "evidence/poc-00" / inventory_name).read_text())
    report = {"sample": manifest, "model": inventory["repo"], "model_size": args.model,
              "processed_start_s": 0, "processed_duration_s": duration,
              "model_revision": inventory["revision"],
              "device": "cpu", "compute_type": "int8", "threads": 4, "beam_size": 5,
              "random_seed": args.seed,
              "vad_filter": not args.no_vad, "condition_on_previous_text": False, "word_timestamps": False,
              "model_load_s": load_seconds, "inference_s": seconds, "rtf": seconds / duration,
              "duration_after_vad_s": info.duration_after_vad, "segments": rows,
              "decode_options": asdict(info.transcription_options),
              "timestamp_issues": issues, "ground_truth_available": False,
              "wer": None, "cer": None, "alignment_accuracy": None,
              "status": "draft; requires manual lyric and timing review; exploratory single-song result"}
    (directory / "transcript.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (directory / "draft.srt").write_text("\n\n".join(
        f"{index + 1}\n{srt_time(row['start_s'])} --> {srt_time(row['end_s'])}\n{row['text']}"
        for index, row in enumerate(rows)) + "\n", encoding="utf-8")
    (directory / "draft.txt").write_text("\n".join(row["text"] for row in rows) + "\n", encoding="utf-8")
    print(json.dumps({"sample_id": args.sample, "duration_s": duration, "segment_count": len(rows),
                      "model_load_s": load_seconds, "inference_s": seconds,
                      "rtf": seconds / duration, "timestamp_issues": len(issues)}), flush=True)


if __name__ == "__main__":
    main()
