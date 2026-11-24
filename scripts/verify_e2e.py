"""Independently decode outputs of the latest passing disposable browser run."""

import hashlib
import json
import sqlite3
from pathlib import Path

import av

ROOT = Path(__file__).resolve().parents[1]


def visual_checks(folder, job, assets):
    """Sparse RGB comparisons for generated 9:16 fixtures, outside the caption area."""
    project = job["project"]
    if project["templateRef"]["id"] != "TPL-01":
        return [
            {
                "status": "not-run",
                "reason": "Overlay template requires preview/output comparison; raw background pixels are intentionally changed.",
            }
        ]
    fps = project["preset"]["fps"]
    visuals = [i for i in project["items"] if i["type"] in {"image", "video"}]
    targets = {round((i["startTicks"] + i["durationTicks"] / 2) * fps / 48000): i for i in visuals}
    decoded = {}
    with av.open(job["outputFile"]) as media:
        for index, frame in enumerate(media.decode(video=0)):
            if index in targets:
                decoded[index] = frame

    def pixel(frame, x, y):
        rgb = frame.reformat(format="rgb24")
        offset = y * rgb.planes[0].line_size + x * 3
        return tuple(memoryview(rgb.planes[0])[offset : offset + 3])

    rows = []
    for index, item in targets.items():
        source = (folder / "workspace/library" / assets[item["assetId"]]["file"]).resolve()
        assert source.is_relative_to((folder / "workspace/library").resolve())
        tick = index * 48000 / fps
        source_time = (
            item["sourceStartTicks"]
            + (tick - item["startTicks"])
            * item["speed"]["numerator"]
            / item["speed"]["denominator"]
        ) / 48000
        reference = None
        with av.open(str(source)) as media:
            for frame in media.decode(video=0):
                reference = frame
                if (
                    item["type"] == "image"
                    or float(frame.pts * frame.time_base) >= source_time - 0.000001
                ):
                    break
        assert reference is not None
        final = decoded[index]
        assert abs(reference.width / reference.height - final.width / final.height) < 0.000001, (
            "This fixture comparison requires matching aspect ratios"
        )
        errors = []
        for x, y in [(0.3, 0.2), (0.5, 0.2), (0.7, 0.2), (0.3, 0.4), (0.5, 0.4), (0.7, 0.4)]:
            sx, sy = int(x * reference.width), int(y * reference.height)
            before = pixel(reference, sx, sy)
            # Match texel centers when upscaling, rather than sampling a bar
            # boundary at the same normalized edge coordinate.
            fx = round((sx + 0.5) * final.width / reference.width - 0.5)
            fy = round((sy + 0.5) * final.height / reference.height - 0.5)
            after = pixel(final, fx, fy)
            errors.extend(abs(a - b) for a, b in zip(before, after))
        mean_error = sum(errors) / len(errors)
        assert mean_error <= 20, ("Visual source/order mismatch", index, item["type"], mean_error)
        rows.append(
            {
                "output_frame": index,
                "type": item["type"],
                "source_time_s": source_time,
                "mean_abs_rgb_error": mean_error,
                "threshold": 20,
            }
        )
    return rows


def main():
    passed = []
    for folder in (ROOT / ".local/e2e").iterdir():
        file = folder / "results.json"
        if file.is_file():
            stats = json.loads(file.read_text(encoding="utf-8")).get("stats", {})
            if stats.get("expected", 0) > 0 and stats.get("unexpected", 0) == 0:
                db = folder / "workspace/runtime/studio.sqlite"
                if db.exists():
                    with sqlite3.connect(db) as connection:
                        if any(
                            json.loads(r[0])["status"] == "succeeded"
                            and json.loads(r[0]).get("kind") == "render"
                            for r in connection.execute("SELECT body FROM jobs")
                        ):
                            passed.append(folder)
    if not passed:
        raise RuntimeError("No passing browser run to validate")
    folder = sorted(passed)[-1]
    database = sqlite3.connect(folder / "workspace/runtime/studio.sqlite")
    try:
        jobs = [json.loads(row[0]) for row in database.execute("SELECT body FROM jobs")]
        assets = {
            row[0]: json.loads(row[1]) for row in database.execute("SELECT id,metadata FROM assets")
        }
    finally:
        database.close()
    rows = []
    for job in jobs:
        if job["status"] != "succeeded" or job.get("kind") != "render":
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
                    png = folder / f"output-{job['id']}-frame-{preset['fps']}.png"
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
                "visual_checks": visual_checks(folder, job, assets),
                "peak_child_private_gib": max(s["private_bytes"] for s in samples) / 1024**3,
                "min_global_available_gib": min(s["system_available_bytes"] for s in samples)
                / 1024**3,
                "scope": "Sampled child processes only; API/preview memory and perceptual quality not certified",
            }
        )
    assert rows, "No successful output to validate"
    result = {"all_passed": True, "run_id": folder.name, "outputs": rows}
    evidence = folder / "independent-validation-s2.json"
    if evidence.exists():
        assert json.loads(evidence.read_text()) == result, "Preserve earlier validation evidence"
    else:
        evidence.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
