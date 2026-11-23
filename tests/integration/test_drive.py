"""Protocol tests use a fake Google transport, not real cloud validation."""

import hashlib
import json
import os
import time
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import httpx
import pytest
from amvs.app import create_app
from amvs.drive import FOLDER, SCOPE, Drive, DriveError, folder_id, protect
from amvs.drive_backup import DriveBackup
from amvs.store import Store
from fastapi.testclient import TestClient

CLIENT = {
    "installed": {
        "client_id": "test-client.apps.googleusercontent.com",
        "client_secret": "fixture-secret",
    }
}
FOLDER_ID = "fixture_folder_12345"


def make_drive(tmp_path, handler):
    store = Store(tmp_path / "workspace")
    drive = Drive(store.root, httpx.MockTransport(handler))
    drive.configure(CLIENT, FOLDER_ID)
    return drive, store


def tokens():
    return {
        "access_token": "fixture-access",
        "refresh_token": "fixture-refresh",
        "expires_in": 3600,
        "token_type": "Bearer",
        "scope": SCOPE,
    }


@pytest.mark.skipif(os.name != "nt", reason="DPAPI is Windows-only by design")
def test_dpapi_roundtrip_no_plaintext(tmp_path):
    secret = b"private-refresh-fixture"
    encrypted = protect(secret)
    assert secret not in encrypted and protect(encrypted, decrypt=True) == secret
    drive, _ = make_drive(tmp_path, lambda _: httpx.Response(500))
    assert b"fixture-secret" not in drive.path.read_bytes()
    restored = Drive(drive.path.parents[1])
    assert restored.status()["configured"]
    assert "client_secret" not in json.dumps(restored.status())
    restored.close()
    drive.close()


def test_folder_url_validation():
    assert folder_id(f"https://drive.google.com/drive/folders/{FOLDER_ID}?usp=sharing") == FOLDER_ID
    for value in (
        "../secret",
        "https://evil.example/folders/123",
        "https://drive.google.com/open?id=abc",
    ):
        with pytest.raises(ValueError):
            folder_id(value)


@pytest.mark.skipif(os.name != "nt", reason="DPAPI")
def test_oauth_pkce_selection_replay_and_safe_status(tmp_path):
    calls = []

    def google(request):
        calls.append(request)
        if request.url.path == "/token":
            assert parse_qs(request.content.decode())["grant_type"] == ["authorization_code"]
            return httpx.Response(200, json=tokens())
        return httpx.Response(
            200,
            json={
                "id": FOLDER_ID,
                "name": "Kho thử",
                "mimeType": FOLDER,
                "capabilities": {"canAddChildren": True},
            },
        )

    drive, _ = make_drive(tmp_path, google)
    try:
        url = drive.begin()["url"]
        params = parse_qs(urlparse(url).query)
        assert params["scope"] == [SCOPE] and params["code_challenge_method"] == ["S256"]
        assert params["trigger_onepick"] == ["true"]
        assert params["allow_folder_selection"] == ["true"]
        assert params["file_ids"] == [FOLDER_ID]
        assert "fixture-secret" not in url
        with pytest.raises(DriveError):
            drive.complete({"state": ["forged"]})
        assert not calls  # Invalid state cannot exchange a code.
        query = {"state": params["state"], "code": ["fixture-code"], "picked_file_ids": [FOLDER_ID]}
        drive.complete(query)
        assert drive.status()["connected"]
        with pytest.raises(DriveError):
            drive.complete(query)
        assert "fixture-access" not in json.dumps(drive.status())
        drive.disconnect()
        assert not drive.status()["connected"]
        restored = Drive(drive.path.parents[1])
        assert not restored.status()["connected"]
        restored.close()
    finally:
        drive.close()


@pytest.mark.skipif(os.name != "nt", reason="DPAPI")
def test_wrong_folder_and_broad_scope_rejected(tmp_path):
    drive, _ = make_drive(tmp_path, lambda _: httpx.Response(500))
    try:
        params = parse_qs(urlparse(drive.begin()["url"]).query)
        with pytest.raises(DriveError):
            drive.complete(
                {"state": params["state"], "code": ["unused"], "picked_file_ids": ["wrong"]}
            )
        assert not drive.status()["connected"] and not drive.status()["pending"]
        with pytest.raises(DriveError):
            Drive.check_tokens({**tokens(), "scope": "https://www.googleapis.com/auth/drive"})
    finally:
        drive.close()


