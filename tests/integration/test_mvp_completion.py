import copy
import json
import shutil
import sys
import time
import zipfile
from pathlib import Path

import pytest
from amvs.app import create_app
from amvs.catalog import Catalog
from amvs.domain import content_hash, validate_job
from amvs.media import probe
from amvs.snapshots import Snapshots
from amvs.store import Conflict, Store, digest_file
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
TOKEN = "s2-s6-test-session-" + "x" * 48
ORIGIN = "http://127.0.0.1:3000"
HEADERS = {"host": "testserver", "origin": ORIGIN, "authorization": "Bearer " + TOKEN}


@pytest.fixture
def setup(tmp_path):
    store = Store(tmp_path / "workspace")
    p = json.loads((ROOT / "tests/fixtures/project.json").read_text(encoding="utf-8"))
    p["durationTicks"] = 48000 * 3
    for i in p["items"]:
        i["durationTicks"] = min(i["durationTicks"], p["durationTicks"])
    for filename in ("artwork.png", "control.wav"):
        source = ROOT / ".local/test-assets" / filename
        metadata = probe(source)
        ext = metadata.pop("extension")
        key = digest_file(source)
        shutil.copyfile(source, store.root / "library" / (key + ext))
        asset = {
            "id": key,
            "file": key + ext,
            "name": filename,
            "bytes": source.stat().st_size,
            **metadata,
        }
        store.put_asset(asset)
        p["assetRefs"].append(key)
        p["items"].append(
            {
                "id": filename.replace(".", "-"),
                "trackId": "music" if asset["kind"] == "audio" else "background",
                "type": asset["kind"],
                "assetId": key,
                "startTicks": 0,
                "durationTicks": 48000 * 3,
                "sourceStartTicks": 0,
                "speed": {"numerator": 1, "denominator": 1},
                "volume": 1,
            }
        )
    store.create(p)
    return store, p


def test_recovery_separate_manual_hash_revision_and_corruption(setup, tmp_path):
    store, p = setup
    s = Snapshots(store)
    manual = tmp_path / "manual"
    manual.mkdir()
    store.save(p["id"], p, 1, manual)
    assert not s.capture(p["id"])["created"]
    changed = copy.deepcopy(p)
    changed["name"] = "Bản làm việc"
    store.update(p["id"], changed, 1)
    assert s.capture(p["id"])["created"]
    assert not s.capture(p["id"])["created"]
    recovery = s.list(p["id"])[0]
    original = (manual / (p["id"] + ".amvs.json")).read_bytes()
    newer = {**changed, "name": "Mới hơn"}
    store.update(p["id"], newer, 2)
    with pytest.raises(Conflict):
        s.restore(p["id"], recovery["id"], 2)
    restored = s.restore(p["id"], recovery["id"], 3)
    assert restored["project"]["name"] == "Bản làm việc" and restored["dirty"]
    assert restored["manualSavedHash"] == content_hash(p)
    assert (manual / (p["id"] + ".amvs.json")).read_bytes() == original
    path = s.directory(p["id"]) / (recovery["id"] + ".json")
    data = json.loads(path.read_bytes())
    data["project"]["name"] = "corrupt"
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        s.restore(p["id"], recovery["id"], 4)
    assert store.load(p["id"])["revision"] == 4


def test_recovery_cap_pauses_without_deleting_user_history(setup):
    store, p = setup
    s = Snapshots(store)
    for index in range(10):
        row = store.load(p["id"])
        store.update(p["id"], {**p, "name": str(index)}, row["revision"])
        assert s.capture(p["id"])["created"]
    row = store.load(p["id"])
    store.update(p["id"], p, row["revision"])
    result = s.capture(p["id"])
    assert not result["created"] and result["warning"]
    assert len(s.list(p["id"])) == 10
    with pytest.raises(ValueError):
        s.clear(p["id"], ["../../manual"])


