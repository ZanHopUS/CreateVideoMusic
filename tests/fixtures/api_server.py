"""Test-only server grants disposable folders; no production endpoint accepts paths."""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "services/local-api"))
sys.path.insert(0, str(ROOT / "scripts"))
from amvs.app import create_app
from test_assets import prepare

prepare()
run = Path(os.environ["AMVS_TEST_RUN"]).resolve()
assert run.is_relative_to((ROOT / ".local").resolve())
run.mkdir(parents=True, exist_ok=True)
app = create_app(workspace=run / "workspace")
for scope in ["project", "export"]:
    folder = run / scope
    folder.mkdir(exist_ok=True)
    app.state.grants["e2e-" + scope] = {"scope": scope, "path": folder}
