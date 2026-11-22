"""Decode real MP4 outputs; check metadata and synthetic click/flash alignment."""
import json
import argparse
from pathlib import Path

import av
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser()
parser.add_argument('--matrix',action='store_true')
parser.add_argument('--directory',type=Path)
parser.add_argument('--strict-container-duration',action='store_true')
args = parser.parse_args()
directory = ROOT / ".poc" / "evidence" / "poc-03"
if args.matrix:
    directory = directory / 'preset-matrix'
if args.directory:
    directory = args.directory.resolve()
    assert directory.is_relative_to(ROOT / '.poc'), 'Evidence must stay inside .poc'
settings = json.loads((directory / "render-results.json").read_text(encoding="utf-8"))
if args.matrix:
    assert len(settings)==36 and len({row['name'] for row in settings})==36
    expected_cases = {(template, width, height, fps)
                      for template in ('TPL01', 'TPL02', 'TPL03')
                      for width, height in ((720, 1280), (1080, 1920), (1280, 720),
                                            (1920, 1080), (720, 720), (1080, 1080))
                      for fps in (30, 60)}
    assert {(row['template'], row['width'], row['height'], row['fps'])
            for row in settings} == expected_cases
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
                    "audio_channels": audio.codec_context.channels,
                    "audio_duration_s": float(audio.duration * audio.time_base),
                    "container_duration_s": container.duration / av.time_base,
                    "video_duration_s": float(video.duration * video.time_base)}
        decoded_frames = 0
        timestamp_errors = 0
        flashes = []
        for frame in container.decode(video=0):
            expected_pts = decoded_frames / case['fps']
            if frame.pts is None or abs(float(frame.pts * frame.time_base) - expected_pts) > 0.000001:
                timestamp_errors += 1
            decoded_frames += 1
            # Inspect the small YUV patch directly instead of converting every full
            # 1080p frame to RGB. FFmpeg may report full-range 4:2:0 as
            # yuvj420p; both formats have the same planar layout.
            assert frame.format.name in ('yuv420p', 'yuvj420p')
            y = np.frombuffer(frame.planes[0],dtype=np.uint8).reshape(frame.height,frame.planes[0].line_size)
            u = np.frombuffer(frame.planes[1],dtype=np.uint8).reshape((frame.height+1)//2,frame.planes[1].line_size)
            v = np.frombuffer(frame.planes[2],dtype=np.uint8).reshape((frame.height+1)//2,frame.planes[2].line_size)
            luminance=y[5:15,frame.width-15:frame.width-5]
            chroma_u=u[3:7,frame.width//2-7:frame.width//2-3].astype(int)
            chroma_v=v[3:7,frame.width//2-7:frame.width//2-3].astype(int)
            if np.min(luminance)>230 and np.max(np.abs(chroma_u-128))<8 and np.max(np.abs(chroma_v-128))<8:
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
                     and metadata['sample_rate'] == 48000 and timestamp_errors == 0
                     and abs(metadata["video_duration_s"] - case["seconds"]) <= 1 / case["fps"]
                     and decoded_frames == round(case["seconds"] * case["fps"]))
    marker_pass = len(flashes) == 3 and len(audio_events) == 3 and all(
        item["av_delta_ms"] is not None and item["av_delta_ms"] <= 100
        and item['flash_error_ms'] <= 100 and item['click_error_ms'] <= 100
        for item in deviations)
    result = {"name": case["name"], "metadata": metadata, "decoded_frames": decoded_frames,
              "flash_times": flashes, "audio_event_times": audio_events, "deviations": deviations,
              "timestamp_errors": timestamp_errors,
              "container_duration_within_one_frame": abs(metadata['container_duration_s'] - case['seconds']) <= 1 / case['fps'],
              "metadata_pass": metadata_pass, "synthetic_marker_pass": marker_pass,
              "preview_fidelity_tested": False}
    results.append(result)
    print(json.dumps(result))
(directory / "validation.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
if not all(row["metadata_pass"] and row["synthetic_marker_pass"] for row in results):
    raise SystemExit(1)
if args.strict_container_duration and not all(row['container_duration_within_one_frame'] for row in results):
    raise SystemExit(2)
