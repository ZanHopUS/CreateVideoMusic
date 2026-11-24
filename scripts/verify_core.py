"""S6 API/render checks on generated media, with unchanged production admission.

Never counts blocked admission as a pass. Raw outputs/evidence stay in .local.
Usage: python scripts/verify_core.py --matrix --long-run --ai-smoke
"""

import argparse
import json
import math
import os
import re
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import av
import psutil

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services/local-api"))
from amvs.app import create_app
from amvs.domain import content_hash
from fastapi.testclient import TestClient
from test_assets import prepare, prepare_vfr, prepare_video


def verify(path, project):
    preset = project["preset"]
    duration = project["durationTicks"] / 48000
    with av.open(str(path)) as media:
        video, audio = media.streams.video[0], media.streams.audio[0]
        valid = (
            video.codec_context.name == "h264"
            and audio.codec_context.name == "aac"
            and video.width == preset["width"]
            and video.height == preset["height"]
            and video.average_rate == preset["fps"]
            and abs(media.duration / av.time_base - duration) <= 1 / preset["fps"]
        )
        previous = None
        frames = 0
        errors = 0
        for frame in media.decode(video=0):
            now = float(frame.pts * frame.time_base)
            errors += int(previous is not None and now <= previous)
            previous = now
            frames += 1
    with av.open(str(path)) as media:
        samples = sum(frame.samples for frame in media.decode(audio=0))
    valid = bool(valid and not errors and frames == round(duration * preset["fps"]) and samples > 0)
    return {
        "passed": valid,
        "frames": frames,
        "timestampErrors": errors,
        "audioSamples": samples,
        "dimensions": [preset["width"], preset["height"]],
        "fps": preset["fps"],
        "duration": duration,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--matrix", action="store_true")
    parser.add_argument("--long-run", action="store_true")
    parser.add_argument("--ai-smoke", action="store_true")
    parser.add_argument("--vfr", action="store_true")
    parser.add_argument("--alignment-smoke", action="store_true")
    parser.add_argument("--development-ai", action="store_true")
    args = parser.parse_args()
    run = ROOT / ".local/evidence/s6" / str(time.time_ns())
    run.mkdir(parents=True)
    report = {
        "dateLocal": datetime.now(timezone(timedelta(hours=7))).isoformat(),
        "kind": "application API checks, generated fixtures; not browser/perceptual/corpus acceptance",
        "run": run.name,
        "admissionMinimumGiB": 4,
        "availableGiB": psutil.virtual_memory().available / 1024**3,
        "matrix": [],
        "ai": [],
        "alignment": [],
        "developmentAI": [],
        "vfr": None,
        "longRun": None,
        "releaseReady": False,
    }

    def save():
        (run / "results.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    if report["availableGiB"] < 4:
        report["status"] = "blocked-resources"
        report["reason"] = "RAM trống dưới admission 4 GiB; không spawn AI/render."
        save()
        print(
            json.dumps(
                {
                    "run": str(run.relative_to(ROOT)),
                    "status": report["status"],
                    "availableGiB": report["availableGiB"],
                }
            )
        )
        return 2
    if not any(
        (
            args.matrix,
            args.long_run,
            args.ai_smoke,
            args.vfr,
            args.alignment_smoke,
            args.development_ai,
        )
    ):
        report["status"] = "preflight-only"
        save()
        print(
            json.dumps(
                {
                    "run": str(run.relative_to(ROOT)),
                    "status": report["status"],
                    "availableGiB": report["availableGiB"],
                }
            )
        )
        return 0
    prepare()
    prepare_video()
    os.environ["AMVS_BROWSER"] = str(
        ROOT
        / "node_modules/.remotion/chrome-headless-shell/win64/chrome-headless-shell-win64/chrome-headless-shell.exe"
    )
    app = create_app(
        run / "workspace", "s6-test-session-" + "x" * 48, "http://127.0.0.1:3000", "testserver"
    )
    headers = {
        "host": "testserver",
        "origin": "http://127.0.0.1:3000",
        "authorization": "Bearer " + "s6-test-session-" + "x" * 48,
    }
    out = run / "exports"
    out.mkdir()
    app.state.grants["export"] = {"scope": "export", "path": out}
    with TestClient(app) as client:
        assets = []
        for filename in ("artwork.png", "artwork-2.png", "background.mp4", "control.wav"):
            with (ROOT / ".local/test-assets" / filename).open("rb") as f:
                r = client.post(
                    "/api/v1/assets",
                    headers=headers,
                    files={"file": (filename, f)},
                    data={"rightsConfirmed": "true"},
                )
            r.raise_for_status()
            assets.append(r.json())
        image, cover, video, audio = assets

        def project(template, preset, duration=2):
            p = json.loads((ROOT / "tests/fixtures/project.json").read_text(encoding="utf-8"))
            p["id"] = uuid.uuid4().hex
            p["name"] = "S6 generated fixture"
            p["templateRef"] = {"id": template, "version": 1}
            p["preset"] = preset
            p["durationTicks"] = duration * 48000
            p["items"] = []
            p["assetRefs"] = []

            def clip(asset, start, length):
                p["items"].append(
                    {
                        "id": uuid.uuid4().hex,
                        "trackId": "music" if asset["kind"] == "audio" else "background",
                        "type": asset["kind"],
                        "assetId": asset["id"],
                        "startTicks": round(start * 48000),
                        "durationTicks": round(length * 48000),
                        "sourceStartTicks": 0,
                        "speed": {"numerator": 1, "denominator": 1},
                        "volume": 1 if asset["kind"] == "audio" else 0,
                    }
                )
                if asset["id"] not in p["assetRefs"]:
                    p["assetRefs"].append(asset["id"])

            if template == "TPL-02":
                clip(image, 0, duration / 2)
                clip(cover, duration / 2, duration / 2)
            else:
                clip(video if template == "TPL-03" and duration <= 4 else image, 0, duration)
            for start in range(0, duration, 4):
                clip(audio, start, min(4, duration - start))
            if template in {"TPL-01", "TPL-02"}:
                definitions = (
                    [("caption", "Chú thích Việt Nam", 54)]
                    if template == "TPL-01"
                    else [
                        ("song-title", "Bài hát Việt Nam", 48),
                        ("artist-name", "Nghệ sĩ kiểm thử", 30),
                    ]
                )
                for role, text, size in definitions:
                    p["items"].append(
                        {
                            "id": role,
                            "type": "text",
                            "trackId": "text",
                            "text": text,
                            "startTicks": 0,
                            "durationTicks": duration * 48000,
                            "sourceStartTicks": 0,
                            "speed": {"numerator": 1, "denominator": 1},
                            "volume": 1,
                            "style": {
                                "fontFamily": "Arial",
                                "fontSize": size,
                                "color": "#ffffff",
                                "x": preset["width"] * 0.08,
                                "y": preset["height"] * 0.7,
                                "strokeWidth": 1,
                                "strokeColor": "#000000",
                                "shadow": True,
                                "animation": "fade",
                            },
                            **({"role": role} if template == "TPL-02" else {}),
                        }
                    )
            if template == "TPL-03":
                p["orderedTracks"].append({"id": "lyrics", "kind": "lyrics"})
                p["lyrics"] = [
                    {
                        "id": "line",
                        "text": "Giai điệu Việt Nam",
                        "sourceStartTicks": 0,
                        "sourceEndTicks": duration * 48000,
                        "source": "user",
                        "status": "reviewed",
                        "alignmentStatus": "sentence",
                        "words": [],
                    }
                ]
                p["lyrics"][0]["alignmentStatus"] = "word"
                p["lyrics"][0]["words"] = [
                    {
                        "text": word,
                        "startTicks": round(index * duration * 48000 / 4),
                        "endTicks": round((index + 1) * duration * 48000 / 4),
                    }
                    for index, word in enumerate(("Giai", "điệu", "Việt", "Nam"))
                ]
                p["items"].append(
                    {
                        "id": "lyric-item",
                        "type": "lyrics",
                        "trackId": "lyrics",
                        "lyricId": "line",
                        "startTicks": 0,
                        "durationTicks": duration * 48000,
                        "sourceStartTicks": 0,
                        "speed": {"numerator": 1, "denominator": 1},
                        "volume": 1,
                        "style": {
                            "fontSize": 40,
                            "x": 40,
                            "y": preset["height"] * 0.7,
                            "animation": "fade",
                        },
                    }
                )
            return p

        def supplied_cues(text):
            def seconds(value):
                h, m, s = value.replace(",", ".").split(":")
                return int(h) * 3600 + int(m) * 60 + float(s)

            cues = []
            for block in text.replace("\r", "").strip().split("\n\n"):
                rows = block.splitlines()
                if len(rows) < 3:
                    continue
                match = re.fullmatch(r"(\d+:\d+:\d+[,.]\d+)\s*-->\s*(\d+:\d+:\d+[,.]\d+)", rows[1])
                if not match:
                    continue
                content = " ".join(rows[2:]).strip()
                if not any(c.isalpha() for c in content) or content.startswith(("[", "(")):
                    continue
                cues.append(
                    {
                        "id": uuid.uuid4().hex,
                        "text": content,
                        "sourceStartTicks": round(seconds(match[1]) * 48000),
                        "sourceEndTicks": round(seconds(match[2]) * 48000),
                        "source": "import",
                        "status": "draft",
                        "alignmentStatus": "sentence",
                        "words": [],
                    }
                )
            return cues

        def wait(job):
            began = time.monotonic()
            while job["status"] not in {"succeeded", "failed", "cancelled", "interrupted"}:
                if (
                    time.monotonic() - began > 3000
                    or job["phase"] == "waiting-resources"
                    and time.monotonic() - began > 45
                ):
                    client.post("/api/v1/jobs/" + job["id"] + "/cancel", headers=headers, json={})
                    return {**job, "status": "blocked-resources-or-timeout"}
                time.sleep(1)
                job = client.get("/api/v1/jobs/" + job["id"], headers=headers).json()
            return job

        def render(p):
            client.post("/api/v1/projects", headers=headers, json=p).raise_for_status()
            response = client.post(
                "/api/v1/jobs",
                headers=headers,
                json={"projectId": p["id"], "revision": 1, "grantId": "export"},
            )
            if not response.is_success:
                return {
                    "template": p["templateRef"]["id"],
                    "preset": p["preset"],
                    "status": "rejected",
                    "httpStatus": response.status_code,
                }
            began = time.monotonic()
            job = wait(response.json())
            row = {
                "template": p["templateRef"]["id"],
                "preset": p["preset"],
                "jobId": job["id"],
                "status": job["status"],
                "elapsedSeconds": time.monotonic() - began,
                "snapshotHash": content_hash(p),
                "resourceSampledPass": job.get("resourceSampledPass", False),
                "resourceScope": job.get("resourceScope"),
            }
            job_folder = app.state.store.root / "jobs" / job["id"]
            sampled = []
            for phase in ("render", "finalize"):
                file = job_folder / (phase + ".resources.json")
                if file.is_file():
                    sampled.extend(json.loads(file.read_text())["samples"])
            if sampled:
                row["sampledChildren"] = {
                    "peakPrivateBytes": max(s["private_bytes"] for s in sampled),
                    "minimumAvailableBytes": min(s["system_available_bytes"] for s in sampled),
                    "peakCpuPercentOfOneCore": max(
                        s.get("cpuPercentOfOneCore", 0) for s in sampled
                    ),
                }
            row["postRunJobBytes"] = sum(
                file.stat().st_size for file in job_folder.rglob("*") if file.is_file()
            )
            row["elapsedRTF"] = row["elapsedSeconds"] / (p["durationTicks"] / 48000)
            if job["status"] == "succeeded":
                row["outputValidation"] = verify(
                    Path(app.state.jobs.rows[job["id"]]["outputFile"]), p
                )
            return row

        if args.matrix:
            for template in ("TPL-01", "TPL-02", "TPL-03"):
                for width, height in (
                    (720, 1280),
                    (1280, 720),
                    (720, 720),
                    (1080, 1920),
                    (1920, 1080),
                    (1080, 1080),
                ):
                    for fps in (30, 60):
                        row = render(
                            project(template, {"width": width, "height": height, "fps": fps})
                        )
                        report["matrix"].append(row)
                        save()
                        print(json.dumps(row), flush=True)
                        if (
                            row["status"] != "succeeded"
                            or not row.get("resourceSampledPass")
                            or not row.get("outputValidation", {}).get("passed")
                        ):
                            report["status"] = "incomplete"
                            save()
                            return 2
        if args.long_run:
            report["longRun"] = render(
                project("TPL-01", {"width": 1080, "height": 1920, "fps": 60}, 300)
            )
            save()
            print(json.dumps(report["longRun"]), flush=True)
        if args.development_ai:
            for language in ("vi", "en"):
                sample = language + "-001"
                source = ROOT / ".poc/data/user" / (sample + ".m4a")
                manifest_path = source.with_suffix(".manifest.json")
                reference = source.with_name(sample + ".reference.srt")
                if not (source.is_file() and manifest_path.is_file() and reference.is_file()):
                    report["developmentAI"].append(
                        {"sample": sample, "status": "missing-development-fixture"}
                    )
                    save()
                    continue
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                from amvs.store import digest_file

                if digest_file(source) != manifest["sha256"]:
                    raise ValueError("Development sample differs from supplied inventory")
                cues = supplied_cues(reference.read_text(encoding="utf-8-sig"))
                if not cues:
                    raise ValueError("No supplied cue windows")
                first = cues[0]["sourceStartTicks"]
                duration = min(
                    20 * 48000, math.floor((manifest["duration_s"] * 48000 - first) / 1600) * 1600
                )
                end = first + duration
                lines = [
                    c for c in cues if c["sourceStartTicks"] >= first and c["sourceEndTicks"] <= end
                ]
                with source.open("rb") as file:
                    response = client.post(
                        "/api/v1/assets",
                        headers=headers,
                        files={"file": (sample + ".m4a", file)},
                        data={"rightsConfirmed": "true"},
                    )
                response.raise_for_status()
                asset = response.json()
                for mode in ("small", "medium", "alignment"):
                    p = project("TPL-01", {"width": 720, "height": 1280, "fps": 30})
                    p["durationTicks"] = duration
                    p["items"] = [i for i in p["items"] if i["type"] != "audio"]
                    for item in p["items"]:
                        item["durationTicks"] = duration
                    music = {
                        "id": "development-music",
                        "trackId": "music",
                        "type": "audio",
                        "assetId": asset["id"],
                        "startTicks": 0,
                        "durationTicks": duration,
                        "sourceStartTicks": first,
                        "speed": {"numerator": 1, "denominator": 1},
                        "volume": 1,
                    }
                    p["items"].append(music)
                    p["assetRefs"] = [image["id"], asset["id"]]
                    client.post("/api/v1/projects", headers=headers, json=p).raise_for_status()
                    payload = {
                        "projectId": p["id"],
                        "revision": 1,
                        "audioItemId": music["id"],
                        "language": language,
                    }
                    if mode == "alignment":
                        payload["lines"] = lines
                        endpoint = "lyrics/alignment"
                    else:
                        payload["model"] = mode
                        endpoint = "lyrics/jobs"
                    response = client.post("/api/v1/" + endpoint, headers=headers, json=payload)
                    row = {
                        "sample": sample,
                        "mode": mode,
                        "split": "development, not held-out or independent timing gold",
                        "sourceRangeTicks": [first, end],
                        "sourceSha256": asset["id"],
                    }
                    if response.is_success:
                        job = wait(response.json())
                        row.update(status=job["status"], jobId=job["id"])
                        if job["status"] == "succeeded":
                            result = client.get(
                                "/api/v1/jobs/" + job["id"] + "/lyrics", headers=headers
                            ).json()
                            row.update(
                                lineCount=len(result["lines"]),
                                wordDraftLines=sum(
                                    l["alignmentStatus"] == "word" for l in result["lines"]
                                ),
                                allDraft=all(l["status"] == "draft" for l in result["lines"]),
                            )
                        unchanged = client.get(
                            "/api/v1/projects/" + p["id"], headers=headers
                        ).json()["contentHash"] == content_hash(p)
                        row["editorUnchanged"] = unchanged
                    else:
                        row.update(status="unavailable", httpStatus=response.status_code)
                    report["developmentAI"].append(row)
                    save()
                    print(json.dumps(row), flush=True)
        if args.vfr:
            source = prepare_vfr()
            with av.open(str(source)) as media:
                points = [frame.pts for frame in media.decode(video=0)]
                deltas = {b - a for a, b in zip(points, points[1:])}
            if len(deltas) < 2:
                raise ValueError("Generated input is not VFR")
            with source.open("rb") as file:
                response = client.post(
                    "/api/v1/assets",
                    headers=headers,
                    files={"file": (source.name, file)},
                    data={"rightsConfirmed": "true"},
                )
            response.raise_for_status()
            vfr = response.json()
            p = project("TPL-03", {"width": 720, "height": 1280, "fps": 30})
            visual = next(i for i in p["items"] if i["type"] == "video")
            visual.update(
                assetId=vfr["id"],
                sourceStartTicks=12000,
                durationTicks=36000,
                speed={"numerator": 2, "denominator": 1},
            )
            p["assetRefs"] = [key for key in p["assetRefs"] if key != video["id"]] + [vfr["id"]]
            row = render(p)
            row["sourceFrameDeltas"] = sorted(deltas)
            if row["status"] == "succeeded":
                output = Path(app.state.jobs.rows[row["jobId"]]["outputFile"])
                samples = {}
                with av.open(str(output)) as media:
                    for index, frame in enumerate(media.decode(video=0)):
                        if index in (7, 19):
                            packed = frame.reformat(format="rgb24")
                            offset = 80 * packed.planes[0].line_size + 80 * 3
                            rgb = list(memoryview(packed.planes[0])[offset : offset + 3])
                            samples[index] = rgb
                row["colorSamples"] = samples
                row["trimRateColorPassed"] = bool(
                    7 in samples
                    and 19 in samples
                    and samples[7][0] > 200
                    and samples[7][2] < 50
                    and samples[19][2] > 200
                    and samples[19][0] < 50
                )
            report["vfr"] = row
            save()
            print(json.dumps(row), flush=True)
        if args.alignment_smoke:
            for language in ("vi", "en"):
                p = project("TPL-01", {"width": 720, "height": 1280, "fps": 30})
                client.post("/api/v1/projects", headers=headers, json=p).raise_for_status()
                music = next(i for i in p["items"] if i["type"] == "audio")
                lines = [
                    {
                        "id": "cue",
                        "text": "Lời kiểm thử" if language == "vi" else "Test supplied words",
                        "sourceStartTicks": 0,
                        "sourceEndTicks": 48000,
                        "source": "user",
                        "status": "draft",
                        "alignmentStatus": "sentence",
                        "words": [],
                    }
                ]
                response = client.post(
                    "/api/v1/lyrics/alignment",
                    headers=headers,
                    json={
                        "projectId": p["id"],
                        "revision": 1,
                        "audioItemId": music["id"],
                        "language": language,
                        "lines": lines,
                    },
                )
                row = {
                    "language": language,
                    "fixture": "supplied words on generated tone; pipeline-only, not timing truth",
                }
                if response.is_success:
                    job = wait(response.json())
                    row.update(status=job["status"], jobId=job["id"])
                    if job["status"] == "succeeded":
                        result = client.get(
                            "/api/v1/jobs/" + job["id"] + "/lyrics", headers=headers
                        ).json()
                        row.update(
                            lineCount=len(result["lines"]),
                            fallbackCount=result.get("fallbackCount"),
                        )
                else:
                    row.update(status="unavailable", httpStatus=response.status_code)
                report["alignment"].append(row)
                save()
                print(json.dumps(row), flush=True)
        if args.ai_smoke:
            for language in ("vi", "en"):
                p = project("TPL-01", {"width": 720, "height": 1280, "fps": 30})
                client.post("/api/v1/projects", headers=headers, json=p).raise_for_status()
                music = next(i for i in p["items"] if i["type"] == "audio")
                response = client.post(
                    "/api/v1/lyrics/jobs",
                    headers=headers,
                    json={
                        "projectId": p["id"],
                        "revision": 1,
                        "audioItemId": music["id"],
                        "language": language,
                        "model": "small",
                    },
                )
                if not response.is_success:
                    report["ai"].append(
                        {
                            "language": language,
                            "status": "unavailable",
                            "httpStatus": response.status_code,
                        }
                    )
                    save()
                    continue
                job = wait(response.json())
                row = {
                    "language": language,
                    "status": job["status"],
                    "jobId": job["id"],
                    "fixture": "generated 440Hz tone, no lyrics",
                }
                if job["status"] == "succeeded":
                    result = client.get(
                        "/api/v1/jobs/" + job["id"] + "/lyrics", headers=headers
                    ).json()
                    row["lineCount"] = len(result["lines"])
                    row["instrumentalPassed"] = not result["lines"]
                report["ai"].append(row)
                save()
                print(json.dumps(row), flush=True)
    successful = all(
        r.get("outputValidation", {}).get("passed", False) and r.get("resourceSampledPass", False)
        for r in report["matrix"]
    )
    if args.long_run:
        successful = successful and bool(
            report["longRun"] and report["longRun"].get("outputValidation", {}).get("passed")
        )
    if args.ai_smoke:
        successful = (
            successful
            and len(report["ai"]) == 2
            and all(r.get("instrumentalPassed", False) for r in report["ai"])
        )
    if args.vfr:
        successful = successful and bool(
            report["vfr"]
            and report["vfr"].get("trimRateColorPassed")
            and report["vfr"].get("outputValidation", {}).get("passed")
        )
    if args.alignment_smoke:
        successful = (
            successful
            and len(report["alignment"]) == 2
            and all(r["status"] == "succeeded" for r in report["alignment"])
        )
    if args.development_ai:
        successful = (
            successful
            and len(report["developmentAI"]) == 6
            and all(
                r["status"] == "succeeded" and r.get("editorUnchanged") and r.get("allDraft")
                for r in report["developmentAI"]
            )
        )
    report["checksPassed"] = successful
    report["status"] = "checks-completed" if successful else "checks-failed-or-incomplete"
    report["releaseBlockers"] = [
        "independent lyrics corpus/timing gold/correction time",
        "audio listening",
        "ACC-01 PO thresholds",
        "VFR regression",
        "UI performance and contention repetitions",
        "Drive cross-PC/offline/quota verification",
    ]
    save()
    print(str(run.relative_to(ROOT)))
    return 0 if successful else 2


if __name__ == "__main__":
    raise SystemExit(main())
