"""Compare ASR drafts to a user-provided SRT without assuming its timing is gold."""
import argparse
import csv
import hashlib
import html
import json
from pathlib import Path
import re
import unicodedata

ROOT = Path(__file__).resolve().parents[2]
LOCAL = ROOT / ".poc"
TIMESTAMP = re.compile(r"^(\d{2,}):(\d{2}):(\d{2})[,.](\d{3})$")


def seconds(value):
    match = TIMESTAMP.fullmatch(value.strip())
    if not match:
        raise ValueError(f"Invalid SRT timestamp: {value}")
    hours, minutes, secs, milliseconds = map(int, match.groups())
    if minutes >= 60 or secs >= 60:
        raise ValueError("Invalid minutes or seconds in SRT")
    return hours * 3600 + minutes * 60 + secs + milliseconds / 1000


def parse_srt(text):
    text = text.lstrip("\ufeff").replace("\r\n", "\n").replace("\r", "\n").strip()
    cues, warnings, identifiers = [], [], set()
    for block in re.split(r"\n\s*\n", text):
        lines = block.splitlines()
        if len(lines) < 3 or not lines[0].strip().isdigit():
            raise ValueError("Expected numeric SRT cue ID, timing line and text")
        identifier = int(lines[0].strip())
        if identifier in identifiers:
            raise ValueError(f"Duplicate SRT cue ID: {identifier}")
        identifiers.add(identifier)
        timing = re.fullmatch(r"\s*(\S+)\s+-->\s+(\S+)\s*", lines[1])
        if not timing:
            raise ValueError(f"Invalid timing line in cue {identifier}")
        start, end = seconds(timing[1]), seconds(timing[2])
        if end <= start:
            raise ValueError(f"Non-positive duration in cue {identifier}")
        words = html.unescape(re.sub(r"<[^>]+>", "", " ".join(lines[2:]))).strip()
        if not words:
            raise ValueError(f"Empty text in cue {identifier}")
        if cues and start < cues[-1]["start_s"]:
            raise ValueError(f"Cues out of chronological order at cue {identifier}")
        if cues and start < cues[-1]["end_s"]:
            warnings.append({"cue_id": identifier, "warning": "overlap with preceding cue"})
        cues.append({"cue_id": identifier, "start_s": start, "end_s": end, "text": words})
    if not cues:
        raise ValueError("Empty SRT")
    return cues, warnings


def normalize(text):
    text = unicodedata.normalize("NFC", text).lower()
    return " ".join("".join(" " if unicodedata.category(char)[0] in "PS" else char
                            for char in text).split())


def edit_counts(reference, hypothesis):
    # Each cell: total edit distance, substitutions, deletions, insertions.
    previous = [(index, 0, 0, index) for index in range(len(hypothesis) + 1)]
    for row, expected in enumerate(reference, start=1):
        current = [(row, 0, row, 0)]
        for column, actual in enumerate(hypothesis, start=1):
            if expected == actual:
                current.append(previous[column - 1])
                continue
            cost, sub, delete, insert = previous[column - 1]
            substitution = (cost + 1, sub + 1, delete, insert)
            cost, sub, delete, insert = previous[column]
            deletion = (cost + 1, sub, delete + 1, insert)
            cost, sub, delete, insert = current[column - 1]
            insertion = (cost + 1, sub, delete, insert + 1)
            current.append(min((substitution, deletion, insertion), key=lambda cell: cell[0]))
        previous = current
    cost, substitutions, deletions, insertions = previous[-1]
    return {"distance": cost, "substitutions": substitutions, "deletions": deletions,
            "insertions": insertions}


def metrics(reference, hypothesis):
    ref, hyp = normalize(reference), normalize(hypothesis)
    if not ref:
        raise ValueError("Reference has no scoring units after normalization")
    words = edit_counts(ref.split(), hyp.split())
    characters = edit_counts(ref.replace(" ", ""), hyp.replace(" ", ""))
    return {"reference_whitespace_units": len(ref.split()),
            "hypothesis_whitespace_units": len(hyp.split()),
            "word_edits": words, "whitespace_unit_error_rate": words["distance"] / len(ref.split()),
            "reference_nonspace_characters": len(ref.replace(" ", "")),
            "character_edits": characters,
            "cer_nonspace": characters["distance"] / len(ref.replace(" ", ""))}


