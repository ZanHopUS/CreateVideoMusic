"""Offline forced alignment of supplied cue windows; sentence fallback is explicit."""

import hashlib
import importlib.util
import json
import math
import os
import sys
import wave
from pathlib import Path

os.environ.update(
    HF_HUB_OFFLINE="1",
    TRANSFORMERS_OFFLINE="1",
    HF_HUB_DISABLE_TELEMETRY="1",
    HF_HUB_DISABLE_IMPLICIT_TOKEN="1",
    DO_NOT_TRACK="1",
)
AUTHOR_SHA = "ed4178006be431a3f5b51558ec36e3e3557d51dd83e181d5c0d91c312537f83b"


def load_vi(directory):
    source = directory / "model_handling.py"
    if hashlib.sha256(source.read_bytes()).hexdigest() != AUTHOR_SHA:
        raise ValueError("Vietnamese model source hash differs from the reviewed architecture.")
    from transformers import Wav2Vec2Processor

    spec = importlib.util.spec_from_file_location("amvs_reviewed_vi_model", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    processor = Wav2Vec2Processor.from_pretrained(str(directory), local_files_only=True)
    model, loading = module.Wav2Vec2ForCTC.from_pretrained(
        str(directory), local_files_only=True, weights_only=True, output_loading_info=True
    )
    if any(
        loading.get(k) for k in ("missing_keys", "unexpected_keys", "mismatched_keys", "error_msgs")
    ):
        raise ValueError("Checkpoint architecture mismatch.")
    return model.to("cpu").eval(), {
        "language": "vi",
        "type": "huggingface",
        "dictionary": {c.lower(): n for c, n in processor.tokenizer.get_vocab().items()},
    }


def main():
    folder = Path(sys.argv[1]).resolve()
    config = json.loads((folder / "asr-input.json").read_text(encoding="utf-8"))
    os.environ["NLTK_DATA"] = config["nltkPath"]
    import nltk

    def forbid(*args, **kwargs):
        raise RuntimeError("Offline tokenizer missing; no download allowed.")

    nltk.download = forbid
    import numpy as np
    import torch
    import whisperx

    torch.set_num_threads(4)
    directory = Path(config["modelPath"])
    if config["language"] == "vi":
        model, metadata = load_vi(directory)
    else:
        model, metadata = whisperx.load_align_model(
            language_code="en", device="cpu", model_name=str(directory), model_cache_only=True
        )
        model.eval()
    with wave.open(str(folder / "audio.wav"), "rb") as file:
        audio = (
            np.frombuffer(file.readframes(file.getnframes()), dtype="<i2").astype(np.float32)
            / 32768
        )
    start, end = config["sourceStartTicks"], config["sourceEndTicks"]
    lines = []
    fallbacks = 0
    for index, line in enumerate(config["lines"]):
        line = {
            **line,
            "words": [],
            "alignmentStatus": "sentence",
            "status": "draft",
            "source": "aligner",
        }
        if line["sourceStartTicks"] >= start and line["sourceEndTicks"] <= end:
            try:
                with torch.inference_mode():
                    raw = whisperx.align(
                        [
                            {
                                "start": (line["sourceStartTicks"] - start) / 48000,
                                "end": (line["sourceEndTicks"] - start) / 48000,
                                "text": line["text"],
                            }
                        ],
                        model,
                        metadata,
                        audio,
                        "cpu",
                        interpolate_method="ignore",
                        return_char_alignments=False,
                    )
                words = []
                previous = line["sourceStartTicks"]
                for word in raw["word_segments"]:
                    if not all(
                        isinstance(word.get(k), (float, int)) and math.isfinite(word[k])
                        for k in ("start", "end", "score")
                    ):
                        raise ValueError("Untimed word")
                    a, b = start + round(word["start"] * 48000), start + round(word["end"] * 48000)
                    if a < previous or b <= a or b > line["sourceEndTicks"] or word["score"] < 0.25:
                        raise ValueError("Word bounds/uncalibrated screening failed")
                    words.append(
                        {
                            "text": word["word"].strip(),
                            "startTicks": a,
                            "endTicks": b,
                            "rawScore": word["score"],
                        }
                    )
                    previous = b
                if not words or len(words) != len(line["text"].split()):
                    raise ValueError("Incomplete units; sentence fallback")
                line["words"] = words
                line["alignmentStatus"] = "word"
            except Exception:
                pass
        if not line["words"]:
            fallbacks += 1
        lines.append(line)
        print(json.dumps({"progress": 0.1 + 0.75 * (index + 1) / len(config["lines"])}), flush=True)
    result = {
        "lines": lines,
        "provider": "whisperx-local",
        "language": config["language"],
        "model": config["model"],
        "timingSource": "forced alignment constrained to supplied cue windows; no interpolated words",
        "fallbackCount": fallbacks,
        "message": f"Đã căn {len(lines)} câu nháp; {fallbacks} câu giữ mốc câu. Cần duyệt độc lập; cutoff 0,25 chưa được hiệu chuẩn.",
    }
    (folder / "lyrics-result.json").write_text(
        json.dumps(result, ensure_ascii=False, allow_nan=False), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
