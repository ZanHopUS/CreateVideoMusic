"""Explicit, conservative collection of unreferenced managed library entries.

Manual/legacy pins persist; current-session history pins last until API restart.
No background source deletion. Candidates are recomputed immediately before removal.
"""

import json
import re

from .domain import parse_json
from .store import contained


class SourceGC:
    def __init__(self, store):
        self.store = store

    def pinned(self):
        pins = set(self.store.session_pins)
        with self.store.connect() as db:
            pins.update(r[0] for r in db.execute("SELECT asset_id FROM asset_pins"))
            for row in db.execute("SELECT body FROM projects"):
                pins.update(parse_json(row[0])["assetRefs"])
            for row in db.execute("SELECT body FROM jobs"):
                pins.update(parse_json(row[0]).get("project", {}).get("assetRefs", []))
            for row in db.execute("SELECT body FROM templates"):
                pins.update(parse_json(row[0])["defaultProject"]["assetRefs"])
        for file in (self.store.root / "recovery").glob("*/*.json"):
            path = contained(file, self.store.root)
            if path.stat().st_size > 16 * 1024**2:
                raise ValueError("Recovery quá lớn; chưa thể chứng minh media không dùng.")
            pins.update(parse_json(path.read_bytes())["project"]["assetRefs"])
        return pins

    def preview(self):
        with self.store.pin_lock:
            pins = self.pinned()
            rows = []
            for id, asset in self.store.assets().items():
                if id in pins:
                    continue
                if not re.fullmatch(r"[a-f0-9]{64}", id) or not re.fullmatch(
                    id + r"\.(png|jpg|jpeg|mp4|wav|mp3|m4a)", asset.get("file", "")
                ):
                    raise ValueError("Asset catalog không hợp lệ.")
                path = contained(
                    self.store.root / "library" / asset["file"], self.store.root / "library"
                )
                rows.append(
                    {
                        "id": id,
                        "name": asset["name"],
                        "bytes": path.stat().st_size if path.is_file() else 0,
                    }
                )
            return {
                "candidates": rows,
                "pinnedCount": len(pins),
                "policy": "manual/legacy/project/recovery/template/job/session-history pins; explicit selection only",
            }

    def collect(self, ids):
        if (
            not isinstance(ids, list)
            or len(ids) > 4096
            or any(not isinstance(i, str) for i in ids)
            or len(set(ids)) != len(ids)
        ):
            raise ValueError("Danh sách media không hợp lệ.")
        with self.store.pin_lock:
            permitted = {r["id"] for r in self.preview()["candidates"]}
            if not set(ids) <= permitted:
                raise ValueError("Media đang được dùng hoặc vừa được pin; dừng dọn.")
            catalog = self.store.assets()
            deleted = []
            failed = []
            for id in ids:
                asset = catalog[id]
                path = contained(
                    self.store.root / "library" / asset["file"], self.store.root / "library"
                )
                # Commit catalog removal first. Crash before unlink leaves recoverable,
                # untracked bytes rather than a catalog record with a missing file.
                with self.store.connect() as db:
                    db.execute("DELETE FROM assets WHERE id=?", (id,))
                try:
                    path.unlink(missing_ok=True)
                except OSError:
                    with self.store.connect() as db:
                        db.execute(
                            "INSERT OR IGNORE INTO assets VALUES(?,?)", (id, json.dumps(asset))
                        )
                    failed.append(id)
                else:
                    deleted.append(id)
            return {
                "deleted": deleted,
                "failed": failed,
                "manualProjectsAndOriginalFilesPreserved": True,
            }
