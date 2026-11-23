"""Independently decode outputs of the latest passing disposable browser run."""

import hashlib
import json
import sqlite3
from pathlib import Path

import av

ROOT = Path(__file__).resolve().parents[1]


def main():
    passed = []
    for folder in (ROOT / ".local/e2e").iterdir():
        file = folder / "results.json"
        if file.is_file():
            stats = json.loads(file.read_text(encoding="utf-8")).get("stats", {})
            if stats.get("expected", 0) > 0 and stats.get("unexpected", 0) == 0:
                passed.append(folder)
    if not passed:
        raise RuntimeError("No passing browser run to validate")
    folder = sorted(passed)[-1]
    database = sqlite3.connect(folder / "workspace/runtime/studio.sqlite")
    try:
        jobs = [json.loads(row[0]) for row in database.execute("SELECT body FROM jobs")]
    finally:
        database.close()
    rows = []
    for job in jobs:
        if job["status"] != "succeeded":
            continue
        output = Path(job["outputFile"]).resolve()
        if not output.is_relative_to(folder.resolve()):
            raise ValueError("Output escaped test workspace")
        project = job["project"]
        preset = project["preset"]
        with av.open(str(output)) as media:
            video, audio = media.streams.video[0], media.streams.audio[0]
            seconds = media.duration / av.time_base
            assert video.codec_context.name == "h264" and audio.codec_context.name == "aac"
            assert (video.width, video.height) == (preset["width"], preset["height"])
            assert float(video.average_rate) == preset["fps"]
            assert abs(seconds - project["durationTicks"] / 48000) <= 1 / preset["fps"]
            count = errors = 0
            for frame in media.decode(video=0):
                if abs(float(frame.pts * frame.time_base) - count / preset["fps"]) > 0.000001:
                    errors += 1
                if count == preset["fps"]:
                    png = folder / "output-frame-30.png"
                    if not png.exists():
                        with av.open(str(png), "w", format="image2") as destination:
                            stream = destination.add_stream("png")
                            stream.width, stream.height = frame.width, frame.height
                            stream.pix_fmt = "rgb24"
                            rgb = frame.reformat(format="rgb24")
                            rgb.pts = None
                            for packet in stream.encode(rgb):
                                destination.mux(packet)
                            for packet in stream.encode():
                                destination.mux(packet)
                count += 1
            assert count == round(project["durationTicks"] * preset["fps"] / 48000) and errors == 0
        with av.open(str(output)) as media:
            audio_samples = sum(frame.samples for frame in media.decode(audio=0))
            assert audio_samples > 0
        samples = []
        for phase in ["render", "finalize"]:
            samples += json.loads(
                (folder / "workspace/jobs" / job["id"] / f"{phase}.resources.json").read_text()
            )["samples"]
        rows.append(
            {
                "job": job["id"],
                "output": output.relative_to(folder).as_posix(),
                "duration_s": seconds,
                "dimensions": [preset["width"], preset["height"]],
                "fps": preset["fps"],
                "decoded_frames": count,
                "timestamp_errors": errors,
                "decoded_audio_samples": audio_samples,
                "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
                "peak_child_private_gib": max(s["private_bytes"] for s in samples) / 1024**3,
                "min_global_available_gib": min(s["system_available_bytes"] for s in samples)
                / 1024**3,
                "scope": "Sampled child processes only; API/preview memory and perceptual quality not certified",
            }
        )
    assert rows, "No successful output to validate"
    result = {"all_passed": True, "run_id": folder.name, "outputs": rows}
    evidence = folder / "independent-validation.json"
    if evidence.exists():
        assert json.loads(evidence.read_text()) == result, "Preserve earlier validation evidence"
    else:
        evidence.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
