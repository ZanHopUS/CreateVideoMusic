"""Generate license-free image/audio for application integration tests."""

import math
import struct
import subprocess
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
    # A second, distinct generated image enables order/reference assertions.
    second = bytes(
        (byte ^ 0x5A) if index % (width * 3 + 1) else 0 for index, byte in enumerate(data)
    )
    (folder / "artwork-2.png").write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(second))
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


def prepare_video():
    import imageio_ffmpeg

    folder = ROOT / ".local/test-assets"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / "background.mp4"
    if not target.exists():
        subprocess.run(
            [
                imageio_ffmpeg.get_ffmpeg_exe(),
                "-hide_banner",
                "-loglevel",
                "error",
                "-n",
                "-f",
                "lavfi",
                "-i",
                "testsrc2=size=180x320:rate=30",
                "-t",
                "4",
                "-an",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                str(target),
            ],
            check=True,
        )
    return target


if __name__ == "__main__":
    print(prepare())


def prepare_vfr():
    """Generated 15/30FPS red/blue VFR input for application trim/rate regression."""
    import imageio_ffmpeg

    folder = ROOT / ".local/test-assets"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / "vfr-red-blue.mp4"
    if not target.exists():
        subprocess.run(
            [
                imageio_ffmpeg.get_ffmpeg_exe(),
                "-hide_banner",
                "-loglevel",
                "error",
                "-n",
                "-f",
                "lavfi",
                "-i",
                "color=c=red:s=180x320:r=15:d=1",
                "-f",
                "lavfi",
                "-i",
                "color=c=blue:s=180x320:r=30:d=1",
                "-filter_complex",
                "[0:v][1:v]concat=n=2:v=1:a=0[v]",
                "-map",
                "[v]",
                "-fps_mode",
                "vfr",
                "-c:v",
                "libx264",
                "-preset",
                "ultrafast",
                "-pix_fmt",
                "yuv420p",
                str(target),
            ],
            check=True,
        )
    return target