def test_portable_cross_workspace_real_bytes_no_overwrite(setup, tmp_path):
    store, p = setup
    s = Snapshots(store)
    out = tmp_path / "out"
    out.mkdir()
    packaged = s.export(p["id"], 1, out)
    path = out / packaged["name"]
    before = path.read_bytes()
    other = Store(tmp_path / "máy khác")
    restored = Snapshots(other).import_package(path)
    assert restored["project"] == p and restored["dirty"]
    assert restored["manualSavedHash"] == store.load(p["id"])["manualSavedHash"]
    for key in p["assetRefs"]:
        assert digest_file(other.asset_path(other.assets()[key])) == key
    with pytest.raises(Conflict):
        Snapshots(other).import_package(path)
    assert path.read_bytes() == before
    with pytest.raises(Conflict):
        s.export(p["id"], 0, out)


@pytest.mark.parametrize(
    "attack",
    [
        "traversal",
        "duplicate",
        "checksum",
        "metadata",
        "missing",
        "version",
        "view-null",
        "view-budget",
    ],
)
def test_portable_rejects_untrusted_archive_before_project_publish(setup, tmp_path, attack):
    store, p = setup
    s = Snapshots(store)
    out = tmp_path / "out"
    out.mkdir()
    result = s.export(p["id"], 1, out)
    source = out / result["name"]
    bad = out / (attack + ".amvs")
    with zipfile.ZipFile(source) as archive:
        entries = {name: archive.read(name) for name in archive.namelist()}
    envelope = json.loads(entries["manifest.json"])
    key = p["assetRefs"][0]
    if attack == "view-null":
        envelope["view"] = None
    if attack == "view-budget":
        envelope["view"] = {"extra": "x" * 65536}
    if attack == "checksum":
        envelope["contentHash"] = "0" * 64
    if attack == "metadata":
        envelope["assets"][key]["kind"] = "audio"
    if attack == "version":
        project = json.loads(entries["project.json"])
        project["schemaVersion"] = "amvs-project/99"
        entries["project.json"] = json.dumps(project).encode()
    if attack == "missing":
        entries.pop("assets/" + envelope["assets"][key]["file"])
    entries["manifest.json"] = json.dumps(envelope).encode()
    with zipfile.ZipFile(bad, "w") as archive:
        for name, data in entries.items():
            archive.writestr(name, data)
        if attack == "traversal":
            archive.writestr("../escape", b"no")
        if attack == "duplicate":
            archive.writestr("project.json", entries["project.json"])
    other = Store(tmp_path / "other")
    with pytest.raises((ValueError, KeyError)):
        Snapshots(other).import_package(bad)
    assert other.list_projects() == [] and not (tmp_path / "escape").exists()


def test_template_bindings_are_typed_and_instance_edits_preserve_template(setup):
    store, p = setup
    catalog = Catalog(store)
    template = catalog.save_template(p, "Mẫu Việt", [p["items"][0]["id"], p["items"][1]["id"]])
    before = copy.deepcopy(template)
    bindings = {
        s["id"]: ("Chữ mới" if s["kind"] == "text" else p["items"][1]["assetId"])
        for s in template["slots"]
    }
    new = catalog.instantiate(template["id"], bindings)
    assert new["project"]["id"] != p["id"] and new["project"]["items"][0]["text"] == "Chữ mới"
    store.update(new["project"]["id"], {**new["project"], "name": "Sửa instance"}, 1)
    assert catalog.templates()[0] == before and store.load(p["id"])["project"] == p
    with pytest.raises(ValueError):
        catalog.instantiate(template["id"], {})
    image_slot = next(s for s in template["slots"] if s["kind"] == "image")
    bad = {**bindings, image_slot["id"]: p["items"][2]["assetId"]}
    with pytest.raises(ValueError):
        catalog.instantiate(template["id"], bad)


def test_thumbnail_and_tags_use_catalog_ids(setup):
    store, p = setup
    catalog = Catalog(store)
    key = p["assetRefs"][0]
    thumb = catalog.thumbnail(key)
    assert thumb.read_bytes().startswith(b"\xff\xd8")
    assert catalog.tags(key, [" Việt ", "Việt"])["tags"] == ["Việt"]
    with pytest.raises(ValueError):
        catalog.tags(key, ["x" * 51])
    assert digest_file(store.asset_path(store.assets()[key])) == key


