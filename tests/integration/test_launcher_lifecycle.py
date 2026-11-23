import json
import os
import subprocess
import sys
import time
from pathlib import Path

import psutil
import pytest
from launcher_lifecycle import AlreadyRunning, WindowsOwnership, record_path, stop_owner

pytestmark = pytest.mark.skipif(os.name != "nt", reason="Windows Job Objects")
ROOT = Path(__file__).resolve().parents[2]


def test_singleton_releases_after_close(tmp_path):
    first = WindowsOwnership(tmp_path)
    try:
        with pytest.raises(AlreadyRunning):
            WindowsOwnership(tmp_path)
    finally:
        first.close()
    third = WindowsOwnership(tmp_path)
    third.close()


def test_abrupt_launcher_exit_kills_owned_descendants(tmp_path):
    pids = tmp_path / "pids.json"
    parent = subprocess.Popen(
        [sys.executable, str(ROOT / "tests/fixtures/job_owner.py"), str(pids)]
    )
    known = {}
    try:
        deadline = time.monotonic() + 10
        while not pids.exists() and time.monotonic() < deadline:
            time.sleep(0.05)
        assert pids.exists()
        known = json.loads(pids.read_text())
        # The venv wrapper may have a distinct interpreter PID; terminate the
        # interpreter owning the handle, not merely its outer launcher.
        owner = psutil.Process(int(pids.with_suffix(".owner").read_text()))
        assert owner and Path(owner.cwd()).resolve() == ROOT
        owner.kill()
        owner.wait(timeout=10)
        deadline = time.monotonic() + 5
        while any(psutil.pid_exists(p) for p in known.values()) and time.monotonic() < deadline:
            time.sleep(0.05)
        assert all(not psutil.pid_exists(p) for p in known.values())
    finally:
        marker = pids.with_suffix(".owner")
        if marker.exists():
            try:
                psutil.Process(int(marker.read_text())).kill()
            except psutil.NoSuchProcess:
                pass
        for pid in known.values():
            try:
                psutil.Process(pid).kill()
            except psutil.NoSuchProcess:
                pass
        if parent.poll() is None:
            parent.kill()
        parent.wait(timeout=10)


def test_forged_owner_record_cannot_stop_unrelated_process(tmp_path):
    child = subprocess.Popen([sys.executable, "-c", "import time;time.sleep(120)"])
    try:
        process = psutil.Process(child.pid)
        file = record_path(tmp_path)
        file.parent.mkdir(parents=True)
        file.write_text(json.dumps({"pid": child.pid, "created": process.create_time()}))
        with pytest.raises(RuntimeError):
            stop_owner(tmp_path)
        assert child.poll() is None
    finally:
        root = psutil.Process(child.pid)
        for process in [*reversed(root.children(recursive=True)), root]:
            try:
                process.kill()
            except psutil.NoSuchProcess:
                pass
        child.wait(timeout=10)
