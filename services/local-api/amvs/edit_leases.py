"""In-memory, expiring per-project editor ownership. No persisted capabilities."""

import re
import threading
import time
from contextlib import contextmanager

from .store import Conflict


class EditLeases:
    def __init__(self, clock=time.monotonic):
        self.clock = clock
        self.rows = {}
        self.lock = threading.RLock()

    def claim(self, project_id, editor, takeover=False):
        if not isinstance(editor, str) or not re.fullmatch(r"[A-Za-z0-9_-]{16,100}", editor):
            raise PermissionError("Editor session không hợp lệ.")
        with self.lock:
            row = self.rows.get(project_id)
            now = self.clock()
            allowed = not row or row["expires"] <= now or row["editor"] == editor or takeover
            if allowed:
                self.rows[project_id] = {"editor": editor, "expires": now + 30}
            return {
                "canWrite": allowed,
                "expiresInSeconds": 30 if allowed else max(0, round(row["expires"] - now)),
            }

    def release(self, project_id, editor):
        with self.lock:
            row = self.rows.get(project_id)
            if row and row["editor"] == editor:
                del self.rows[project_id]
                return {"released": True}
            return {"released": False}

    @contextmanager
    def guard(self, project_id, editor):
        with self.lock:
            row = self.rows.get(project_id)
            if row and (row["expires"] <= self.clock() or row["editor"] != editor):
                raise Conflict("Project đang được chỉnh sửa ở tab khác; nhận quyền trước khi ghi.")
            yield
