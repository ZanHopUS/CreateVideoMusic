"""Decode user inputs once with the proven ASR environment, cap at 300 seconds."""
import json
from pathlib import Path
import wave

from faster_whisper.audio import decode_audio
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
for sample in ("vi-001", "en-001"):
    directory = ROOT / ".poc/data/user"
    manifest = json.loads((directory / f"{sample}.manifest.json").read_text(encoding="utf-8"))
    audio = decode_audio(str(directory / f"{sample}.m4a"), sampling_rate=16000)[:16000 * 300]
    target = directory / f"{sample}.16k.wav"
    with wave.open(str(target), "wb") as output:
        output.setparams((1, 2, 16000, 0, "NONE", "not compressed"))
        output.writeframes((np.clip(audio, -1, 1) * 32767).astype("<i2").tobytes())
    print(json.dumps({"sample": sample, "source_sha256": manifest["sha256"],
                      "processed_seconds": len(audio) / 16000, "format": "mono PCM16 16000Hz"}))
