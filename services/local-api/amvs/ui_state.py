"""Workspace UI metadata, deliberately separate from project content."""

import json
import os
import threading
import uuid
from datetime import datetime, timezone

from .store import contained


class UIState:
    def __init__(self, store):
        self.store = store
        self.path = contained(store.root / "runtime/ui-state.json", store.root)
        self.lock = threading.RLock()

    def read(self):
        default = {"schemaVersion": 1, "recent": [], "preferences": {"timelineHeight": 280, "projectViewMode": "grid"}, "version": 0}
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            if raw.get("schemaVersion") != 1 or not isinstance(raw.get("recent"), list) or not isinstance(raw.get("preferences"), dict):
                return default
            recent = [item for item in raw["recent"] if isinstance(item, dict) and isinstance(item.get("id"), str) and isinstance(item.get("openedAt"), str)][:30]
            prefs = default["preferences"].copy()
            for key, value in raw["preferences"].items():
                try:
                    self.validate(key, value)
                    prefs[key] = value
                except ValueError:
                    pass
            return {"schemaVersion": 1, "recent": recent, "preferences": prefs, "version": raw.get("version", 0) if type(raw.get("version")) is int else 0}
        except (OSError, ValueError, TypeError, AttributeError):
            return default

    def validate(self, key, value):
        if key == "timelineHeight" and type(value) is int and 180 <= value <= 900:
            return
        if key == "projectViewMode" and value in ("grid", "list"):
            return
        raise ValueError("Tùy chọn giao diện không hợp lệ.")

    def write(self, state):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        stage = self.path.with_name(uuid.uuid4().hex + ".stage")
        try:
            with stage.open("xb") as file:
                file.write(json.dumps(state, ensure_ascii=False).encode("utf-8"))
                file.flush()
                os.fsync(file.fileno())
            os.replace(stage, self.path)
        finally:
            stage.unlink(missing_ok=True)
        return state

    def status(self):
        with self.lock:
            state = self.read()
            existing = {row["id"] for row in self.store.list_projects()}
            state["recent"] = [item for item in state["recent"] if item["id"] in existing]
            return state

    def opened(self, id):
        self.store.load(id)
        with self.lock:
            state = self.read()
            state["recent"] = [{"id": id, "openedAt": datetime.now(timezone.utc).isoformat()}] + [entry for entry in state["recent"] if entry["id"] != id][:29]
            state["version"] += 1
            return self.write(state)

    def preference(self, key, value):
        self.validate(key, value)
        with self.lock:
            state = self.read()
            state["preferences"][key] = value
            state["version"] += 1
            return self.write(state)
