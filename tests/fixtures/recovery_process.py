"""Disposable crash-test child, never launched against the user's workspace."""

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "services/local-api"))
from amvs.snapshots import Snapshots
from amvs.store import Store

store = Store(Path(sys.argv[1]))
row = store.load(sys.argv[2])
project = {**row["project"], "name": "Bản trước crash"}
store.update(project["id"], project, row["revision"])
Snapshots(store).capture(project["id"])
Path(sys.argv[3]).write_text("published", encoding="utf-8")
while True:
    time.sleep(1)