def test_new_routes_auth_consent_and_stale_revision(setup, tmp_path, monkeypatch):
    model = tmp_path / "models/faster-whisper-small"
    model.mkdir(parents=True)
    (model / "model.bin").write_bytes(b"admission-only-fixture-never-inferred")
    monkeypatch.setenv("AMVS_ASR_PYTHON", sys.executable)
    monkeypatch.setenv("AMVS_MODEL_ROOT", str(tmp_path / "models"))
    store, p = setup
    app = create_app(store.root, TOKEN, ORIGIN, "testserver", headroom=999)
    with TestClient(app) as client:
        assert client.get("/api/v1/ai/providers", headers=HEADERS).json()["cloudEgress"] is False
        assert (
            client.post(
                f"/api/v1/projects/{p['id']}/restore", headers=HEADERS, json={"confirmed": False}
            ).status_code
            == 422
        )
        assert (
            client.post(
                "/api/v1/templates",
                headers=HEADERS,
                json={"projectId": p["id"], "revision": 0, "name": "Mẫu", "itemIds": ["caption"]},
            ).status_code
            == 409
        )
        assert (
            client.get(
                "/api/v1/templates", headers={"host": "testserver", "origin": ORIGIN}
            ).status_code
            == 401
        )
        audio = next(i for i in p["items"] if i["type"] == "audio")
        response = client.post(
            "/api/v1/lyrics/jobs",
            headers=HEADERS,
            json={
                "projectId": p["id"],
                "revision": 1,
                "audioItemId": audio["id"],
                "language": "vi",
                "model": "small",
            },
        )
        assert response.status_code == 202
        job = response.json()
        validate_job(job)
        assert "asr" not in job and "modelPath" not in response.text
        client.post(f"/api/v1/jobs/{job['id']}/cancel", headers=HEADERS, json={})
        for _ in range(30):
            state = client.get(f"/api/v1/jobs/{job['id']}", headers=HEADERS).json()
            if state["status"] == "cancelled":
                break
            time.sleep(0.1)
        assert state["status"] == "cancelled" and store.load(p["id"])["project"] == p


def test_package_background_job_snapshot_and_temp_cleanup_preserve_outputs(setup, tmp_path):
    store, p = setup
    app = create_app(store.root, TOKEN, ORIGIN, "testserver", headroom=999)
    folder = tmp_path / "backup"
    folder.mkdir()
    app.state.grants["backup"] = {"scope": "backup", "path": folder}
    with TestClient(app) as client:
        response = client.post(
            f"/api/v1/projects/{p['id']}/packages",
            headers=HEADERS,
            json={"revision": 1, "grantId": "backup"},
        )
        assert response.status_code == 202
        job = response.json()
        validate_job(job)
        store.update(p["id"], {**p, "name": "Edited after snapshot"}, 1)
        for _ in range(100):
            state = client.get(f"/api/v1/jobs/{job['id']}", headers=HEADERS).json()
            if state["status"] in {"succeeded", "failed"}:
                break
            time.sleep(0.05)
        assert state["status"] == "succeeded"
        result = client.get(f"/api/v1/jobs/{job['id']}/package", headers=HEADERS).json()
        with zipfile.ZipFile(folder / result["name"]) as archive:
            assert json.loads(archive.read("project.json"))["name"] == p["name"]
            assert set(archive.namelist()) == {
                "manifest.json",
                "project.json",
                *("assets/" + a["file"] for a in store.assets().values()),
            }
        owned = store.root / "jobs" / job["id"]
        (owned / "public").mkdir()
        (owned / "public" / "copy.bin").write_bytes(b"temp")
        outside = tmp_path / "keep.mp4"
        outside.write_bytes(b"published-output")
        assert client.get(f"/api/v1/outputs/{job['id']}", headers=HEADERS).status_code == 422
        preview = client.get("/api/v1/storage/temp", headers=HEADERS).json()["jobs"]
        assert preview[0]["id"] == job["id"]
        assert (
            client.post(
                "/api/v1/storage/temp/cleanup",
                headers=HEADERS,
                json={"ids": [job["id"]], "confirmed": False},
            ).status_code
            == 422
        )
        assert (
            client.post(
                "/api/v1/storage/temp/cleanup",
                headers=HEADERS,
                json={"ids": ["../../escape"], "confirmed": True},
            ).status_code
            == 422
        )
        assert (
            client.post(
                "/api/v1/storage/temp/cleanup",
                headers=HEADERS,
                json={"ids": [job["id"]], "confirmed": True},
            ).status_code
            == 200
        )
        assert not (owned / "public").exists() and outside.read_bytes() == b"published-output"
        assert (folder / result["name"]).is_file()
        for key in p["assetRefs"]:
            assert store.asset_path(store.assets()[key]).is_file()


