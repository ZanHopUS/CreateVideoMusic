import copy
import json
from pathlib import Path

import pytest
from amvs.app import create_app
from amvs.domain import content_hash, parse_json, validate_job, validate_template
from amvs.store import Conflict, Store
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
TOKEN = "integration-test-session-" + "x" * 48
ORIGIN = "http://127.0.0.1:3000"
HEADERS = {"host": "testserver", "origin": ORIGIN, "authorization": "Bearer " + TOKEN}


@pytest.fixture
def project():
    return json.loads((ROOT / "tests/fixtures/project.json").read_text(encoding="utf-8"))


@pytest.fixture
def server(tmp_path):
    app = create_app(tmp_path / "workspace", TOKEN, ORIGIN, "testserver", headroom=0)
    with TestClient(app) as client:
        yield app, client


def test_jcs_golden_and_duplicate_key_parser(project):
    assert content_hash(project) == (ROOT / "tests/fixtures/project.sha256").read_text().strip()
    with pytest.raises(ValueError):
        parse_json('{"name":1,"name":2}')


def test_request_auth_origin_and_no_path_leak(server):
    app, client = server
    assert (
        client.get("/api/v1/projects", headers={"host": "testserver", "origin": ORIGIN}).status_code
        == 401
    )
    assert (
        client.get(
            "/api/v1/projects", headers={**HEADERS, "origin": "https://evil.example"}
        ).status_code
        == 403
    )
    assert (
        client.get("/api/v1/projects", headers={**HEADERS, "host": "evil.example"}).status_code
        == 403
    )
    assert (
        client.get("/api/v1/projects", headers={**HEADERS, "authorization": TOKEN}).status_code
        == 401
    )
    response = client.post(
        "/api/v1/folder-grants", headers=HEADERS, json={"scope": "project", "path": "C:/Windows"}
    )
    assert response.status_code == 422 and "Windows" not in response.text


def test_json_budget_rejects_before_persistence(server):
    app, client = server
    response = client.post(
        "/api/v1/projects",
        headers={**HEADERS, "content-type": "application/json"},
        content=b" " * (16 * 1024**2 + 1),
    )
    assert response.status_code == 413 and app.state.store.list_projects() == []


def test_revision_dirty_and_manual_race(server, project, tmp_path):
    app, client = server
    store = app.state.store
    current = store.create(project)
    assert current["dirty"]
    save_folder = tmp_path / "Lưu tiếng Việt"
    save_folder.mkdir()
    store.save(project["id"], project, current["revision"], save_folder)
    assert not store.load(project["id"])["dirty"]
    b = copy.deepcopy(project)
    b["name"] = "B"
    working = store.update(project["id"], b, current["revision"])
    with pytest.raises(Conflict):
        store.update(project["id"], project, current["revision"])
    saved = store.save(project["id"], b, working["revision"], save_folder)
    assert not saved["dirty"]
    c = copy.deepcopy(b)
    c["name"] = "C"
    store.update(project["id"], c, working["revision"])
    envelope = parse_json((save_folder / (project["id"] + ".amvs.json")).read_bytes())
    assert envelope["project"]["name"] == "B" and store.load(project["id"])["dirty"]
    with pytest.raises(Conflict):
        store.open_manual(save_folder / (project["id"] + ".amvs.json"))


def test_failed_publish_preserves_old_manual(server, project, tmp_path, monkeypatch):
    from amvs import store as module

    store = server[0].state.store
    current = store.create(project)
    store.save(project["id"], project, current["revision"], tmp_path)
    target = tmp_path / (project["id"] + ".amvs.json")
    before = target.read_bytes()
    changed = copy.deepcopy(project)
    changed["name"] = "Mới"
    store.update(project["id"], changed, 1)

    def fail(*args):
        raise OSError("Injected replace failure")

    monkeypatch.setattr(module.os, "replace", fail)
    with pytest.raises(OSError):
        store.save(project["id"], changed, 2, tmp_path)
    assert target.read_bytes() == before and store.load(project["id"])["dirty"]


def test_bad_grant_rejected_and_deletion_preserves_library(server, project):
    app, client = server
    response = client.post("/api/v1/projects", headers=HEADERS, json=project)
    assert response.status_code == 200
    response = client.post(
        f"/api/v1/projects/{project['id']}/save",
        headers=HEADERS,
        json={"project": project, "revision": 1, "grantId": "forged"},
    )
    assert response.status_code == 403
    keep = app.state.store.root / "library/canary"
    keep.write_bytes(b"generated")
    response = client.delete(f"/api/v1/projects/{project['id']}", headers=HEADERS)
    assert response.status_code == 200 and keep.read_bytes() == b"generated"


def test_upload_probe_and_readonly_cookie(server):
    app, client = server
    response = client.post(
        "/api/v1/assets",
        headers=HEADERS,
        files={"file": ("fake.png", b"not a picture", "image/png")},
        data={"rightsConfirmed": "true"},
    )
    assert response.status_code == 422
    image = ROOT / ".local/test-assets/artwork.png"
    response = client.post(
        "/api/v1/assets",
        headers=HEADERS,
        files={"file": ("ảnh.png", image.read_bytes(), "image/png")},
        data={"rightsConfirmed": "true"},
    )
    assert response.status_code == 200, response.text
    asset = response.json()
    assert asset["kind"] == "image"
    response = client.get("/api/v1/session", headers=HEADERS)
    assert response.status_code == 200
    cookie_headers = {"host": "testserver", "origin": ORIGIN}
    assert (
        client.get(f"/api/v1/assets/{asset['id']}/content", headers=cookie_headers).status_code
        == 200
    )
    assert client.post("/api/v1/projects", headers=cookie_headers, json={}).status_code == 401
    audio = ROOT / ".local/test-assets/control.wav"
    response = client.post(
        "/api/v1/assets",
        headers=HEADERS,
        files={"file": ("nhạc.wav", audio.read_bytes(), "audio/wav")},
        data={"rightsConfirmed": "true"},
    )
    assert response.status_code == 200 and response.json()["kind"] == "audio"


