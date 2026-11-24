"""SQLite working persistence, revisions and independent manual checkpoints."""

import hashlib
import json
import os
import sqlite3
import threading
import uuid
from contextlib import contextmanager
from functools import wraps
from pathlib import Path

from .domain import canonical, content_hash, parse_json, validate


class Conflict(Exception):
    pass


def digest_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def contained(path, root):
    path, root = Path(path).resolve(), Path(root).resolve()
    if not path.is_relative_to(root):
        raise PermissionError("Đường dẫn nằm ngoài phạm vi được cấp.")
    return path


def validate_view(view):
    # Imported envelopes share the same view budget as PATCH. Missing view is
    # represented by {}, while explicit non-object state cannot crash the UI.
    if not isinstance(view, dict) or len(json.dumps(view, allow_nan=False)) > 65536:
        raise ValueError("View state không hợp lệ.")
    return view


def pin_guard(method):
    @wraps(method)
    def guarded(self, *args, **kwargs):
        with self.pin_lock:
            return method(self, *args, **kwargs)

    return guarded


class Store:
    def __init__(self, workspace):
        self.pin_lock = threading.RLock()
        self.session_pins = set()
        self.root = Path(workspace).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / "runtime").mkdir(exist_ok=True)
        (self.root / "library").mkdir(exist_ok=True)
        contained(self.root / "runtime", self.root)
        contained(self.root / "library", self.root)
        self.path = self.root / "runtime/studio.sqlite"
        with self.connect() as db:
            version = db.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0, 1):
                raise ValueError("Database version không được hỗ trợ.")
            had_pins = db.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='asset_pins'"
            ).fetchone()
            db.executescript("""CREATE TABLE IF NOT EXISTS projects(
              id TEXT PRIMARY KEY, body TEXT NOT NULL, view TEXT NOT NULL,
              revision INTEGER NOT NULL, saved_hash TEXT);
              CREATE TABLE IF NOT EXISTS assets(id TEXT PRIMARY KEY, metadata TEXT NOT NULL);
              CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY, body TEXT NOT NULL);
              CREATE TABLE IF NOT EXISTS templates(id TEXT PRIMARY KEY, body TEXT NOT NULL);
              CREATE TABLE IF NOT EXISTS asset_pins(asset_id TEXT NOT NULL, reason TEXT NOT NULL, PRIMARY KEY(asset_id,reason));
              PRAGMA user_version=1;""")
            if not had_pins:
                db.execute(
                    "INSERT OR IGNORE INTO asset_pins SELECT id,'legacy-manual-inventory-unknown' FROM assets"
                )

    @contextmanager
    def connect(self):
        db = sqlite3.connect(contained(self.path, self.root), timeout=5)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("PRAGMA synchronous=FULL")
        try:
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def assets(self):
        with self.connect() as db:
            return {r["id"]: parse_json(r["metadata"]) for r in db.execute("SELECT * FROM assets")}

    @pin_guard
    def put_asset(self, asset):
        self.session_pins.add(asset["id"])
        with self.connect() as db:
            db.execute("INSERT OR IGNORE INTO assets VALUES(?,?)", (asset["id"], json.dumps(asset)))

    def asset_path(self, asset):
        library = contained(self.root / "library", self.root)
        path = contained(library / asset["file"], library)
        if not path.is_file():
            raise FileNotFoundError("Không tìm thấy media.")
        return path

    @pin_guard
    def create(self, project):
        validate(project, self.assets())
        with self.connect() as db:
            try:
                db.execute(
                    "INSERT INTO projects VALUES(?,?,?,?,NULL)",
                    (project["id"], canonical(project).decode(), "{}", 1),
                )
            except sqlite3.IntegrityError as error:
                raise Conflict("Project đã tồn tại.") from error
        return self.load(project["id"])

    def load(self, id):
        with self.connect() as db:
            row = db.execute("SELECT * FROM projects WHERE id=?", (id,)).fetchone()
        if row is None:
            raise KeyError(id)
        project = parse_json(row["body"])
        hash = content_hash(project)
        self.pin_assets(project["assetRefs"])
        return {
            "project": project,
            "view": parse_json(row["view"]),
            "revision": row["revision"],
            "contentHash": hash,
            "manualSavedHash": row["saved_hash"],
            "dirty": hash != row["saved_hash"],
        }

    def list_projects(self):
        with self.connect() as db:
            return [
                {"id": r["id"], "name": parse_json(r["body"])["name"]}
                for r in db.execute("SELECT * FROM projects ORDER BY rowid DESC")
            ]

    @pin_guard
    def update(self, id, project, revision, view=None):
        validate(project, self.assets())
        if project["id"] != id:
            raise ValueError("Project ID không khớp.")
        if view is not None:
            validate_view(view)
        with self.connect() as db:
            if view is None:
                cursor = db.execute(
                    "UPDATE projects SET body=?,revision=revision+1 WHERE id=? AND revision=?",
                    (canonical(project).decode(), id, revision),
                )
            else:
                cursor = db.execute(
                    "UPDATE projects SET body=?,view=?,revision=revision+1 WHERE id=? AND revision=?",
                    (canonical(project).decode(), json.dumps(view), id, revision),
                )
            if cursor.rowcount != 1:
                raise Conflict("Project đã thay đổi; tải lại trước khi ghi.")
        return self.load(id)

    @pin_guard
    def save(self, id, project, revision, folder):
        current = self.load(id)
        if current["revision"] != revision:
            raise Conflict("Project đã thay đổi trước khi lưu.")
        if project["id"] != id or content_hash(project) != current["contentHash"]:
            raise Conflict("Snapshot chưa được ghi vào working state.")
        catalog = self.assets()
        validate(project, catalog)
        for name in project["assetRefs"]:
            if name not in catalog or digest_file(self.asset_path(catalog[name])) != name:
                raise ValueError("Media thiếu hoặc checksum sai.")
        self.pin_manual(project["assetRefs"])
        folder = Path(folder).resolve()
        if not folder.is_dir():
            raise ValueError("Thư mục đã chọn không tồn tại.")
        target = contained(folder / f"{id}.amvs.json", folder)
        staging = contained(folder / f".{id}.{uuid.uuid4().hex}.stage", folder)
        body = {
            "format": "amvs-manual/1",
            "contentHash": current["contentHash"],
            "project": project,
            "view": current["view"],
            "assets": {name: catalog[name] for name in project["assetRefs"]},
        }
        try:
            with staging.open("xb") as output:
                output.write(json.dumps(body, ensure_ascii=False, allow_nan=False).encode())
                output.flush()
                os.fsync(output.fileno())
            check = parse_json(staging.read_bytes())
            if content_hash(check["project"]) != check["contentHash"]:
                raise ValueError("Snapshot validation failed.")
            contained(staging, folder)
            contained(target, folder)
            os.replace(staging, target)
        finally:
            contained(staging, folder).unlink(missing_ok=True)
        with self.connect() as db:
            db.execute("UPDATE projects SET saved_hash=? WHERE id=?", (current["contentHash"], id))
        return self.load(id)

    @pin_guard
    def open_manual(self, file):
        if Path(file).stat().st_size > 16 * 1024**2:
            raise ValueError("File project vượt giới hạn 16 MiB.")
        envelope = parse_json(Path(file).read_bytes())
        if envelope.get("format") != "amvs-manual/1" or content_hash(
            envelope["project"]
        ) != envelope.get("contentHash"):
            raise ValueError("File lưu không hợp lệ.")
        project = envelope["project"]
        validate_view(envelope.get("view", {}))
        validate(project, self.assets())
        self.pin_manual(project["assetRefs"])
        for id in project["assetRefs"]:
            asset = self.assets().get(id)
            if not asset or digest_file(self.asset_path(asset)) != id:
                raise ValueError("Media bị thiếu; cần liên kết lại.")
        try:
            current = self.load(project["id"])
        except KeyError:
            current = self.create(project)
        # Opening an old manual snapshot never silently overwrites dirty working edits.
        if current["dirty"] and current["contentHash"] != envelope["contentHash"]:
            raise Conflict("Có bản làm việc chưa lưu; mở lại project đó trước.")
        with self.connect() as db:
            db.execute(
                "UPDATE projects SET body=?,view=?,revision=revision+1,saved_hash=? WHERE id=?",
                (
                    canonical(project).decode(),
                    json.dumps(envelope.get("view", {})),
                    envelope["contentHash"],
                    project["id"],
                ),
            )
        return self.load(project["id"])

    def pin_assets(self, ids):
        with self.pin_lock:
            self.session_pins.update(ids)

    def pin_manual(self, ids):
        with self.connect() as db:
            db.executemany(
                "INSERT OR IGNORE INTO asset_pins VALUES(?, 'manual-snapshot')",
                [(id,) for id in ids],
            )

    def put_job(self, job):
        with self.connect() as db:
            db.execute("INSERT OR REPLACE INTO jobs VALUES(?,?)", (job["id"], json.dumps(job)))

    def jobs(self):
        with self.connect() as db:
            return {r["id"]: parse_json(r["body"]) for r in db.execute("SELECT * FROM jobs")}
