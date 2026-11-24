"""Shared schema plus cross-field invariants. No renderer/frame based persistence."""

import hashlib
import json
from pathlib import Path

import rfc8785
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[3]
SCHEMA = json.loads((ROOT / "packages/domain/project.schema.json").read_text(encoding="utf-8"))
VALIDATOR = Draft202012Validator(SCHEMA)
TEMPLATE_VALIDATOR = Draft202012Validator(
    json.loads((ROOT / "packages/domain/template.schema.json").read_text())
)
JOB_VALIDATOR = Draft202012Validator(
    json.loads((ROOT / "packages/domain/job.schema.json").read_text())
)
TICKS = 48000


def parse_json(data):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate JSON key")
            result[key] = value
        return result

    return json.loads(
        data,
        object_pairs_hook=unique,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Non-finite JSON")),
    )


def validate(project, assets=None):
    errors = list(VALIDATOR.iter_errors(project))
    if errors:
        raise ValueError("Dữ liệu project không hợp lệ.")
    tracks = {t["id"]: t["kind"] for t in project["orderedTracks"]}
    if len(tracks) != len(project["orderedTracks"]) or len(
        {i["id"] for i in project["items"]}
    ) != len(project["items"]):
        raise ValueError("ID trùng.")
    preset = project["preset"]
    if (preset["width"], preset["height"]) not in {
        (720, 1280),
        (1280, 720),
        (720, 720),
        (1080, 1920),
        (1920, 1080),
        (1080, 1080),
    }:
        raise ValueError("Preset không hợp lệ.")
    kinds = {
        "image": "background",
        "video": "background",
        "audio": "music",
        "text": "text",
        "lyrics": "lyrics",
    }
    lyrics = {l["id"]: l for l in project["lyrics"]}
    if len(lyrics) != len(project["lyrics"]):
        raise ValueError("Lyric ID trùng.")
    for item in project["items"]:
        if (
            tracks.get(item["trackId"]) != kinds[item["type"]]
            or item["startTicks"] + item["durationTicks"] > project["durationTicks"]
        ):
            raise ValueError("Track hoặc thời lượng không hợp lệ.")
        if item.get("assetId") and item["assetId"] not in project["assetRefs"]:
            raise ValueError("Asset không tồn tại.")
        if item.get("lyricId") and item["lyricId"] not in lyrics:
            raise ValueError("Lyrics không tồn tại.")
        if assets is not None and item["type"] in {"image", "video", "audio"}:
            asset = assets.get(item["assetId"])
            if not asset or asset["kind"] != item["type"]:
                raise ValueError("Loại media không khớp.")
            if asset["durationTicks"]:
                end = (
                    item["sourceStartTicks"]
                    + item["durationTicks"]
                    * item["speed"]["numerator"]
                    / item["speed"]["denominator"]
                )
                if end > asset["durationTicks"]:
                    raise ValueError("Đoạn nguồn vượt thời lượng media.")
    for line in lyrics.values():
        audio_id = line.get("sourceAudioItemId")
        if audio_id:
            audio = next(
                (i for i in project["items"] if i["id"] == audio_id and i["type"] == "audio"), None
            )
            if (
                not audio
                or assets is not None
                and line["sourceEndTicks"] > assets[audio["assetId"]]["durationTicks"]
            ):
                raise ValueError("Nguồn lời bị thiếu hoặc timestamp vượt nguồn nhạc.")
        if not line["text"].strip() or line["sourceEndTicks"] <= line["sourceStartTicks"]:
            raise ValueError("Thời gian lyrics không hợp lệ.")
        previous = line["sourceStartTicks"]
        for word in line["words"]:
            if (
                word["startTicks"] < previous
                or word["endTicks"] <= word["startTicks"]
                or word["endTicks"] > line["sourceEndTicks"]
            ):
                raise ValueError("Thời gian từ không hợp lệ.")
            previous = word["endTicks"]
    return project


def canonical(project):
    validate(project)
    return rfc8785.dumps(project)


def content_hash(project):
    return hashlib.sha256(canonical(project)).hexdigest()


def validate_template(template):
    if list(TEMPLATE_VALIDATOR.iter_errors(template)):
        raise ValueError("Template không hợp lệ.")
    validate(template["defaultProject"])
    if len({s["id"] for s in template["slots"]}) != len(template["slots"]):
        raise ValueError("Slot ID trùng.")
    for slot in template["slots"]:
        if not any(
            i["id"] == slot["itemId"] and i["type"] == slot["kind"]
            for i in template["defaultProject"]["items"]
        ):
            raise ValueError("Placeholder không hợp lệ.")
    return template


def validate_job(job):
    if list(JOB_VALIDATOR.iter_errors(job)):
        raise ValueError("Job không hợp lệ.")
    return job