def self_test():
    assert edit_counts("a b c".split(), "a x c".split()) == {
        "distance": 1, "substitutions": 1, "deletions": 0, "insertions": 0}
    assert edit_counts(["a", "b"], []) == {
        "distance": 2, "substitutions": 0, "deletions": 2, "insertions": 0}
    assert edit_counts([], ["a"]) == {
        "distance": 1, "substitutions": 0, "deletions": 0, "insertions": 1}
    assert normalize("TIẾNG, Việt!") == normalize("tie\u0302\u0301ng việt")
    assert metrics("Đây là lời", "Đây là lời")["cer_nonspace"] == 0
    assert metrics("Đây là lời", "đây là lơi")["cer_nonspace"] > 0
    cues, warnings = parse_srt("\ufeff1\r\n00:00:01,000 --> 00:00:02,500\r\n<i>Xin</i>\r\nchào\r\n")
    assert len(cues) == 1 and cues[0]["text"] == "Xin chào" and not warnings
    try:
        parse_srt("1\n00:00:02,000 --> 00:00:01,000\nBad")
    except ValueError:
        pass
    else:
        raise AssertionError("Reverse timing was accepted")
    print("Scoring/parser regression checks passed")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--sample", default="vi-001")
    parser.add_argument("--runs", nargs="+", help="Explicit run IDs; defaults to the sample's VAD pair")
    parser.add_argument("--evaluation-id", help="Separate output ID so prior evaluations remain intact")
    parser.add_argument("--exclude-cues", default="",
                        help="Explicit non-verbal cue IDs for a supplementary comparison only")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    sample = args.sample
    if not sample or any(char not in "abcdefghijklmnopqrstuvwxyz0123456789-" for char in sample):
        parser.error("Use a safe sample ID containing lowercase letters, numbers or hyphens")
    reference_path = LOCAL / "data/user" / f"{sample}.reference.srt"
    manifest_path = LOCAL / "data/user" / f"{sample}.manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    raw = reference_path.read_bytes()
    cues, warnings = parse_srt(raw.decode("utf-8-sig"))
    try:
        excluded_ids = {int(value) for value in args.exclude_cues.split(",") if value.strip()}
    except ValueError:
        parser.error("Excluded cue IDs must be comma-separated integers")
    if excluded_ids - {cue["cue_id"] for cue in cues}:
        parser.error("Excluded cue ID not present in reference")
    outside = [cue["cue_id"] for cue in cues if cue["end_s"] > manifest["duration_s"] + 0.1]
    if outside:
        warnings.append({"cue_ids": outside, "warning": "reference beyond audio duration"})
    evaluation_id = args.evaluation_id or f"{sample}-reference-evaluation"
    run_ids = args.runs or [sample, f"{sample}-no-vad"]
    for identifier in [evaluation_id, *run_ids]:
        if not identifier or any(char not in "abcdefghijklmnopqrstuvwxyz0123456789-" for char in identifier):
            parser.error("Use safe run/evaluation IDs containing lowercase letters, numbers or hyphens")
    if len(run_ids) != len(set(run_ids)):
        parser.error("Run IDs must be unique")
    directory = LOCAL / "evidence/poc-01" / evaluation_id
    directory.mkdir(parents=True, exist_ok=True)
    reference_text = "\n".join(cue["text"] for cue in cues)
    verbal_reference = "\n".join(cue["text"] for cue in cues if cue["cue_id"] not in excluded_ids)
    reference_info = {"file": f"{sample}.reference.srt", "sha256": hashlib.sha256(raw).hexdigest(),
                      "source": "user supplied as original lyrics", "cue_count": len(cues),
                      "start_s": cues[0]["start_s"], "end_s": cues[-1]["end_s"],
                      "warnings": warnings, "text_role": "user-provided reference",
                      "timing_role": "supplied subtitle timing; not independently annotated word boundaries"}
    runs, review = [], []
    for name in run_ids:
        transcript = json.loads((LOCAL / "evidence/poc-01" / name / "transcript.json").read_text(encoding="utf-8"))
        if transcript["sample"]["sha256"] != manifest["sha256"]:
            raise ValueError("Transcript audio hash differs from the reference sample manifest")
        processed_start = transcript.get("processed_start_s", 0)
        processed_duration = transcript.get("processed_duration_s", manifest["duration_s"])
        if any(cue["start_s"] < processed_start or
               cue["end_s"] > processed_start + processed_duration + 0.1 for cue in cues):
            raise ValueError("Reference extends beyond processed audio; define a matched reference before scoring")
        hypothesis = "\n".join(segment["text"] for segment in transcript["segments"])
        runs.append({"run": name, "vad_filter": transcript["vad_filter"],
                     "model": transcript["model"], "model_revision": transcript["model_revision"],
                     "processed_start_s": processed_start, "processed_duration_s": processed_duration,
                     "text_comparison": metrics(reference_text, hypothesis),
                     "raw_hypothesis_text": hypothesis,
                     "raw_reference_text": reference_text})
        if excluded_ids:
            runs[-1]["supplementary_verbal_reference_comparison"] = metrics(verbal_reference, hypothesis)
        for cue in cues:
            overlapping = [segment for segment in transcript["segments"]
                           if segment["start_s"] < cue["end_s"] and segment["end_s"] > cue["start_s"]]
            review.append({"run": name, "cue_id": cue["cue_id"], "start_s": cue["start_s"],
                           "end_s": cue["end_s"], "reference": cue["text"],
                           "asr_overlapping_time": " / ".join(segment["text"] for segment in overlapping),
                           "reviewed_correction": "", "timing_review": ""})
    report = {"sample_id": sample, "reference": reference_info,
              "normalization": "Unicode NFC, lowercase, punctuation/symbols to spaces; keep Vietnamese accents",
              "word_unit": "whitespace-delimited, not semantic Vietnamese words",
              "cer_unit": "Unicode codepoints after NFC, spaces excluded",
              "supplementary_excluded_cue_ids": sorted(excluded_ids),
              "supplementary_policy": "explicitly classified non-verbal descriptions only; no automatic removal of parenthetical lyrics",
              "scope": "one exploratory song, whole processed-window text comparison; no timing accuracy or generalization claim",
              "runs": runs}
    (directory / "evaluation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    with (directory / "lyric-review.tsv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(review[0]), delimiter="\t")
        writer.writeheader()
        writer.writerows(review)
    (directory / "reference.txt").write_text(reference_text + "\n", encoding="utf-8")
    manifest["ground_truth"] = {**reference_info, "status": "text reference received; timing not independently verified"}
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"reference": reference_info,
                      "runs": [{"run": run["run"], **run["text_comparison"],
                                "supplementary": run.get("supplementary_verbal_reference_comparison")}
                               for run in runs]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
