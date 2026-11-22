"""Generate render fixtures locally, without third-party recordings."""
import json
import math
from pathlib import Path
import struct
import subprocess
import wave

import imageio_ffmpeg

ROOT = Path(__file__).resolve().parents[2]
directory = ROOT / ".poc" / "render" / "public"
directory.mkdir(parents=True, exist_ok=True)
rate = 48000
with wave.open(str(directory / "control.wav"), "wb") as output:
    output.setparams((1, 2, rate, 0, "NONE", "not compressed"))
    # Short click at t=0/5/10 seconds; matching white flash in the composition.
    pcm = bytearray()
    for index in range(rate * 15):
        position = index % (rate * 5)
        value = 0.25 * math.sin(2 * math.pi * 880 * index / rate) if position < rate * 0.02 else 0
        pcm.extend(struct.pack("<h", int(value * 32767)))
    output.writeframes(pcm)
ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
command = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi",
           "-i", "testsrc2=size=360x640:rate=30:duration=15", "-an", "-c:v", "libx264",
           "-preset", "ultrafast", "-pix_fmt", "yuv420p", str(directory / "background.mp4")]
subprocess.run(command, check=True)
(directory / "provenance.json").write_text(json.dumps({
    "origin": "generated locally", "audio": "PCM sine clicks at 0,5,10s",
    "video": "FFmpeg lavfi testsrc2", "third_party_recording": False,
    "command": command,
}, indent=2), encoding="utf-8")
print("Generated local audio/video render fixtures")