@pytest.mark.skipif(os.name != "nt", reason="DPAPI")
@pytest.mark.parametrize(
    "bad_checksum,evil_location", [(False, False), (True, False), (False, True)]
)
def test_resumable_upload_is_bounded_and_checks_remote_hash(tmp_path, bad_checksum, evil_location):
    payload = b"media-data" * (1024 * 1024)
    uploaded = bytearray()

    def google(request):
        if request.method == "POST":
            return httpx.Response(
                200,
                headers={
                    "location": "https://evil.example/upload"
                    if evil_location
                    else "https://www.googleapis.com/upload/drive/v3/files?upload_id=fixture"
                },
            )
        assert request.url.host == "www.googleapis.com"
        assert len(request.content) <= 8 * 1024**2
        uploaded.extend(request.content)
        if len(uploaded) < len(payload):
            return httpx.Response(308, headers={"range": f"bytes=0-{len(uploaded) - 1}"})
        return httpx.Response(
            200,
            json={
                "id": "remote_fixture",
                "size": str(len(uploaded)),
                "md5Checksum": "bad" if bad_checksum else hashlib.md5(payload).hexdigest(),
            },
        )

    drive, _ = make_drive(tmp_path, google)
    drive.data["tokens"] = {**tokens(), "expires_at": time.time() + 3600}
    source = tmp_path / "media.bin"
    source.write_bytes(payload)
    try:
        if bad_checksum or evil_location:
            with pytest.raises(DriveError):
                drive.upload(source, FOLDER_ID, "fixture.bin", "application/octet-stream")
        else:
            result = drive.upload(source, FOLDER_ID, "fixture.bin", "application/octet-stream")
            assert result["bytes"] == len(payload) and bytes(uploaded) == payload
        assert source.read_bytes() == payload
    finally:
        drive.close()


@pytest.mark.skipif(os.name != "nt", reason="DPAPI")
def test_backup_manifest_last_no_database_and_failure_preserves_local(tmp_path):
    uploads, contents = [], {}

    def google(request):
        if request.method == "GET" and request.url.path == "/drive/v3/files":
            return httpx.Response(200, json={"files": []})
        if request.method == "POST" and request.url.path == "/drive/v3/files":
            name = json.loads(request.content)["name"]
            return httpx.Response(200, json={"id": "folder_" + name})
        if request.method == "POST":
            name = json.loads(request.content)["name"]
            uploads.append(name)
            return httpx.Response(
                200,
                headers={
                    "location": "https://www.googleapis.com/upload/drive/v3/files?upload_id=fixture"
                },
            )
        if request.method == "PUT":
            contents[uploads[-1]] = bytes(request.content)
            return httpx.Response(
                200,
                json={
                    "id": "remote_manifest",
                    "size": str(len(request.content)),
                    "md5Checksum": hashlib.md5(request.content).hexdigest(),
                },
            )
        value = list(contents.values())[-1]
        return httpx.Response(
            200,
            json={
                "id": "remote_manifest",
                "parents": ["folder_Backups"],
                "md5Checksum": hashlib.md5(value).hexdigest(),
            },
        )

    drive, store = make_drive(tmp_path, google)
    drive.data["tokens"] = {**tokens(), "expires_at": time.time() + 3600}
    backup = DriveBackup(drive, store)
    try:
        project = json.loads(
            (Path(__file__).parents[1] / "fixtures/project.json").read_text(encoding="utf-8")
        )
        store.create(project)
        payload = b"immutable-fixture-media"
        id = hashlib.sha256(payload).hexdigest()
        asset = {
            "id": id,
            "file": id + ".png",
            "kind": "image",
            "mime": "image/png",
            "durationTicks": 0,
            "name": "fixture.png",
            "bytes": len(payload),
        }
        (store.root / "library" / asset["file"]).write_bytes(payload)
        store.put_asset(asset)
        before = store.load(project["id"])
        backup.copy()
        manifest = json.loads(list(contents.values())[-1])
        assert manifest["format"] == "amvs-drive-checkpoint/1"
        assert backup.status()["status"] == "succeeded"
        assert list(manifest["assets"]) == [id] and len(manifest["projects"]) == 1
        assert uploads[0] == asset["file"] and uploads[1].endswith(".amvs.json")
        assert store.load(project["id"]) == before  # Cloud checkpoint never marks manual save.
        assert all(not name.endswith((".sqlite", ".db", ".stage")) for name in uploads)
        previous = drive.data["lastBackup"]
        drive.client.close()
        drive.client = httpx.Client(
            transport=httpx.MockTransport(
                lambda _: httpx.Response(403, text="private-provider-body")
            )
        )
        backup.run()
        assert backup.status()["status"] == "failed"
        assert drive.data["lastBackup"] == previous and store.path.is_file()
        assert "private-provider-body" not in json.dumps(backup.status())
    finally:
        drive.close()


def test_drive_routes_require_session_origin_and_explicit_upload_consent(tmp_path):
    token = "test-drive-session-" + "x" * 48
    origin = "http://127.0.0.1:3000"
    headers = {"host": "testserver", "origin": origin, "authorization": "Bearer " + token}
    app = create_app(tmp_path, token, origin, "testserver", headroom=0)
    with TestClient(app) as client:
        assert client.get("/api/v1/drive").status_code == 403
        assert client.post("/api/v1/drive/backup", headers=headers, json={}).status_code == 422
        assert (
            client.post(
                "/api/v1/drive/backup", headers=headers, json={"confirmed": True}
            ).status_code
            == 409
        )
        assert client.get("/api/v1/drive", headers=headers).json()["connected"] is False
