"""Validate real alignment exports and provenance; does not grade acoustic accuracy."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
LOCAL = ROOT / ".poc"
sys.path.insert(0, str(ROOT / "poc/lyrics"))
from evaluate import parse_srt


def reject_nonfinite(value):
    raise ValueError(f"Nonstandard JSON numeric constant: {value}")


def main():
    results = []
    for run_id, expected_cues in (("vi-001-author", 68), ("en-001", 102)):
        directory = LOCAL / "evidence/poc-02" / run_id
        report = json.loads((directory / "alignment.json").read_text(encoding="utf-8"),
                            parse_constant=reject_nonfinite)
        assert report["device"] == "cpu" and report["versions"]["torch"].endswith("+cpu")
        assert report["interpolate_method"] == "ignore" and report["review_required"]
        assert len(report["rows"]) == expected_cues and not report["limited_smoke"]
        assert len({row["cue"]["cue_id"] for row in report["rows"]}) == expected_cues
        assert all(row["decision"]["review_required"] for row in report["rows"])
        sample = report["sample_id"]
        reference = LOCAL / "data/user" / f"{sample}.reference.srt"
        assert hashlib.sha256(reference.read_bytes()).hexdigest() == report["reference_sha256"]
        if report["language"] == "vi":
            loading = report["model_loading_info"]["loading_info"]
            assert all(not loading.get(key) for key in ("missing_keys", "unexpected_keys", "mismatched_keys", "error_msgs"))
        exported, warnings = parse_srt((directory / "hybrid-draft.srt").read_text(encoding="utf-8-sig"))
        event_count = sum(len(row["decision"]["accepted_words"])
                          if row["decision"]["mode"] == "word_draft" else 1 for row in report["rows"])
        assert len(exported) == event_count
        assert all(0 <= cue["start_s"] < cue["end_s"] <= report["processed_audio_s"] + 0.02 for cue in exported)
        result = {"run_id": run_id, "reference_cues_attempted": len(report["rows"]),
                  "exported_srt_events": len(exported), "srt_overlap_warnings": warnings,
                  "provenance_and_export_checks": "passed", "timing_accuracy_evaluated": False}
        results.append(result)
        print(json.dumps(result))
    (LOCAL / "evidence/poc-02/export-validation.json").write_text(json.dumps(results, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
