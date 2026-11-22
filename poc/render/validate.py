"""Decode real MP4 outputs; check metadata and synthetic click/flash alignment."""
import json
from pathlib import Path

import av
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
directory = ROOT / ".poc" / "evidence" / "poc-03"
settings = json.loads((directory / "render-results.json").read_text(encoding="utf-8"))
results = []
for case in settings:
    path = directory / f"{case['name']}.mp4"
    with av.open(str(path)) as container:
        video = container.streams.video[0]
        audio = container.streams.audio[0]
        metadata = {"width": video.width, "height": video.height,
                    "fps": float(video.average_rate), "video_codec": video.codec_context.name,
                    "audio_codec": audio.codec_context.name,
                    "sample_rate": audio.codec_context.sample_rate,
                    "video_duration_s": float(video.duration * video.time_base)}
        decoded_frames = 0
        flashes = []
        for frame in container.decode(video=0):
            decoded_frames += 1
            rgb = frame.to_ndarray(format="rgb24")
            # The marker is an opaque 20x20 white square in the top-right corner.
            if np.min(rgb[5:15, -15:-5]) > 230:
                flashes.append(float(frame.pts * frame.time_base))
    audio_events = []
    with av.open(str(path)) as container:
        for frame in container.decode(audio=0):
            values = frame.to_ndarray()
            mono = np.max(np.abs(values), axis=0)
            indices = np.flatnonzero(mono > 0.01)
            if indices.size:
                at = float(frame.pts * frame.time_base) + int(indices[0]) / frame.sample_rate
                if not audio_events or at - audio_events[-1] > 1:
                    audio_events.append(at)
    expected = [0, 5, 10]
    deviations = [{"expected_s": time,
                   "flash_error_ms": abs(flashes[index] - time) * 1000 if index < len(flashes) else None,
                   "click_error_ms": abs(audio_events[index] - time) * 1000 if index < len(audio_events) else None,
                   "av_delta_ms": abs(flashes[index] - audio_events[index]) * 1000
                   if index < len(flashes) and index < len(audio_events) else None}
                  for index, time in enumerate(expected)]
    metadata_pass = (metadata["width"] == case["width"] and metadata["height"] == case["height"]
                     and abs(metadata["fps"] - case["fps"]) < 0.001
                     and metadata["video_codec"] == "h264" and metadata["audio_codec"] == "aac"
                     and abs(metadata["video_duration_s"] - case["seconds"]) <= 1 / case["fps"]
                     and decoded_frames == round(case["seconds"] * case["fps"]))
    marker_pass = len(flashes) == 3 and len(audio_events) == 3 and all(
        item["av_delta_ms"] is not None and item["av_delta_ms"] <= 100 for item in deviations)
    result = {"name": case["name"], "metadata": metadata, "decoded_frames": decoded_frames,
              "flash_times": flashes, "audio_event_times": audio_events, "deviations": deviations,
              "metadata_pass": metadata_pass, "synthetic_marker_pass": marker_pass,
              "preview_fidelity_tested": False}
    results.append(result)
    print(json.dumps(result))
(directory / "validation.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
if not all(row["metadata_pass"] and row["synthetic_marker_pass"] for row in results):
    raise SystemExit(1)
