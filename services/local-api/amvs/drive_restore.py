"""Restore an immutable Drive checkpoint into a local library and SQLite transaction."""

import json
import re
import tempfile
import threading
from pathlib import Path

from .domain import canonical, content_hash, parse_json, validate, validate_template
from .drive import API, DriveError
from .store import contained, digest_file, validate_view


class DriveRestore:
    def __init__(self, drive, store):
        self.drive, self.store = drive, store
        self.lock = threading.Lock()
        self.thread = None
        self.state = {"status": "idle", "message": "Chưa khôi phục từ Drive."}

    def status(self):
        with self.lock:
            return dict(self.state)

    def patch(self, **values):
        with self.lock:
            self.state.update(values)

    def backup_folder(self):
        if not self.drive.status()["connected"]:
            raise DriveError("Hãy kết nối Drive trước khi khôi phục.")
        return self.drive.child_folder(self.drive.data["folder"], "Backups")

    def list(self):
        parent = self.backup_folder()
        files = (
            self.drive.request(
                "GET",
                API,
                headers=self.drive.auth(),
                params={
                    "q": f"'{parent}' in parents and trashed=false and appProperties has {{ key='amvs' and value='1' }}",
                    "fields": "nextPageToken,files(id,name,size,md5Checksum,createdTime)",
                    "orderBy": "createdTime desc",
                    "pageSize": 100,
                },
            )
            .json()
            .get("files", [])
        )
        return [
            {
                "id": f["id"],
                "name": f["name"],
                "bytes": int(f["size"]),
                "md5": f["md5Checksum"],
                "createdTime": f.get("createdTime"),
            }
            for f in files
            if re.fullmatch(r"[a-f0-9]{32}\.json", f.get("name", ""))
        ]

    def start(self, manifest_id):
        with self.lock:
            if self.state["status"] == "running":
                raise DriveError("Đang khôi phục. Hãy chờ lượt hiện tại.")
            selected = next((f for f in self.list() if f["id"] == manifest_id), None)
            if not selected:
                raise DriveError("Không tìm thấy bản sao lưu trong kho Drive này.")
            self.state = {"status": "running", "message": "Đang kiểm tra manifest…"}
            self.thread = threading.Thread(target=self.run, args=(selected,), daemon=True)
            self.thread.start()
            return dict(self.state)

    def run(self, selected):
        try:
            added = self.restore(selected)
            self.patch(
                status="succeeded",
                message=f"Đã khôi phục {added} project mới. Project hiện có được giữ nguyên.",
            )
        except Exception:
            self.patch(
                status="failed",
                message="Không thể khôi phục bản này; dữ liệu hiện có được giữ nguyên. Kiểm tra kết nối và checksum.",
            )

    def restore(self, selected):
        if selected["bytes"] > 16 * 1024**2:
            raise DriveError("Manifest vượt giới hạn 16 MiB.")
        with tempfile.TemporaryDirectory(
            prefix="drive-restore-", dir=self.store.root / "runtime"
        ) as temp:
            stage = Path(temp)
            self.drive.download(
                selected["id"], stage / "manifest.json", selected["bytes"], selected["md5"]
            )
            manifest = parse_json((stage / "manifest.json").read_bytes())
            if (
                manifest.get("format") != "amvs-drive-checkpoint/1"
                or not re.fullmatch(r"[a-f0-9]{32}", manifest.get("snapshotId", ""))
                or not isinstance(manifest.get("assets"), dict)
                or not isinstance(manifest.get("projects"), list)
            ):
                raise DriveError("Định dạng manifest chưa được hỗ trợ.")
            if len(manifest["assets"]) > 10000 or len(manifest["projects"]) > 1000:
                raise DriveError("Manifest vượt giới hạn số file.")
            exports = manifest.get("exports", [])
            if not isinstance(exports, list) or len(exports) > 1000:
                raise DriveError("Danh sách MP4 không hợp lệ.")
            media_folder = self.drive.child_folder(self.drive.data["folder"], "Media")
            project_folder = self.drive.child_folder(self.drive.data["folder"], "Projects")
            export_folder = self.drive.child_folder(self.drive.data["folder"], "Exports")
            catalog = self.store.assets()
            recovered = {}
            for id, asset in manifest["assets"].items():
                if (
                    not re.fullmatch(r"[a-f0-9]{64}", id)
                    or asset.get("id") != id
                    or not re.fullmatch(
                        re.escape(id) + r"\.(png|jpg|jpeg|mp4|mp3|m4a|wav)", asset.get("file", "")
                    )
                ):
                    raise DriveError("Media inventory không hợp lệ.")
                self.store.pin_assets([id])
                meta = self.drive.request(
                    "GET",
                    API + "/" + asset["fileId"],
                    headers=self.drive.auth(),
                    params={"fields": "parents,trashed,size,md5Checksum"},
                ).json()
                if (
                    meta.get("trashed")
                    or media_folder not in meta.get("parents", [])
                    or int(meta.get("size", -1)) != asset["bytes"]
                ):
                    raise DriveError("Media không còn trong kho đã chọn.")
                target = contained(
                    self.store.root / "library" / asset["file"], self.store.root / "library"
                )
                if target.is_file() and digest_file(target) == id:
                    recovered[id] = asset
                    continue
                self.patch(
                    message=f"Đang tải media ({len(recovered) + 1}/{len(manifest['assets'])})…"
                )
                self.drive.download(
                    asset["fileId"], stage / asset["file"], asset["bytes"], asset["md5"], id
                )
                recovered[id] = asset
            rows = []
            for entry in manifest["projects"]:
                meta = self.drive.request(
                    "GET",
                    API + "/" + entry["fileId"],
                    headers=self.drive.auth(),
                    params={"fields": "parents,trashed,size,md5Checksum"},
                ).json()
                if (
                    meta.get("trashed")
                    or project_folder not in meta.get("parents", [])
                    or int(meta.get("size", -1)) != entry["bytes"]
                ):
                    raise DriveError("Project snapshot không còn trong kho đã chọn.")
                name = f"{entry['id']}-{entry['revision']}-{manifest['snapshotId']}.amvs.json"
                if not re.fullmatch(r"[A-Za-z0-9_-]{1,100}-[0-9]+-[a-f0-9]{32}\.amvs\.json", name):
                    raise DriveError("Tên project snapshot không hợp lệ.")
                self.patch(
                    message=f"Đang tải project ({len(rows) + 1}/{len(manifest['projects'])})…"
                )
                path = stage / f"project-{len(rows)}.json"
                self.drive.download(entry["fileId"], path, entry["bytes"], entry["md5"])
                envelope = parse_json(path.read_bytes())
                project = envelope["project"]
                if (
                    envelope.get("format") != "amvs-manual/1"
                    or project["id"] != entry["id"]
                    or (
                        content_hash(project) != entry["contentHash"]
                        or envelope.get("contentHash") != entry["contentHash"]
                    )
                    or set(envelope.get("assets", {})) != set(project["assetRefs"])
                ):
                    raise DriveError("Nội dung project không khớp manifest.")
                if not set(project["assetRefs"]) <= set(recovered):
                    raise DriveError("Project tham chiếu media ngoài manifest.")
                validate(project, {**catalog, **recovered})
                validate_view(envelope.get("view", {}))
                saved_hash = envelope.get("manualSavedHash")
                if saved_hash is not None and (
                    not isinstance(saved_hash, str) or not re.fullmatch(r"[a-f0-9]{64}", saved_hash)
                ):
                    raise DriveError("Manual hash không hợp lệ.")
                rows.append((project, envelope.get("view", {}), saved_hash))
            restored_exports = []
            local_exports = contained(self.store.root / "exports", self.store.root)
            local_exports.mkdir(exist_ok=True)
            for entry in exports:
                sha = entry.get("sha256", "")
                if not re.fullmatch(r"[a-f0-9]{64}", sha):
                    raise DriveError("Checksum MP4 không hợp lệ.")
                target = contained(local_exports / (sha + ".mp4"), local_exports)
                if target.is_file() and digest_file(target) == sha:
                    continue
                meta = self.drive.request(
                    "GET",
                    API + "/" + entry["fileId"],
                    headers=self.drive.auth(),
                    params={"fields": "parents,trashed,size,md5Checksum"},
                ).json()
                if (
                    meta.get("trashed")
                    or export_folder not in meta.get("parents", [])
                    or int(meta.get("size", -1)) != entry["bytes"]
                ):
                    raise DriveError("MP4 không còn trong kho đã chọn.")
                self.patch(message=f"Đang tải MP4 ({len(restored_exports) + 1}/{len(exports)})…")
                source = stage / ("export-" + sha + ".mp4")
                self.drive.download(entry["fileId"], source, entry["bytes"], entry["md5"], sha)
                restored_exports.append((source, target))
            templates = manifest.get("templates", [])
            if not isinstance(templates, list) or len(templates) > 1000:
                raise DriveError("Template inventory không hợp lệ.")
            template_rows = []
            if templates:
                template_folder = self.drive.child_folder(self.drive.data["folder"], "Templates")
                for entry in templates:
                    if (
                        not re.fullmatch(r"[a-f0-9]{32}", entry.get("id", ""))
                        or not re.fullmatch(r"[a-f0-9]{64}", entry.get("sha256", ""))
                        or not isinstance(entry.get("bytes"), int)
                        or not 0 < entry["bytes"] <= 16 * 1024**2
                    ):
                        raise DriveError("Template descriptor không hợp lệ.")
                    meta = self.drive.request(
                        "GET",
                        API + "/" + entry["fileId"],
                        headers=self.drive.auth(),
                        params={"fields": "parents,trashed,size"},
                    ).json()
                    if (
                        meta.get("trashed")
                        or template_folder not in meta.get("parents", [])
                        or int(meta.get("size", -1)) != entry["bytes"]
                    ):
                        raise DriveError("Template không còn trong kho.")
                    path = stage / (entry["id"] + ".template.json")
                    self.drive.download(
                        entry["fileId"], path, entry["bytes"], entry["md5"], entry["sha256"]
                    )
                    template = parse_json(path.read_bytes())
                    validate_template(template)
                    if not set(template["defaultProject"]["assetRefs"]) <= set(recovered):
                        raise DriveError("Template tham chiếu media ngoài manifest.")
                    validate(template["defaultProject"], {**catalog, **recovered})
                    if template["id"] != entry["id"]:
                        raise DriveError("Template ID không khớp.")
                    template_rows.append(template)
            self.store.pin_assets(recovered.keys())
            published = []
            try:
                for id, asset in recovered.items():
                    source = stage / asset["file"]
                    target = contained(
                        self.store.root / "library" / asset["file"], self.store.root / "library"
                    )
                    if source.is_file():
                        if target.exists():
                            raise DriveError(
                                "Media local trùng tên nhưng sai checksum; dừng khôi phục."
                            )
                        source.replace(target)
                        published.append(target)
                for source, target in restored_exports:
                    if target.exists():
                        raise DriveError("MP4 local trùng tên nhưng sai checksum; dừng khôi phục.")
                    source.replace(target)
                    published.append(target)
                added = 0
                with self.store.connect() as db:
                    for id, asset in recovered.items():
                        db.execute(
                            "INSERT OR IGNORE INTO assets VALUES(?,?)", (id, json.dumps(asset))
                        )
                    for template in template_rows:
                        db.execute(
                            "INSERT OR IGNORE INTO templates VALUES(?,?)",
                            (template["id"], json.dumps(template)),
                        )
                    for project, view, hash in rows:
                        if db.execute(
                            "SELECT 1 FROM projects WHERE id=?", (project["id"],)
                        ).fetchone():
                            continue
                        db.execute(
                            "INSERT INTO projects VALUES(?,?,?,?,?)",
                            (project["id"], canonical(project).decode(), json.dumps(view), 1, hash),
                        )
                        added += 1
                return added
            except BaseException:
                for path in published:
                    path.unlink(missing_ok=True)
                raise

    def close(self):
        if self.thread:
            self.thread.join()
