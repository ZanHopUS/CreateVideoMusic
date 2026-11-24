"""Independent recovery and portable snapshots; never archives live SQLite."""

import json
import os
import re
import shutil
import tempfile
import threading
import time
import uuid
import zipfile
from pathlib import Path

from .domain import canonical, content_hash, parse_json, validate
from .media import probe
from .storage_policy import StoragePolicy
from .store import Conflict, contained, digest_file, validate_view

MAX_JSON = 16 * 1024**2
MAX_EXPANDED = 8 * 1024**3


def atomic_json(target, value):
    stage = target.with_name(uuid.uuid4().hex + ".stage")
    try:
        with stage.open("xb") as output:
            output.write(json.dumps(value, ensure_ascii=False, allow_nan=False).encode())
            output.flush()
            os.fsync(output.fileno())
        os.replace(stage, target)
    finally:
        stage.unlink(missing_ok=True)


class Snapshots:
    def __init__(self, store):
        self.store = store
        self.lock = threading.RLock()
        self.stop = threading.Event()
        self.thread = None
        self.warning = ""

    def start(self):
        def loop():
            while not self.stop.wait(30):
                try:
                    for row in self.store.list_projects():
                        self.capture(row["id"])
                except Exception:
                    self.warning = (
                        "Không thể tạo recovery; hãy lưu thủ công và kiểm tra dung lượng."
                    )

        self.thread = threading.Thread(target=loop, daemon=True)
        self.thread.start()

    def close(self):
        self.stop.set()
        if self.thread:
            self.thread.join(timeout=5)

    def directory(self, id):
        self.store.load(id)
        folder = contained(self.store.root / "recovery" / id, self.store.root)
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    def list(self, id):
        with self.lock:
            rows = []
            for path in self.directory(id).glob("*.json"):
                try:
                    if path.stat().st_size > MAX_JSON:
                        raise ValueError("Recovery quá lớn.")
                    data = parse_json(contained(path, self.store.root).read_bytes())
                    rows.append(
                        {
                            "id": path.stem,
                            "createdAt": data["createdAt"],
                            "contentHash": data["contentHash"],
                            "bytes": path.stat().st_size,
                        }
                    )
                except (ValueError, KeyError, OSError):
                    self.warning = "Có recovery hỏng; bản lưu thủ công được giữ nguyên."
            return sorted(rows, key=lambda r: r["createdAt"], reverse=True)

    def capture(self, id):
        with self.lock:
            current = self.store.load(id)
            rows = self.list(id)
            if not current["dirty"] or rows and rows[0]["contentHash"] == current["contentHash"]:
                return {"created": False, "warning": self.warning}
            data = {
                "format": "amvs-recovery/1",
                "createdAt": time.time(),
                "project": current["project"],
                "view": current["view"],
                "contentHash": current["contentHash"],
            }
            size = len(json.dumps(data).encode())
            if len(rows) >= 10 or sum(r["bytes"] for r in rows) + size > 200 * 1024**2:
                self.warning = (
                    "Recovery đã đạt 10 bản hoặc 200 MiB. Hãy xem và dọn các bản không cần."
                )
                return {"created": False, "warning": self.warning}
            atomic_json(self.directory(id) / (uuid.uuid4().hex + ".json"), data)
            return {"created": True, "warning": self.warning}

    def restore(self, id, recovery_id, revision):
        with self.lock:
            if not re.fullmatch("[a-f0-9]{32}", recovery_id):
                raise ValueError("Recovery ID không hợp lệ.")
            path = contained(self.directory(id) / (recovery_id + ".json"), self.store.root)
            if path.stat().st_size > MAX_JSON:
                raise ValueError("Recovery quá lớn.")
            data = parse_json(path.read_bytes())
            if (
                data.get("format") != "amvs-recovery/1"
                or data["project"]["id"] != id
                or content_hash(data["project"]) != data["contentHash"]
            ):
                raise ValueError("Recovery bị hỏng.")
            return self.store.update(id, data["project"], revision, data.get("view", {}))

    def clear(self, id, ids):
        with self.lock:
            if not isinstance(ids, list) or not all(
                isinstance(i, str) and re.fullmatch("[a-f0-9]{32}", i) for i in ids
            ):
                raise ValueError("Danh sách recovery không hợp lệ.")
            for key in ids:
                contained(self.directory(id) / (key + ".json"), self.store.root).unlink(
                    missing_ok=True
                )
            self.warning = ""
            return {"deleted": len(ids)}

    def export(self, id, revision, folder, snapshot=None, check=lambda: None):
        with self.lock:
            current = snapshot or self.store.load(id)
            if current["revision"] != revision:
                raise Conflict("Revision cũ.")
            project = current["project"]
            catalog = self.store.assets()
            validate(project, catalog)
            inventory = {}
            total = 0
            for key in project["assetRefs"]:
                check()
                asset = catalog[key]
                source = self.store.asset_path(asset)
                if digest_file(source) != key:
                    raise ValueError("Media bị hỏng.")
                total += source.stat().st_size
                inventory[key] = dict(asset)
            if total > MAX_EXPANDED or len(inventory) > 4093:
                raise ValueError("Package vượt 8 GiB hoặc 4093 media.")
            if shutil.disk_usage(folder).free < total + max(
                StoragePolicy(self.store).read()["reserveGiB"] * 1024**3, total // 10
            ):
                raise OSError("Không đủ dung lượng package.")
            target = contained(Path(folder) / (id + "-" + uuid.uuid4().hex + ".amvs"), folder)
            stage = target.with_suffix(".stage")
            envelope = {
                "format": "amvs-portable/1",
                "project": project,
                "view": current["view"],
                "contentHash": current["contentHash"],
                "manualSavedHash": current["manualSavedHash"],
                "assets": inventory,
            }
            payload = json.dumps(envelope, ensure_ascii=False, allow_nan=False).encode()
            if len(payload) > MAX_JSON:
                raise ValueError("Project JSON vượt 16 MiB.")
            try:
                with zipfile.ZipFile(
                    stage, "x", compression=zipfile.ZIP_STORED, allowZip64=True
                ) as archive:
                    manifest = {k: v for k, v in envelope.items() if k != "project"}
                    manifest_bytes = json.dumps(
                        manifest, ensure_ascii=False, allow_nan=False
                    ).encode()
                    if len(manifest_bytes) > 4 * 1024**2:
                        raise ValueError("Manifest vượt 4 MiB.")
                    archive.writestr("manifest.json", manifest_bytes)
                    archive.writestr("project.json", canonical(project))
                    for key, asset in inventory.items():
                        with (
                            self.store.asset_path(asset).open("rb") as source,
                            archive.open(
                                "assets/" + asset["file"], "w", force_zip64=True
                            ) as output,
                        ):
                            while chunk := source.read(1024 * 1024):
                                check()
                                output.write(chunk)
                with zipfile.ZipFile(stage) as archive:
                    if archive.testzip():
                        raise ValueError("Package không đạt CRC.")
                with stage.open("rb+") as handle:
                    os.fsync(handle.fileno())
                check()
                os.replace(stage, target)
                return {
                    "name": target.name,
                    "bytes": target.stat().st_size,
                    "sha256": digest_file(target),
                }
            finally:
                stage.unlink(missing_ok=True)

    def import_package(self, path):
        with (
            self.lock,
            tempfile.TemporaryDirectory(prefix="package-", dir=self.store.root / "runtime") as temp,
        ):
            stage = Path(temp)
            with zipfile.ZipFile(path) as archive:
                infos = archive.infolist()
                names = [i.filename for i in infos]
                if (
                    len(infos) > 4096
                    or len(set(names)) != len(names)
                    or not {"project.json", "manifest.json"}.issubset(names)
                ):
                    raise ValueError("Package trùng file hoặc quá nhiều entries.")
                total = 0
                for info in infos:
                    name = info.filename
                    if name not in {"project.json", "manifest.json"} and not re.fullmatch(
                        r"assets/[a-f0-9]{64}\.(png|jpg|mp4|wav|mp3|m4a)", name
                    ):
                        raise ValueError("Đường dẫn package không hợp lệ.")
                    if (
                        info.flag_bits & 1
                        or info.is_dir()
                        or (info.external_attr >> 16) & 0o170000 == 0o120000
                    ):
                        raise ValueError("Package có link hoặc mã hóa.")
                    total += info.file_size
                    if total > MAX_EXPANDED or info.file_size / max(1, info.compress_size) > 200:
                        raise ValueError("Package vượt giới hạn giải nén.")
                if archive.getinfo("project.json").file_size > MAX_JSON:
                    raise ValueError("Project JSON quá lớn.")
                if (
                    shutil.disk_usage(stage).free
                    < total + StoragePolicy(self.store).read()["reserveGiB"] * 1024**3
                ):
                    raise OSError("Không đủ dung lượng restore.")
                if archive.getinfo("manifest.json").file_size > 4 * 1024**2:
                    raise ValueError("Manifest quá lớn.")
                envelope = parse_json(archive.read("manifest.json"))
                envelope["project"] = parse_json(archive.read("project.json"))
                project = envelope["project"]
                validate_view(envelope.get("view", {}))
                inventory = envelope["assets"]
                if (
                    envelope.get("format") != "amvs-portable/1"
                    or content_hash(project) != envelope.get("contentHash")
                    or set(inventory) != set(project["assetRefs"])
                ):
                    raise ValueError("Manifest không khớp.")
                saved_hash = envelope.get("manualSavedHash")
                if saved_hash is not None and (
                    not isinstance(saved_hash, str) or not re.fullmatch(r"[a-f0-9]{64}", saved_hash)
                ):
                    raise ValueError("Manual save hash không hợp lệ.")
                validate(project, inventory)
                if set(names) != {
                    "project.json",
                    "manifest.json",
                    *("assets/" + a["file"] for a in inventory.values()),
                }:
                    raise ValueError("Inventory package không khớp.")
                try:
                    self.store.load(project["id"])
                except KeyError:
                    pass
                else:
                    raise Conflict("Project đã tồn tại; không ghi đè.")
                for key, asset in inventory.items():
                    if not re.fullmatch(r"[a-f0-9]{64}", key) or not re.fullmatch(
                        key + r"\.(png|jpg|mp4|wav|mp3|m4a)", asset["file"]
                    ):
                        raise ValueError("Tên media không khớp hash.")
                    info = archive.getinfo("assets/" + asset["file"])
                    if info.file_size != asset["bytes"]:
                        raise ValueError("Size media sai.")
                    output = stage / asset["file"]
                    count = 0
                    with archive.open(info) as source, output.open("xb") as target:
                        while chunk := source.read(1024 * 1024):
                            count += len(chunk)
                            if count > info.file_size:
                                raise ValueError("Dữ liệu giải nén vượt size.")
                            target.write(chunk)
                    if digest_file(output) != key:
                        raise ValueError("Checksum media sai.")
                    actual = probe(output)
                    if any(
                        actual.get(k) != asset.get(k)
                        for k in ("kind", "mime", "codec", "durationTicks", "width", "height")
                    ):
                        raise ValueError("Metadata media sai.")
                self.store.pin_assets(inventory.keys())
                # Verified immutable media can be shared; never overwrite existing bytes.
                for key, asset in inventory.items():
                    target = contained(
                        self.store.root / "library" / asset["file"], self.store.root / "library"
                    )
                    if target.exists():
                        if digest_file(target) != key:
                            raise ValueError("Media local bị hỏng; hãy relink trước.")
                    else:
                        os.link(stage / asset["file"], target)
                with self.store.connect() as db:
                    for key, asset in inventory.items():
                        db.execute(
                            "INSERT OR IGNORE INTO assets VALUES(?,?)", (key, json.dumps(asset))
                        )
                    db.execute(
                        "INSERT INTO projects VALUES(?,?,?,?,?)",
                        (
                            project["id"],
                            canonical(project).decode(),
                            json.dumps(envelope.get("view", {})),
                            1,
                            saved_hash,
                        ),
                    )
                return self.store.load(project["id"])
