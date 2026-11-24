"""Test-only server grants disposable folders; no production endpoint accepts paths."""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "services/local-api"))
sys.path.insert(0, str(ROOT / "scripts"))
from amvs.app import create_app
from test_assets import prepare, prepare_video

prepare()
prepare_video()
run = Path(os.environ["AMVS_TEST_RUN"]).resolve()
assert run.is_relative_to((ROOT / ".local").resolve())
run.mkdir(parents=True, exist_ok=True)
app = create_app(
    workspace=run / "workspace", headroom=float(os.environ.get("AMVS_TEST_HEADROOM_GIB", "4"))
)
for scope in ["project", "export", "backup"]:
    folder = run / scope
    folder.mkdir(exist_ok=True)
    app.state.grants["e2e-" + scope] = {"scope": scope, "path": folder}

# Optional fidelity harness: restore only generated, completed matrix snapshots.
# This path is supplied by the test launcher, never by a production client endpoint.
if os.environ.get("AMVS_FIDELITY_RUN"):
    import copy
    import json
    import shutil
    import sqlite3

    from amvs.store import digest_file

    source = Path(os.environ["AMVS_FIDELITY_RUN"]).resolve()
    assert source.is_relative_to((ROOT / ".local/evidence/s6").resolve())
    database = sqlite3.connect(source / "workspace/runtime/studio.sqlite")
    try:
        jobs = [json.loads(row[0]) for row in database.execute("SELECT body FROM jobs")]
        catalog = {
            id: json.loads(raw) for id, raw in database.execute("SELECT id,metadata FROM assets")
        }
    finally:
        database.close()
    cases = []
    for template in ("TPL-01", "TPL-02", "TPL-03"):
        job = next(
            j
            for j in jobs
            if j["kind"] == "render"
            and j["status"] == "succeeded"
            and j["project"]["templateRef"]["id"] == template
            and j["project"]["preset"] == {"width": 720, "height": 1280, "fps": 30}
        )
        project = copy.deepcopy(job["project"])
        # Name is deliberately nonvisual; all scene fields remain byte-equivalent.
        project["name"] = "Đối chiếu " + template
        for key in project["assetRefs"]:
            asset = catalog[key]
            original = (source / "workspace/library" / asset["file"]).resolve()
            assert (
                original.is_relative_to((source / "workspace/library").resolve())
                and digest_file(original) == key
            )
            target = app.state.store.root / "library" / asset["file"]
            if not target.exists():
                shutil.copyfile(original, target)
            app.state.store.put_asset(asset)
        app.state.store.create(project)
        cases.append(
            {
                "projectId": project["id"],
                "name": project["name"],
                "template": template,
                "output": job["outputFile"],
                "frames": [15, 45]
                if template == "TPL-02"
                else [7, 22, 37, 52]
                if template == "TPL-03"
                else [30],
            }
        )
    (run / "fidelity-inputs.json").write_text(
        json.dumps(cases, ensure_ascii=False, indent=2), encoding="utf-8"
    )
