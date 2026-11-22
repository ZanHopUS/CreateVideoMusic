"""Validate the actual review MP4 and audio crop; not acoustic lyric accuracy."""
from fractions import Fraction
import json
from pathlib import Path
import subprocess
import wave

import av
import imageio_ffmpeg
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
LOCAL = ROOT / ".poc"
directory = LOCAL / "evidence/poc-03/vi-lyrics-review"
movie = directory / "vi-lyrics-review.mp4"
payload = json.loads((directory / "input.json").read_text(encoding="utf-8"))
checks = json.loads((directory / "timing-checks.json").read_text())
probe = ROOT / "poc/render/node_modules/@remotion/compositor-win32-x64-msvc/ffprobe.exe"
metadata = json.loads(subprocess.check_output([str(probe), "-v", "error", "-show_format", "-show_streams", "-of", "json", str(movie)]))
(directory / "ffprobe.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
video = next(stream for stream in metadata["streams"] if stream["codec_type"] == "video")
audio = next(stream for stream in metadata["streams"] if stream["codec_type"] == "audio")
assert (video["width"], video["height"], video["codec_name"]) == (720, 1280, "h264")
assert Fraction(video["avg_frame_rate"]) == payload["fps"]
assert audio["codec_name"] == "aac" and int(audio["sample_rate"]) == 48000
assert abs(float(video["duration"]) - payload["frames"] / payload["fps"]) < 1 / payload["fps"]
frame_count, color_checks, underline_checks = 0, {}, {}
with av.open(str(movie)) as container:
    for frame_count, frame in enumerate(container.decode(video=0), start=1):
        index = frame_count - 1
        if index in (checks["wordFrame"], checks["fallbackFrame"]):
            rgb = frame.to_ndarray(format="rgb24")[580:840, 48:672].astype(float)
            red, green, blue = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
            gold = (red > 175) & (green > 130) & (blue < 160) & (red > green * 1.08) & (green > blue * 1.2)
            color_checks[str(index)] = int(gold.sum())
            longest = 0
            for line in gold:
                edges = np.flatnonzero(np.diff(np.r_[0, line.astype(np.int8), 0]))
                if edges.size:
                    longest = max(longest, int(np.diff(edges.reshape(-1, 2), axis=1).max()))
            underline_checks[str(index)] = longest
assert frame_count == payload["frames"]
assert color_checks[str(checks["wordFrame"])] > 50
# Font subpixel antialiasing/4:2:0 encoding can create isolated gold-like edge pixels
# on white glyphs. Test the contiguous active-word underline instead of zero pixels.
assert underline_checks[str(checks["wordFrame"])] >= 40
assert underline_checks[str(checks["fallbackFrame"])] < 40

ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
sources = {"reference": LOCAL / "render/lyrics-review-public/review-audio.wav", "rendered": movie}
signals = {}
for label, source in sources.items():
    output = directory / f"audio-check-{label}.wav"
    subprocess.run([ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", str(source),
                    "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(output)], check=True)
    with wave.open(str(output), "rb") as stream:
        signals[label] = np.frombuffer(stream.readframes(stream.getnframes()), dtype="<i2").astype(float) / 32768
correlations = []
for start in (1, 15, 30):
    first = start * 16000
    reference = signals["reference"][first:first + 32000]
    rendered = signals["rendered"][first:first + 32000]
    assert len(reference) == len(rendered) == 32000
    reference = reference - reference.mean()
    rendered = rendered - rendered.mean()
    nfft = 1 << (2 * len(reference) - 1).bit_length()
    values = np.fft.irfft(np.fft.rfft(reference, nfft) * np.conj(np.fft.rfft(rendered, nfft)), nfft)
    lags = np.arange(nfft)
    lags[lags > nfft // 2] -= nfft
    candidates = np.flatnonzero(np.abs(lags) <= 1600)
    best = candidates[np.argmax(values[candidates])]
    lag_ms = abs(float(lags[best])) / 16
    coefficient = float(values[best] / (np.linalg.norm(reference) * np.linalg.norm(rendered)))
    assert lag_ms <= 100 and coefficient >= 0.90
    correlations.append({"window_start_s": start, "absolute_offset_ms": lag_ms, "normalized_correlation": coefficient})
report = {"metadata": "passed", "decoded_frames": frame_count, "expected_frames": payload["frames"],
          "highlight_pixel_checks": color_checks, "highlight_underline_runs": underline_checks,
          "audio_crop_correlation": correlations,
          "source_start_s": payload["sourceStart"], "source_end_s": payload["sourceEnd"],
          "human_lyric_timing_review": "not performed", "word_timing_accuracy": None,
          "scope": "export integrity, correct word/fallback visual state and audio crop preservation"}
(directory / "validation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
