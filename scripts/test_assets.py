"""Generate license-free image/audio for application integration tests."""

import math
import struct
import wave
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def prepare():
    folder = ROOT / ".local/test-assets"
    folder.mkdir(parents=True, exist_ok=True)
    width, height = 180, 320
    data = b"".join(
        b"\0"
        + bytes(
            v
            for x in range(width)
            for v in (
                int(50 + 110 * y / height),
                int(50 + 40 * x / width),
                int(130 + 60 * y / height),
            )
        )
        for y in range(height)
    )

    def chunk(kind, payload):
        return (
            struct.pack(">I", len(payload))
            + kind
            + payload
            + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
        )

    (folder / "artwork.png").write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(data))
        + chunk(b"IEND", b"")
    )
    rate = 48000
    with wave.open(str(folder / "control.wav"), "wb") as audio:
        audio.setparams((1, 2, rate, 0, "NONE", "not compressed"))
        for second in range(4):
            audio.writeframes(
                b"".join(
                    struct.pack(
                        "<h", round(7000 * math.sin(2 * math.pi * 440 * (second * rate + i) / rate))
                    )
                    for i in range(rate)
                )
            )
    return folder


if __name__ == "__main__":
    print(prepare())
