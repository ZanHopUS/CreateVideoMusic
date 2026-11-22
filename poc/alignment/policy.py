"""Conservative structural acceptance of draft word timing, not accuracy grading."""
import math
import re
import unicodedata


def units(text):
    normalized = unicodedata.normalize("NFC", text)
    return [word for word in normalized.split() if any(char.isalnum() for char in word)]


def classify(cue, words):
    expected = units(cue["text"])
    valid, issues = [], []
    for word in words:
        if not units(word.get("word", "")):
            continue
        start, end, score = word.get("start"), word.get("end"), word.get("score")
        if not all(isinstance(value, (int, float)) and math.isfinite(value)
                   for value in (start, end, score)):
            issues.append("missing_or_nonfinite_timing_or_score")
            continue
        if not (cue["start_s"] - 0.02 <= start < end <= cue["end_s"] + 0.02):
            issues.append("outside_cue_or_nonpositive_duration")
            continue
        if valid and start < valid[-1]["end"] - 0.02:
            issues.append("overlapping_word_timing")
            continue
        # This is an uncalibrated screening cutoff, not a probability of correctness.
        if score < 0.25:
            issues.append("low_alignment_score")
            continue
        valid.append(word)
    # A matching count alone cannot establish textual identity or acoustic correctness.
    meaningful_count = sum(bool(units(word.get("word", ""))) for word in words)
    if meaningful_count != len(expected) or len(valid) != len(expected):
        issues.append("incomplete_word_coverage")
    if [re.sub(r"\W", "", unicodedata.normalize("NFC", item["word"]), flags=re.UNICODE).casefold() for item in valid] != [
            re.sub(r"\W", "", token, flags=re.UNICODE).casefold() for token in expected]:
        issues.append("word_sequence_mismatch")
    return {"mode": "word_draft" if not issues and expected else "sentence_fallback",
            "expected_units": len(expected), "valid_units": len(valid),
            "issues": sorted(set(issues)), "accepted_words": valid,
            "review_required": True}


def self_test():
    cue = {"start_s": 1, "end_s": 3, "text": "Xin chào"}
    good = [{"word": "Xin", "start": 1.1, "end": 1.5, "score": 0.8},
            {"word": "chào", "start": 1.6, "end": 2.2, "score": 0.9}]
    assert classify(cue, good)["mode"] == "word_draft"
    assert classify({**cue, "text": "♪ Xin chào ♪"}, [{"word": "♪"}, *good, {"word": "♪"}])["mode"] == "word_draft"
    assert classify(cue, good[:1])["mode"] == "sentence_fallback"
    assert classify(cue, [{**good[0], "start": float("nan")}, good[1]])["mode"] == "sentence_fallback"
    assert classify(cue, [{**good[0], "start": 0.5}, good[1]])["mode"] == "sentence_fallback"
    assert classify(cue, [{**good[0], "score": 0.01}, good[1]])["mode"] == "sentence_fallback"
    assert classify(cue, [{**good[0], "word": "Sai"}, good[1]])["mode"] == "sentence_fallback"
    print("Alignment fallback policy regression checks passed")
