"""Explicit cloud checkpoints; working SQLite and manual-save state stay local."""

import hashlib
import json
import tempfile
import threading
import uuid
from pathlib import Path

from .domain import content_hash, parse_json, validate
from .drive import API, DriveError
from .store import contained, digest_file


class DriveBackup:
    def __init__(self, drive, store):
        self.drive, self.store = drive, store
        self.lock = threading.Lock()
        self.thread = None
        self.state = {"status": "idle", "message": "Chưa sao lưu lên Drive."}
        self.stop_signal = threading.Event()
        self.monitor = None

    def start_monitor(self):
        if not self.monitor:
            self.monitor = threading.Thread(target=self.auto_loop, daemon=True)
            self.monitor.start()

    def auto_loop(self):
        while not self.stop_signal.wait(30):
            try:
                if self.status()["status"] == "failed":
                    self.stop_signal.wait(300)
                if not self.drive.status()["autoSync"] or self.status()["status"] == "running":
                    continue
                if self.inventory_fingerprint() != (self.drive.status()["lastBackup"] or {}).get(
                    "fingerprint"
                ):
                    self.start()
            except Exception:
                self.stop_signal.wait(300)

    def inventory_fingerprint(self):
        with self.store.connect() as db:
            rows = [
                list(db.execute("SELECT id,metadata FROM assets ORDER BY id")),
                list(db.execute("SELECT id,body,view,revision FROM projects ORDER BY id")),
                list(db.execute("SELECT id,body FROM jobs ORDER BY id")),
            ]
        # Job progress changes should not trigger repeated cloud snapshots.
        jobs = [
            (id, row)
            for id, raw in rows[2]
            if (row := parse_json(raw)).get("status") == "succeeded"
        ]
        payload = [
            list(map(tuple, rows[0])),
            list(map(tuple, rows[1])),
            [(id, row.get("outputFile")) for id, row in jobs],
        ]
        return hashlib.sha256(
            json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()
        ).hexdigest()

    def status(self):
        with self.lock:
            return dict(self.state)

    def start(self):
        with self.lock:
            if self.state["status"] == "running":
                raise DriveError("Đang sao lưu Drive. Hãy chờ hoàn tất.")
            connection = self.drive.status()
            if connection["pending"]:
                raise DriveError("Hãy hoàn tất hoặc hủy đăng nhập trước khi sao lưu.")
            if not connection["connected"]:
                raise DriveError("Hãy kết nối Drive trước khi sao lưu.")
            self.state = {"status": "running", "message": "Đang chốt bản sao dữ liệu local…"}
            self.thread = threading.Thread(target=self.run, daemon=True)
            self.thread.start()
            return dict(self.state)

    def patch(self, **values):
        with self.lock:
            self.state.update(values)

    def run(self):
        try:
            self.copy()
        except Exception:
            # No provider body, token, filesystem paths, or project text in error responses.
            self.patch(
                status="failed",
                message="Sao lưu chưa hoàn tất. Kiểm tra mạng, quyền và quota Drive; bản local vẫn được giữ.",
            )

    def copy(self):
        fingerprint = self.inventory_fingerprint()
        # One SQLite read transaction captures a coherent inventory, never DB bytes.
        with self.store.connect() as db:
            db.execute("BEGIN")
            catalog = {
                r["id"]: parse_json(r["metadata"]) for r in db.execute("SELECT * FROM assets")
            }
            projects = [
                {
                    "project": parse_json(r["body"]),
                    "view": parse_json(r["view"]),
                    "revision": r["revision"],
                    "manualSavedHash": r["saved_hash"],
                }
                for r in db.execute("SELECT * FROM projects")
            ]
            jobs = [parse_json(r["body"]) for r in db.execute("SELECT * FROM jobs")]
        for row in projects:
            validate(row["project"], catalog)
            row["contentHash"] = content_hash(row["project"])
        root = self.drive.data["folder"]
        folders = {
            name: self.drive.child_folder(root, name)
            for name in ("Media", "Projects", "Exports", "Lyrics", "Templates", "Backups")
        }
        snapshot = uuid.uuid4().hex
        manifest = {
            "format": "amvs-drive-checkpoint/1",
            "snapshotId": snapshot,
            "assets": {},
            "projects": [],
            "exports": [],
        }
        previous_assets = {}
        last = self.drive.status().get("lastBackup") or {}
        if last.get("manifestId"):
            try:
                old = self.drive.request(
                    "GET",
                    API + "/" + last["manifestId"],
                    headers=self.drive.auth(),
                    params={"fields": "size,md5Checksum,trashed"},
                ).json()
                if not old.get("trashed") and int(old["size"]) <= 16 * 1024**2:
                    with tempfile.TemporaryDirectory(
                        prefix="drive-prev-", dir=self.store.root / "runtime"
                    ) as prior:
                        path = Path(prior) / "manifest.json"
                        self.drive.download(
                            last["manifestId"], path, int(old["size"]), old["md5Checksum"]
                        )
                        previous_assets = parse_json(path.read_bytes()).get("assets", {})
            except (DriveError, ValueError, KeyError):
                previous_assets = {}
        for id, asset in catalog.items():
            self.patch(
                message=f"Đang sao lưu media ({len(manifest['assets']) + 1}/{len(catalog)})…"
            )
            path = self.store.asset_path(asset)
            if digest_file(path) != id:
                raise DriveError("Media local sai checksum.")
            copied = None
            candidate = previous_assets.get(id, {})
            if candidate.get("bytes") == asset["bytes"] and candidate.get("file") == asset["file"]:
                try:
                    meta = self.drive.request(
                        "GET",
                        API + "/" + candidate["fileId"],
                        headers=self.drive.auth(),
                        params={"fields": "parents,trashed,size,md5Checksum"},
                    ).json()
                    if (
                        not meta.get("trashed")
                        and folders["Media"] in meta.get("parents", [])
                        and int(meta.get("size", -1)) == asset["bytes"]
                        and meta.get("md5Checksum") == candidate.get("md5")
                    ):
                        copied = {key: candidate[key] for key in ("fileId", "bytes", "md5")}
                except (DriveError, KeyError, ValueError):
                    pass
            if copied is None:
                copied = self.drive.upload(path, folders["Media"], asset["file"], asset["mime"])
            manifest["assets"][id] = {**asset, **copied}
        with tempfile.TemporaryDirectory(prefix="drive-", dir=self.store.root / "runtime") as stage:
            stage = Path(stage)
            for row in projects:
                # Each run writes immutable files. It never overwrites another revision.
                name = f"{row['project']['id']}-{row['revision']}-{snapshot}.amvs.json"
                path = contained(stage / name, stage)
                envelope = {
                    "format": "amvs-manual/1",
                    **row,
                    "assets": {id: manifest["assets"][id] for id in row["project"]["assetRefs"]},
                }
                path.write_text(
                    json.dumps(envelope, ensure_ascii=False, allow_nan=False), encoding="utf-8"
                )
                copied = self.drive.upload(path, folders["Projects"], name, "application/json")
                manifest["projects"].append(
                    {
                        "id": row["project"]["id"],
                        "revision": row["revision"],
                        "contentHash": row["contentHash"],
                        **copied,
                    }
                )
            for job in jobs:
                if job.get("status") != "succeeded":
                    continue
                # Only outputs registered by the backend, never a client-supplied path.
                path = contained(job["outputFile"], job["grant"])
                if not path.is_file():
                    raise DriveError("MP4 đã xuất bị thiếu; không công bố snapshot đầy đủ.")
                self.patch(message="Đang sao lưu MP4 đã xuất…")
                copied = self.drive.upload(
                    path, folders["Exports"], f"{job['id']}-{snapshot}.mp4", "video/mp4"
                )
                manifest["exports"].append(
                    {"jobId": job["id"], "sha256": digest_file(path), **copied}
                )
            path = stage / f"{snapshot}.json"
            path.write_text(
                json.dumps(manifest, ensure_ascii=False, allow_nan=False), encoding="utf-8"
            )
            final = self.drive.upload(path, folders["Backups"], path.name, "application/json")
        # Verify the final manifest exists under the selected root's Backups folder.
        verified = self.drive.request(
            "GET",
            API + "/" + final["fileId"],
            headers=self.drive.auth(),
            params={"fields": "id,parents,trashed,size,md5Checksum"},
        ).json()
        if (
            verified.get("trashed")
            or folders["Backups"] not in verified.get("parents", [])
            or verified.get("md5Checksum") != final["md5"]
        ):
            raise DriveError("Không xác minh được manifest cuối.")
        with self.drive.lock:
            self.drive.data["lastBackup"] = {
                "snapshotId": snapshot,
                "manifestId": final["fileId"],
                "assets": len(catalog),
                "projects": len(projects),
                "exports": len(manifest["exports"]),
                "fingerprint": fingerprint,
            }
            self.drive.persist()
        self.patch(
            status="succeeded",
            message="Đã kiểm tra checksum các file và manifest trên Drive. Chưa kiểm chứng khôi phục sang máy khác.",
        )

    def close(self):
        self.stop_signal.set()
        if self.monitor:
            self.monitor.join(timeout=2)
        # Request timeouts are bounded. Do not close the HTTP client during an upload.
        if self.thread:
            self.thread.join()