def test_missing_model_and_bad_input_do_not_mutate_working_project(setup, tmp_path, monkeypatch):
    store, p = setup
    monkeypatch.setenv("AMVS_MODEL_ROOT", str(tmp_path / "missing-models"))
    app = create_app(store.root, TOKEN, ORIGIN, "testserver", headroom=999)
    with TestClient(app) as client:
        before = store.load(p["id"])
        audio = next(i for i in p["items"] if i["type"] == "audio")
        response = client.post(
            "/api/v1/lyrics/jobs",
            headers=HEADERS,
            json={
                "projectId": p["id"],
                "revision": 1,
                "audioItemId": audio["id"],
                "language": "vi",
                "model": "small",
            },
        )
        assert response.status_code == 422 and store.load(p["id"]) == before
        assert client.post("/api/v1/templates", headers=HEADERS, json=[]).status_code == 422
        assert (
            client.post(
                "/api/v1/lyrics/jobs",
                headers={**HEADERS, "origin": "https://outside.example"},
                json={},
            ).status_code
            == 403
        )
        assert (
            client.post(
                f"/api/v1/assets/{audio['assetId']}/relink",
                headers=HEADERS,
                json={"confirmed": True, "path": "C:/private"},
            ).status_code
            == 422
        )
        assert store.load(p["id"]) == before


def test_drive_template_roundtrip_transport_and_offline_preserve_local(setup, tmp_path):
    # This exercises real backup/restore code with an in-memory Google transport.
    # It does not claim cloud-account, quota, cross-PC or long-run verification.
    import hashlib
    import threading

    import httpx
    from amvs.drive import API, DriveError
    from amvs.drive_backup import DriveBackup
    from amvs.drive_restore import DriveRestore

    store, p = setup
    template = Catalog(store).save_template(p, "Mẫu backup", ["caption"])
    payloads = {}
    metadata = {}
    uploads = []

    class TransportDrive:
        data = {"folder": "fixture-root"}
        lock = threading.RLock()
        fail = False

        def status(self):
            return {
                "connected": True,
                "pending": False,
                "autoSync": False,
                "lastBackup": self.data.get("lastBackup"),
            }

        def child_folder(self, _, name):
            return "folder-" + name

        def persist(self):
            pass

        def auth(self):
            return {"Authorization": "Bearer fixture"}

        def upload(self, path, parent, name, mime):
            if self.fail:
                raise DriveError("transport offline fixture")
            body = path.read_bytes()
            key = "file-" + str(len(payloads))
            payloads[key] = body
            uploads.append((parent, name))
            md5 = hashlib.md5(body).hexdigest()
            metadata[key] = {
                "id": key,
                "parents": [parent],
                "size": str(len(body)),
                "md5Checksum": md5,
            }
            return {"fileId": key, "bytes": len(body), "md5": md5}

        def request(self, method, url, **kwargs):
            if self.fail:
                raise DriveError("transport offline fixture")
            assert method == "GET" and url.startswith(API + "/")
            return httpx.Response(200, json=metadata[url.rsplit("/", 1)[-1]])

        def download(self, id, target, size, md5, expected_sha256=None):
            body = payloads[id]
            assert len(body) == size and hashlib.md5(body).hexdigest() == md5
            if expected_sha256:
                assert hashlib.sha256(body).hexdigest() == expected_sha256
            with target.open("xb") as file:
                file.write(body)

    drive = TransportDrive()
    backup = DriveBackup(drive, store)
    store.put_job({"id": "a" * 32, "kind": "asr", "status": "succeeded"})
    backup.copy()
    first = copy.deepcopy(drive.data["lastBackup"])
    manifest = json.loads(payloads[first["manifestId"]])
    assert len(manifest["templates"]) == 1 and not manifest["exports"]
    backup.copy()
    second = copy.deepcopy(drive.data["lastBackup"])
    next_manifest = json.loads(payloads[second["manifestId"]])
    assert [a["fileId"] for a in manifest["assets"].values()] == [
        a["fileId"] for a in next_manifest["assets"].values()
    ]
    other = Store(tmp_path / "restored-drive")
    restore = DriveRestore(drive, other)
    descriptor = {
        "id": second["manifestId"],
        "bytes": len(payloads[second["manifestId"]]),
        "md5": metadata[second["manifestId"]]["md5Checksum"],
    }
    assert restore.restore(descriptor) == 1
    assert Catalog(other).templates() == [template] and other.load(p["id"])["project"] == p
    for key in p["assetRefs"]:
        assert digest_file(other.asset_path(other.assets()[key])) == key
    before = store.load(p["id"])
    drive.fail = True
    backup.run()
    assert (
        backup.status()["status"] == "failed"
        and drive.data["lastBackup"] == second
        and store.load(p["id"]) == before
    )


