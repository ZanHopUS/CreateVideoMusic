"""Offline ASR child. Invoked only by the API with owned job files."""

import hashlib
import json
import math
import os
import sys
import uuid
from importlib.metadata import version
from pathlib import Path

os.environ.update(
    HF_HUB_OFFLINE="1",
    TRANSFORMERS_OFFLINE="1",
    HF_HUB_DISABLE_TELEMETRY="1",
    HF_HUB_DISABLE_IMPLICIT_TOKEN="1",
    DO_NOT_TRACK="1",
)


def main():
    folder = Path(sys.argv[1]).resolve()
    config = json.loads((folder / "asr-input.json").read_text(encoding="utf-8"))
    from faster_whisper import WhisperModel

    model = WhisperModel(
        config["modelPath"],
        device="cpu",
        compute_type="int8",
        cpu_threads=4,
        num_workers=1,
        local_files_only=True,
    )
    segments, _ = model.transcribe(
        str(folder / "audio.wav"),
        language=config["language"],
        beam_size=5,
        vad_filter=True,
        condition_on_previous_text=False,
        word_timestamps=True,
    )
    lines = []
    offset = config["sourceStartTicks"]
    limit = config["sourceEndTicks"]
    for segment in segments:
        print(
            json.dumps(
                {"progress": min(0.85, 0.1 + segment.end / max(1, (limit - offset) / 48000) * 0.75)}
            ),
            flush=True,
        )
        if segment.no_speech_prob > 0.6 or segment.avg_logprob < -1 or not segment.text.strip():
            continue
        start, end = (
            max(offset, offset + round(segment.start * 48000)),
            min(limit, offset + round(segment.end * 48000)),
        )
        if end <= start:
            continue
        words, previous = [], start
        for word in segment.words or []:
            if not all(math.isfinite(v) for v in (word.start, word.end, word.probability)):
                words = []
                break
            a, b = offset + round(word.start * 48000), offset + round(word.end * 48000)
            if a < previous or b <= a or b > end or not word.word.strip():
                words = []
                break
            words.append(
                {
                    "text": word.word.strip(),
                    "startTicks": a,
                    "endTicks": b,
                    "rawScore": word.probability,
                }
            )
            previous = b
        lines.append(
            {
                "id": uuid.uuid4().hex,
                "text": segment.text.strip(),
                "sourceStartTicks": start,
                "sourceEndTicks": end,
                "source": "asr",
                "status": "draft",
                "alignmentStatus": "word" if words else "sentence",
                "words": words,
            }
        )
    result = {
        "lines": lines,
        "message": "Bản nháp ASR cần kiểm tra lời và mốc thời gian; rawScore chưa được hiệu chuẩn."
        if lines
        else "Không tìm thấy lời đủ rõ. Có thể là nhạc không giọng; hãy nhập lời hoặc thử lại đoạn khác.",
        "provider": "faster-whisper-local",
        "model": config["model"],
        "language": config["language"],
        "timingSource": "ASR word timestamps; not forced alignment",
    }
    digest = hashlib.sha256()
    with (Path(config["modelPath"]) / "model.bin").open("rb") as model_file:
        for chunk in iter(lambda: model_file.read(1024 * 1024), b""):
            digest.update(chunk)
    result["provenance"] = {
        "modelBinarySha256": digest.hexdigest(),
        "fasterWhisperVersion": version("faster-whisper"),
        "computeType": "int8",
        "device": "cpu",
        "wordScoresCalibrated": False,
    }
    target = folder / "lyrics-result.json"
    target.write_text(json.dumps(result, ensure_ascii=False, allow_nan=False), encoding="utf-8")


if __name__ == "__main__":
    main()
