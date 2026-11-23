"""Forced-parent-exit fixture for Windows Job Object ownership verification."""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from launcher_lifecycle import WindowsOwnership

owner = WindowsOwnership(Path(sys.argv[1]).parent / "owner-scope")
Path(sys.argv[1]).with_suffix(".owner").write_text(str(os.getpid()))
owner.launch([sys.executable, str(ROOT / "tests/fixtures/owned_process.py"), sys.argv[1]])
import time

time.sleep(120)