def test_abrupt_owned_process_exit_leaves_recovery_and_manual_independent(setup, tmp_path):
    import subprocess

    store, p = setup
    manual = tmp_path / "manual"
    manual.mkdir()
    store.save(p["id"], p, 1, manual)
    marker = tmp_path / "ready"
    child = subprocess.Popen(
        [
            sys.executable,
            str(ROOT / "tests/fixtures/recovery_process.py"),
            str(store.root),
            p["id"],
            str(marker),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    try:
        for _ in range(100):
            if marker.exists():
                break
            if child.poll() is not None:
                raise AssertionError("Crash fixture exited before publishing")
            time.sleep(0.05)
        assert marker.exists()
        child.kill()
        child.wait(timeout=10)
        reopened = Store(store.root)
        snapshots = Snapshots(reopened)
        rows = snapshots.list(p["id"])
        assert len(rows) == 1
        current = reopened.load(p["id"])
        assert current["project"]["name"] == "Bản trước crash"
        restored = snapshots.restore(p["id"], rows[0]["id"], current["revision"])
        assert restored["dirty"] and restored["manualSavedHash"] == content_hash(p)
        envelope = json.loads((manual / (p["id"] + ".amvs.json")).read_bytes())
        assert envelope["project"] == p
    finally:
        if child.poll() is None:
            child.kill()
            child.wait(timeout=10)
        if child.stderr:
            child.stderr.close()


def test_disabled_cloud_provider_never_egresses_and_preserves_project(setup, monkeypatch):
    import httpx

    original_request = httpx.Client.request

    def forbidden(self, *args, **kwargs):
        if isinstance(self, TestClient):
            return original_request(self, *args, **kwargs)
        raise AssertionError("Cloud AI egress")

    monkeypatch.setattr(httpx.Client, "request", forbidden)
    store, p = setup
    app = create_app(store.root, TOKEN, ORIGIN, "testserver", headroom=999)
    with TestClient(app) as client:
        before = store.load(p["id"])
        audio = next(i for i in p["items"] if i["type"] == "audio")
        for provider in ("gemini", "openai"):
            response = client.post(
                "/api/v1/lyrics/jobs",
                headers=HEADERS,
                json={
                    "projectId": p["id"],
                    "revision": 1,
                    "audioItemId": audio["id"],
                    "language": "vi",
                    "model": "small",
                    "provider": provider,
                },
            )
            assert response.status_code == 422 and response.json()["code"] == "AI_UNAVAILABLE"
        assert store.load(p["id"]) == before


def test_editor_lease_blocks_stale_tabs_allows_explicit_takeover_and_expires(setup):
    from amvs.edit_leases import EditLeases

    store, p = setup
    app = create_app(store.root, TOKEN, ORIGIN, "testserver", headroom=999)
    a = {**HEADERS, "x-amvs-editor": "editor-a-" + "a" * 24}
    b = {**HEADERS, "x-amvs-editor": "editor-b-" + "b" * 24}
    url = f"/api/v1/projects/{p['id']}"
    with TestClient(app) as client:
        assert client.post(url + "/editor-session", headers=a, json={"takeover": False}).json()[
            "canWrite"
        ]
        assert not client.post(url + "/editor-session", headers=b, json={"takeover": False}).json()[
            "canWrite"
        ]
        assert client.patch(url, headers=b, json={"project": p, "revision": 1}).status_code == 409
        assert client.post(url + "/editor-session", headers=b, json={"takeover": True}).json()[
            "canWrite"
        ]
        assert client.patch(url, headers=a, json={"project": p, "revision": 1}).status_code == 409
        assert not client.delete(url + "/editor-session", headers=a).json()["released"]
        assert (
            client.request(
                "DELETE", url + "/recoveries", headers=a, json={"ids": [], "confirmed": True}
            ).status_code
            == 409
        )
        assert client.patch(url, headers=b, json={"project": p, "revision": 1}).status_code == 200
        assert client.delete(url + "/editor-session", headers=b).json()["released"]
        assert client.post(url + "/editor-session", headers=a, json={"takeover": False}).json()[
            "canWrite"
        ]
    now = [0.0]
    leases = EditLeases(clock=lambda: now[0])
    assert leases.claim("p", "a" * 32)["canWrite"]
    now[0] = 31
    with pytest.raises(Conflict):
        with leases.guard("p", "a" * 32):
            pass
    assert leases.claim("p", "b" * 32)["canWrite"]


def test_source_gc_rechecks_history_pin_and_never_removes_shared_source(setup):
    from amvs.source_gc import SourceGC

    store, p = setup
    assert SourceGC(store).preview()["candidates"] == []
    with store.connect() as db:
        db.execute("DELETE FROM projects")
    reopened = Store(store.root)
    gc = SourceGC(reopened)
    candidates = gc.preview()["candidates"]
    assert len(candidates) == 2
    first, second = [r["id"] for r in candidates]
    reopened.pin_assets([first])
    with pytest.raises(ValueError):
        gc.collect([first, second])
    assert all(reopened.asset_path(reopened.assets()[key]).exists() for key in (first, second))
    before = reopened.asset_path(reopened.assets()[first]).read_bytes()
    result = gc.collect([second])
    assert (
        result["deleted"] == [second]
        and first in reopened.assets()
        and second not in reopened.assets()
    )
    assert reopened.asset_path(reopened.assets()[first]).read_bytes() == before
    with pytest.raises(ValueError):
        gc.collect(["../../outside"])


@pytest.mark.parametrize("pin", ["manual", "recovery", "job", "template", "legacy"])
def test_source_gc_pins_survive_restart_and_project_removal(setup, tmp_path, pin):
    from amvs.source_gc import SourceGC

    store, p = setup
    if pin == "manual":
        folder = tmp_path / "manual"
        folder.mkdir()
        store.save(p["id"], p, 1, folder)
    if pin == "recovery":
        Snapshots(store).capture(p["id"])
    if pin == "job":
        store.put_job({"id": "b" * 32, "status": "succeeded", "kind": "render", "project": p})
    if pin == "template":
        Catalog(store).save_template(p, "Mẫu pin", ["caption"])
    with store.connect() as db:
        db.execute("DELETE FROM projects")
        if pin == "legacy":
            db.execute("DROP TABLE asset_pins")
    reopened = Store(store.root)
    assert SourceGC(reopened).preview()["candidates"] == []
    for key in p["assetRefs"]:
        assert reopened.asset_path(reopened.assets()[key]).exists()


def test_source_gc_locked_file_restores_catalog_and_keeps_bytes(setup, monkeypatch):
    from amvs.source_gc import SourceGC

    store, p = setup
    with store.connect() as db:
        db.execute("DELETE FROM projects")
    reopened = Store(store.root)
    key = p["assetRefs"][0]
    target = reopened.asset_path(reopened.assets()[key])
    original_unlink = Path.unlink

    def blocked(self, *args, **kwargs):
        if self == target:
            raise PermissionError("injected Windows file lock")
        return original_unlink(self, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", blocked)
    result = SourceGC(reopened).collect([key])
    assert result["failed"] == [key] and not result["deleted"]
    assert key in reopened.assets() and digest_file(target) == key


def test_cache_quota_configuration_and_cleanup_never_delete_sources(setup, monkeypatch):
    from amvs.storage_policy import StoragePolicy, StorageQuota

    store, p = setup
    policy = StoragePolicy(store)
    policy.configure({"cacheQuotaMiB": 32, "reserveGiB": 2})
    assert StoragePolicy(store).read() == {"cacheQuotaMiB": 32, "reserveGiB": 2}
    with pytest.raises(ValueError):
        policy.configure({"cacheQuotaMiB": -1, "reserveGiB": 2})
    folder = store.root / "cache/thumbnails"
    folder.mkdir(parents=True)
    large = folder / ("d" * 64 + ".jpg")
    with large.open("wb") as file:
        file.truncate(33 * 1024**2)
    (folder / "keep.json").write_bytes(b"not-a-managed-thumbnail")
    with pytest.raises(StorageQuota):
        policy.check_cache(1)
    assert policy.clear_cache()["deleted"] == 1 and (folder / "keep.json").exists()
    for key in p["assetRefs"]:
        assert digest_file(store.asset_path(store.assets()[key])) == key
    import shutil

    usage = shutil.disk_usage(store.root)
    monkeypatch.setattr(shutil, "disk_usage", lambda _: type(usage)(usage.total, usage.total, 0))
    with pytest.raises(StorageQuota):
        policy.check_cache(100)


@pytest.mark.parametrize("edited_after_save", [False, True])
def test_portable_preserves_original_manual_saved_hash(setup, tmp_path, edited_after_save):
    store, p = setup
    manual = tmp_path / "manual"
    manual.mkdir()
    store.save(p["id"], p, 1, manual)
    revision = 1
    if edited_after_save:
        store.update(p["id"], {**p, "name": "Unconfirmed working edit"}, 1)
        revision = 2
    out = tmp_path / "portable"
    out.mkdir()
    result = Snapshots(store).export(p["id"], revision, out)
    other = Store(tmp_path / "destination")
    row = Snapshots(other).import_package(out / result["name"])
    assert row["manualSavedHash"] == content_hash(p) and row["dirty"] is edited_after_save
    assert row["contentHash"] == store.load(p["id"])["contentHash"]


def test_lyrics_template_requires_approved_timeline_cues_before_render(setup, tmp_path):
    store, p = setup
    p = {**p, "templateRef": {"id": "TPL-03", "version": 1}}
    store.update(p["id"], p, 1)
    app = create_app(store.root, TOKEN, ORIGIN, "testserver", headroom=999)
    folder = tmp_path / "output"
    folder.mkdir()
    app.state.grants["export"] = {"scope": "export", "path": folder}
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/jobs",
            headers=HEADERS,
            json={"projectId": p["id"], "revision": 2, "grantId": "export"},
        )
        assert (
            response.status_code == 422
            and response.json()["code"] == "RENDER_INPUT"
            and not app.state.jobs.rows
        )
        assert store.load(p["id"])["project"] == p


def test_resource_monitor_discovers_only_disposable_run_and_stops(tmp_path):
    import os
    import subprocess
    import uuid

    folder = ROOT / ".local/e2e" / ("monitor-" + uuid.uuid4().hex)
    folder.mkdir(parents=True)
    child = subprocess.Popen(
        [
            sys.executable,
            str(ROOT / "scripts/monitor_e2e_resources.py"),
            str(folder),
            str(os.getpid()),
        ],
        env={**os.environ, "AMVS_TEST_RUN": str(folder)},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    try:
        path = folder / "application-resources.jsonl"
        for _ in range(100):
            if path.exists() and len(path.read_text().splitlines()) >= 3:
                break
            if child.poll() is not None:
                raise AssertionError("Owned monitor exited early")
            time.sleep(0.1)
        (folder / "resource-monitor.stop").write_text("stop")
        assert child.wait(timeout=10) == 0
        summary = json.loads((folder / "application-resources-summary.json").read_text())
        assert (
            summary["samples"] >= 3
            and summary["peakPrivateBytes"] > 0
            and summary["minimumAvailableBytes"] > 0
        )
    finally:
        if child.poll() is None:
            child.kill()
            child.wait(timeout=10)
        if child.stderr:
            child.stderr.close()


def test_energy_suggestions_decode_real_audio_without_numpy_or_project_edits(setup, tmp_path):
    import math
    import struct
    import wave

    store, p = setup
    source = tmp_path / "energy.wav"
    rate = 8000
    with wave.open(str(source), "wb") as file:
        file.setparams((1, 2, rate, 0, "NONE", "not compressed"))
        for second in range(18):
            amplitude = 1500 if second < 6 else 12000 if second < 12 else 5000
            file.writeframes(
                b"".join(
                    struct.pack("<h", round(amplitude * math.sin(2 * math.pi * 440 * n / rate)))
                    for n in range(rate)
                )
            )
    key = digest_file(source)
    metadata = probe(source)
    extension = metadata.pop("extension")
    target = store.root / "library" / (key + extension)
    shutil.copyfile(source, target)
    store.put_asset(
        {
            "id": key,
            "file": target.name,
            "name": "Energy fixture",
            "bytes": target.stat().st_size,
            **metadata,
        }
    )
    before = store.load(p["id"])
    result = Catalog(store).suggestions(key)
    assert result["method"] == "local-energy-v1" and len(result["segments"]) >= 2
    assert 4 * 48000 <= result["segments"][0]["startTicks"] <= 8 * 48000
    assert all(s["startTicks"] + s["durationTicks"] <= 18 * 48000 for s in result["segments"])
    assert store.load(p["id"]) == before and digest_file(target) == key


@pytest.mark.parametrize("fault", ["cancel", "fsync"])
def test_publish_fault_discards_owned_stage_preserves_source(setup, tmp_path, monkeypatch, fault):
    from amvs.jobs import Jobs

    store, p = setup
    manager = Jobs(store)
    output = tmp_path / "output"
    output.mkdir()
    source = tmp_path / "validated.mp4"
    source.write_bytes(b"generated-test-media" * 100000)
    expected = digest_file(source)
    target = output / "result.mp4"
    before = store.load(p["id"])
    try:
        if fault == "cancel":
            calls = []

            def check(_):
                calls.append(True)
                if len(calls) > 1:
                    raise InterruptedError("cancelled")

            monkeypatch.setattr(manager, "check", check)
            failure = InterruptedError
        else:

            def fail(_):
                raise OSError("injected fsync fault")

            monkeypatch.setattr("amvs.jobs.os.fsync", fail)
            failure = OSError
        with pytest.raises(failure):
            manager.publish_file("test", source, target, output)
        assert not list(output.iterdir())
        assert digest_file(source) == expected
        assert store.load(p["id"]) == before
    finally:
        manager.shutdown()


def test_queued_manual_save_rechecks_owner_after_takeover(setup, tmp_path, monkeypatch):
    import asyncio

    store, p = setup
    app = create_app(store.root, TOKEN, ORIGIN, "testserver", headroom=999)
    app.state.grants["test-project"] = {"scope": "project", "path": tmp_path}
    a = {**HEADERS, "x-amvs-editor": "editor-a-" + "a" * 24}
    b = {**HEADERS, "x-amvs-editor": "editor-b-" + "b" * 24}
    url = f"/api/v1/projects/{p['id']}"
    original = asyncio.to_thread
    queued = []
    with TestClient(app) as client:
        client.post(url + "/editor-session", headers=a, json={"takeover": False}).raise_for_status()

        async def delayed(function, *args, **kwargs):
            if function.__name__ in {"save", "save_owned"}:
                queued.append(True)
                response = await original(
                    client.post, url + "/editor-session", headers=b, json={"takeover": True}
                )
                assert response.json()["canWrite"]
            return await original(function, *args, **kwargs)

        monkeypatch.setattr("amvs.app.asyncio.to_thread", delayed)
        response = client.post(
            url + "/save",
            headers=a,
            json={"project": p, "revision": 1, "grantId": "test-project"},
        )
        assert queued and response.status_code == 409
        assert not list(tmp_path.glob("*.amvs.json"))
        assert store.load(p["id"])["manualSavedHash"] is None
