"""Managed catalog, immutable reusable templates and transparent local suggestions."""

import copy
import json
import math
import uuid
from array import array

import av

from .domain import TICKS, parse_json, validate, validate_template
from .storage_policy import StoragePolicy
from .store import contained, pin_guard


class Catalog:
    def __init__(self, store):
        self.pin_lock = store.pin_lock
        self.store = store
        self.storage = StoragePolicy(store)
        with store.connect() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS templates(id TEXT PRIMARY KEY, body TEXT NOT NULL)"
            )

    def templates(self):
        with self.store.connect() as db:
            return [
                parse_json(r["body"])
                for r in db.execute("SELECT body FROM templates ORDER BY rowid DESC")
            ]

    @pin_guard
    def save_template(self, project, name, item_ids):
        validate(project, self.store.assets())
        if (
            not isinstance(item_ids, list)
            or len(set(item_ids)) != len(item_ids)
            or any(not isinstance(i, str) for i in item_ids)
        ):
            raise ValueError("Chọn placeholders hợp lệ.")
        items = {i["id"]: i for i in project["items"]}
        if not item_ids or any(i not in items or items[i]["type"] == "lyrics" for i in item_ids):
            raise ValueError("Chọn placeholder ảnh/video/nhạc/chữ; lời gắn nguồn được giữ nguyên.")
        template = {
            "schemaVersion": "amvs-template/1",
            "id": uuid.uuid4().hex,
            "version": 1,
            "name": name,
            "defaultProject": copy.deepcopy(project),
            "slots": [
                {"id": uuid.uuid4().hex, "itemId": i, "kind": items[i]["type"], "required": True}
                for i in item_ids
            ],
        }
        validate_template(template)
        self.store.pin_assets(project["assetRefs"])
        with self.store.connect() as db:
            db.execute("INSERT INTO templates VALUES(?,?)", (template["id"], json.dumps(template)))
        return template

    @pin_guard
    def instantiate(self, id, bindings):
        template = next((t for t in self.templates() if t["id"] == id), None)
        if template is None:
            raise KeyError(id)
        if not isinstance(bindings, dict) or set(bindings) != {s["id"] for s in template["slots"]}:
            raise ValueError("Cần đủ bindings cho từng slot.")
        p = copy.deepcopy(template["defaultProject"])
        p["id"] = uuid.uuid4().hex
        p["name"] = template["name"] + " · bản mới"
        items = {i["id"]: i for i in p["items"]}
        for slot in template["slots"]:
            value = bindings[slot["id"]]
            if not isinstance(value, str):
                raise ValueError("Binding phải là text hoặc asset ID.")
            if slot["kind"] == "text":
                items[slot["itemId"]]["text"] = value
            else:
                items[slot["itemId"]]["assetId"] = value
        remap = {i["id"]: uuid.uuid4().hex for i in p["items"]}
        for item in p["items"]:
            if item["id"] in {"song-title", "artist-name"}:
                item["role"] = item["id"]
        lyric_ids = {line["id"]: uuid.uuid4().hex for line in p["lyrics"]}
        track_ids = {t["id"]: uuid.uuid4().hex for t in p["orderedTracks"]}
        for track in p["orderedTracks"]:
            track["id"] = track_ids[track["id"]]
        for item in p["items"]:
            item["id"] = remap[item["id"]]
            item["trackId"] = track_ids[item["trackId"]]
            if item.get("lyricId"):
                item["lyricId"] = lyric_ids[item["lyricId"]]
        for line in p["lyrics"]:
            line["id"] = lyric_ids[line["id"]]
            if line.get("sourceAudioItemId"):
                line["sourceAudioItemId"] = remap[line["sourceAudioItemId"]]
        p["assetRefs"] = list(dict.fromkeys(i["assetId"] for i in p["items"] if i.get("assetId")))
        validate(p, self.store.assets())
        return self.store.create(p)

    @pin_guard
    def tags(self, id, tags):
        if (
            not isinstance(tags, list)
            or len(tags) > 20
            or any(not isinstance(t, str) or len(t) > 50 for t in tags)
        ):
            raise ValueError("Tối đa 20 tags, mỗi tag 50 ký tự.")
        asset = self.store.assets()[id]
        asset["tags"] = list(dict.fromkeys(t.strip() for t in tags if t.strip()))
        with self.store.connect() as db:
            db.execute("UPDATE assets SET metadata=? WHERE id=?", (json.dumps(asset), id))
        return asset

    @pin_guard
    def thumbnail(self, id):
        asset = self.store.assets()[id]
        if asset["kind"] == "audio":
            raise ValueError("Nhạc không có thumbnail ảnh.")
        folder = contained(self.store.root / "cache" / "thumbnails", self.store.root)
        folder.mkdir(parents=True, exist_ok=True)
        target = contained(folder / (id + ".jpg"), self.store.root)
        if target.is_file():
            return target
        with self.storage.lock:
            with av.open(str(self.store.asset_path(asset))) as source:
                frame = next(source.decode(video=0))
                width = 256
                height = max(2, round(frame.height / frame.width * width / 2) * 2)
                height = min(height, 1024)
                frame = frame.reformat(width=width, height=height, format="yuvj420p")
                codec = av.CodecContext.create("mjpeg", "w")
                codec.width = width
                codec.height = height
                codec.pix_fmt = "yuvj420p"
                data = b"".join(
                    bytes(packet) for packet in [*codec.encode(frame), *codec.encode(None)]
                )
                self.storage.check_cache(len(data))
                target.write_bytes(data)
            return target

    def suggestions(self, id):
        asset = self.store.assets()[id]
        if asset["kind"] != "audio":
            raise ValueError("Chọn file nhạc.")
        # Streaming decode bounded to first 300 source seconds. No vocals/mood claim.
        seconds = min(300, asset["durationTicks"] / TICKS)
        if seconds < 12:
            return {
                "segments": [],
                "message": "Nguồn quá ngắn để đề xuất hai đoạn khác nhau. Hãy nghe và cắt thủ công.",
                "method": "local-energy-v1",
            }
        buckets = {}
        with av.open(str(self.store.asset_path(asset))) as source:
            resampler = av.AudioResampler(format="fltp", layout="mono", rate=8000)
            for frame in source.decode(audio=0):
                if frame.time is not None and frame.time >= seconds:
                    break
                for mono in resampler.resample(frame):
                    if mono.time is None:
                        continue
                    position = max(0, int(mono.time))
                    samples = array("f")
                    samples.frombytes(bytes(mono.planes[0])[: mono.samples * 4])
                    power = sum(sample * sample for sample in samples) / max(1, len(samples))
                    if math.isfinite(power):
                        total, count = buckets.get(position, (0, 0))
                        buckets[position] = (total + power, count + 1)
        window = min(20, seconds / 3)
        candidates = []
        for start in range(0, max(1, math.floor(seconds - window)) + 1):
            values = [
                buckets[s][0] / buckets[s][1]
                for s in range(start, math.ceil(start + window))
                if s in buckets
            ]
            if values:
                candidates.append((sum(values) / len(values), start))
        chosen = []
        for score, start in sorted(candidates, reverse=True):
            if score <= 1e-8:
                continue
            if all(abs(start - old["startTicks"] / TICKS) >= window for old in chosen):
                chosen.append(
                    {
                        "startTicks": round(start * TICKS),
                        "durationTicks": round(window * TICKS),
                        "energy": score,
                    }
                )
            if len(chosen) >= 3:
                break
        return {
            "segments": chosen,
            "method": "local-energy-v1",
            "message": "Đề xuất theo năng lượng trong 300 giây đầu, không nhận biết đoạn hay hoặc mood. Nghe thử rồi chọn; không tự đổi clip."
            if len(chosen) >= 2
            else "Chưa tìm đủ hai vùng khác nhau; hãy cắt thủ công.",
        }