def test_newer_database_version_preserved(tmp_path):
    import sqlite3

    store = Store(tmp_path)
    with store.connect() as db:
        db.execute("PRAGMA user_version=99")
    with pytest.raises(ValueError):
        Store(tmp_path)
    db = sqlite3.connect(store.path)
    assert db.execute("PRAGMA user_version").fetchone()[0] == 99
    db.close()


def test_template_and_job_contracts(project):
    template = {
        "schemaVersion": "amvs-template/1",
        "id": "my-template",
        "version": 1,
        "name": "Mẫu thử",
        "defaultProject": project,
        "slots": [{"id": "caption-slot", "itemId": "caption", "kind": "text", "required": True}],
    }
    validate_template(template)
    template["slots"][0]["kind"] = "image"
    with pytest.raises(ValueError):
        validate_template(template)
    job = {
        "schemaVersion": "amvs-job/1",
        "id": "a" * 32,
        "kind": "render",
        "projectId": "fixture-project",
        "status": "succeeded",
        "phase": "succeeded",
        "progress": 1,
        "snapshotHash": "b" * 64,
        "message": "Sẵn sàng",
    }
    validate_job(job)
    job["progress"] = 0.95
    with pytest.raises(ValueError):
        validate_job(job)


def test_queued_job_cancel_and_snapshot_isolation(tmp_path, project):
    import time

    from amvs.jobs import Jobs
    from test_assets import prepare

    store = Store(tmp_path / "workspace")
    folder = prepare()
    import shutil

    from amvs.media import probe
    from amvs.store import digest_file

    for name in ["artwork.png", "control.wav"]:
        source = folder / name
        meta = probe(source)
        id = digest_file(source)
        file = id + meta.pop("extension")
        shutil.copy2(source, store.root / "library" / file)
        store.put_asset(
            {"id": id, "file": file, "name": name, "bytes": source.stat().st_size, **meta}
        )
        kind = meta["kind"]
        project["assetRefs"].append(id)
        project["items"].append(
            {
                "id": kind,
                "trackId": "background" if kind == "image" else "music",
                "type": kind,
                "assetId": id,
                "startTicks": 0,
                "durationTicks": project["durationTicks"],
                "sourceStartTicks": 0,
                "speed": {"numerator": 1, "denominator": 1},
                "volume": 1,
            }
        )
    manager = Jobs(store, headroom=1024)  # Deliberately never admits a heavy process.
    export = tmp_path / "exports"
    export.mkdir()
    try:
        job = manager.start(project, export)
        id = job["id"]
        original = job["snapshotHash"]
        project["name"] = "Sửa khi chờ job"
        assert (
            manager.rows[id]["project"]["name"] != project["name"]
            and manager.rows[id]["snapshotHash"] == original
        )
        began = time.monotonic()
        manager.cancel(id)
        while manager.public(id)["status"] != "cancelled" and time.monotonic() - began < 5:
            time.sleep(0.05)
        assert manager.public(id)["status"] == "cancelled" and time.monotonic() - began < 5
        assert not list(export.iterdir())
    finally:
        manager.shutdown()


def test_owned_tree_cancel_preserves_unrelated_process(tmp_path, project):
    import json
    import subprocess
    import sys
    import threading
    import time

    import psutil
    from amvs.jobs import Jobs

    store = Store(tmp_path / "workspace")
    manager = Jobs(store)
    id = "c" * 32
    folder = tmp_path / "process-tree"
    folder.mkdir()
    pids = folder / "pids.json"
    manager.rows[id] = {
        "schemaVersion": "amvs-job/1",
        "id": id,
        "kind": "render",
        "projectId": project["id"],
        "status": "running",
        "phase": "running",
        "progress": 0,
        "snapshotHash": content_hash(project),
        "message": "Test",
    }
    result = []

    def command():
        try:
            manager.command(
                id,
                [sys.executable, str(ROOT / "tests/fixtures/owned_process.py"), str(pids)],
                folder,
                "cancel-test",
            )
        except InterruptedError:
            result.append("cancelled")

    unrelated = subprocess.Popen([sys.executable, "-c", "import time;time.sleep(120)"])
    worker = threading.Thread(target=command)
    try:
        worker.start()
        deadline = time.monotonic() + 10
        while not pids.exists() and time.monotonic() < deadline:
            time.sleep(0.05)
        assert pids.exists()
        known = json.loads(pids.read_text())
        began = time.monotonic()
        manager.cancel(id)
        worker.join(timeout=10)
        assert not worker.is_alive() and result == ["cancelled"] and time.monotonic() - began < 10
        assert all(not psutil.pid_exists(pid) for pid in known.values())
        assert unrelated.poll() is None
    finally:
        manager.stopping = True
        worker.join(timeout=10)
        manager.shutdown()
        if unrelated.poll() is None:
            root = psutil.Process(unrelated.pid)
            children = root.children(recursive=True)
            for process in [*reversed(children), root]:
                try:
                    process.kill()
                except psutil.NoSuchProcess:
                    pass
            unrelated.wait(timeout=10)
