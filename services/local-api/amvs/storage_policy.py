"""Configurable cache budget and disk reserve; never evicts source media."""

import json
import os
import shutil
import threading
import uuid

from .domain import parse_json
from .store import contained


class StorageQuota(ValueError):
    pass


class StoragePolicy:
    def __init__(self, store):
        self.store = store
        self.lock = threading.RLock()
        self.path = contained(store.root / "runtime/storage-policy.json", store.root)

    def read(self):
        value = {"cacheQuotaMiB": 512, "reserveGiB": 2}
        if self.path.exists():
            saved = parse_json(self.path.read_bytes())
            self.validate(saved)
            value.update(saved)
        return value

    def validate(self, value):
        if (
            not isinstance(value, dict)
            or set(value) != {"cacheQuotaMiB", "reserveGiB"}
            or any(type(v) is not int for v in value.values())
            or not 32 <= value["cacheQuotaMiB"] <= 4096
            or not 2 <= value["reserveGiB"] <= 64
        ):
            raise ValueError("Quota cache 32–4096 MiB và dự phòng 2–64 GiB.")

    def configure(self, value):
        self.validate(value)
        with self.lock:
            stage = self.path.with_name(uuid.uuid4().hex + ".stage")
            try:
                with stage.open("xb") as file:
                    file.write(json.dumps(value).encode())
                    file.flush()
                    os.fsync(file.fileno())
                os.replace(stage, self.path)
            finally:
                stage.unlink(missing_ok=True)
        return self.status()

    def cache_files(self):
        folder = contained(self.store.root / "cache/thumbnails", self.store.root)
        if not folder.exists():
            return []
        import re

        return [
            contained(path, folder)
            for path in folder.iterdir()
            if path.is_file() and re.fullmatch(r"[a-f0-9]{64}\.jpg", path.name)
        ]

    def status(self):
        with self.lock:
            policy = self.read()
            size = sum(f.stat().st_size for f in self.cache_files())
            free = shutil.disk_usage(self.store.root).free
            return {
                **policy,
                "cacheBytes": size,
                "freeBytes": free,
                "warning": "Cache đã đạt quota; có thể dọn thumbnail để tạo lại."
                if size >= policy["cacheQuotaMiB"] * 1024**2
                else "Dung lượng trống dưới mức dự phòng."
                if free < policy["reserveGiB"] * 1024**3
                else "",
            }

    def check_cache(self, added):
        status = self.status()
        if (
            status["cacheBytes"] + added > status["cacheQuotaMiB"] * 1024**2
            or status["freeBytes"] - added < status["reserveGiB"] * 1024**3
        ):
            raise StorageQuota(
                "Chưa đủ quota cache hoặc dung lượng dự phòng. Dọn cache hoặc đổi quota trong Dữ liệu project."
            )

    def clear_cache(self):
        with self.lock:
            deleted = 0
            failed = 0
            for path in self.cache_files():
                try:
                    path.unlink()
                    deleted += 1
                except OSError:
                    failed += 1
            return {"deleted": deleted, "failed": failed, "sourceMediaPreserved": True}
