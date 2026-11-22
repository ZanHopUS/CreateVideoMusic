"""Compare completed, matched CPU ASR runs without passing lyrics into inference."""
import hashlib
import json
from pathlib import Path

from evaluate import metrics, parse_srt

ROOT = Path(__file__).resolve().parents[2]
LOCAL = ROOT / ".poc"


def main():
    manifest = json.loads((LOCAL / "data/user/vi-001.manifest.json").read_text(encoding="utf-8"))
    source = LOCAL / "data/user/vi-001.m4a"
    assert hashlib.sha256(source.read_bytes()).hexdigest() == manifest["sha256"]
    reference = LOCAL / "data/user/vi-001.reference.srt"
    cues, warnings = parse_srt(reference.read_text(encoding="utf-8-sig"))
    text = "\n".join(cue["text"] for cue in cues)
    rows = []
    contract = None
    for size in ("small", "medium"):
        run_id = f"vi-001-{size}-seeded"
        base = LOCAL / "evidence/poc-01" / run_id
        run = json.loads((base / "transcript.json").read_text(encoding="utf-8"))
        assert run["sample"]["sha256"] == manifest["sha256"] and run["sample"]["language"] == "vi"
        assert run["model_size"] == size and run["vad_filter"] is False
        settings = {key: run[key] for key in ("processed_start_s", "processed_duration_s", "device",
            "compute_type", "threads", "beam_size", "condition_on_previous_text", "word_timestamps", "random_seed", "decode_options")}
        assert settings["random_seed"] == 42 and settings["device"] == "cpu" and settings["compute_type"] == "int8"
        if contract is None:
            contract = settings
        else:
            assert settings == contract, "Decode settings/time ranges differ between models"
        assert all(cue["end_s"] <= run["processed_duration_s"] + 0.1 for cue in cues)
        resources = json.loads((base / "resources/resources.json").read_text())
        assert resources["exit_code"] == 0 and resources["abort_reason"] is None
        hypothesis = "\n".join(segment["text"] for segment in run["segments"])
        rows.append({"run_id": run_id, "model": run["model"], "revision": run["model_revision"],
                     "metrics": metrics(text, hypothesis), "segments": len(run["segments"]),
                     "model_load_s": run["model_load_s"], "inference_s": run["inference_s"], "rtf": run["rtf"],
                     "timestamp_issues": run["timestamp_issues"],
                     "private_peak_gib": max(item["private_bytes"] for item in resources["samples"]) / 1024**3,
                     "available_min_gib": min(item["system_available_bytes"] for item in resources["samples"]) / 1024**3})
    small, medium = rows
    report = {"sample_id": "vi-001", "source_sha256": manifest["sha256"],
              "reference_sha256": hashlib.sha256(reference.read_bytes()).hexdigest(),
              "reference_cues": len(cues), "reference_warnings": warnings,
              "comparison_contract": contract, "runs": rows,
              "medium_minus_small_wer_points": 100 * (medium["metrics"]["whitespace_unit_error_rate"] - small["metrics"]["whitespace_unit_error_rate"]),
              "medium_minus_small_cer_points": 100 * (medium["metrics"]["cer_nonspace"] - small["metrics"]["cer_nonspace"]),
              "medium_inference_time_multiple": medium["inference_s"] / small["inference_s"],
              "scope": "single-song matched screening runs; not held-out, not a cold/warm median or accuracy guarantee",
              "reference_used_as_prompt": False, "correction_time_measured": False}
    output = LOCAL / "evidence/poc-01/vi-001-model-comparison"
    output.mkdir(parents=True, exist_ok=True)
    (output / "comparison.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
