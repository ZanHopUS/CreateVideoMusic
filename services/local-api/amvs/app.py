"""Loopback API with session authentication and backend-owned folder grants."""

import asyncio
import hashlib
import hmac
import json
import os
import re
import sys
import uuid
import zipfile
from contextlib import asynccontextmanager
from pathlib import Path

import av
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse

from .catalog import Catalog
from .domain import ROOT, parse_json
from .drive import Drive, DriveError
from .drive_backup import DriveBackup
from .drive_restore import DriveRestore
from .edit_leases import EditLeases
from .jobs import Jobs, RenderInputError
from .media import probe
from .providers import PROVIDERS, AIUnavailable
from .snapshots import Snapshots
from .source_gc import SourceGC
from .storage_policy import StorageQuota
from .store import Conflict, Store, contained


class BudgetExceeded(ValueError):
    pass


async def body(request):
    content = bytearray()
    async for chunk in request.stream():
        content.extend(chunk)
        if len(content) > 16 * 1024**2:
            raise BudgetExceeded("Dữ liệu vượt giới hạn 16 MiB.")
    value = parse_json(content)
    if not isinstance(value, dict):
        raise ValueError("Body phải là JSON object.")
    return value


def create_app(workspace=None, token=None, origin=None, api_host=None, headroom=4):
    token = token or os.environ.get("AMVS_SESSION")
    if not token or len(token) < 32:
        raise RuntimeError("Launcher phải cấp session token.")
    origin = origin or os.environ.get("AMVS_ORIGIN", "http://127.0.0.1:3000")
    api_host = api_host or os.environ.get("AMVS_API_HOST", "127.0.0.1:8765")
    store = Store(workspace or os.environ.get("AMVS_WORKSPACE", str(ROOT / ".local/workspace")))
    jobs = Jobs(store, headroom=headroom)
    drive = Drive(store.root)
    drive_backup = DriveBackup(drive, store)
    drive_restore = DriveRestore(drive, store)
    snapshots = Snapshots(store)
    catalog = Catalog(store)
    source_gc = SourceGC(store)
    leases = EditLeases()
    grants = {}
    picker_lock = asyncio.Lock()
    drive_control = asyncio.Lock()

    @asynccontextmanager
    async def lifespan(_):
        snapshots.start()
        drive_backup.start_monitor()
        yield
        await asyncio.to_thread(snapshots.close)
        await asyncio.to_thread(jobs.shutdown)
        await asyncio.to_thread(drive_backup.close)
        await asyncio.to_thread(drive_restore.close)
        await asyncio.to_thread(drive.close)

    app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
    app.state.snapshots = snapshots
    app.state.catalog = catalog
    app.state.store = store
    app.state.jobs = jobs
    app.state.grants = grants
    app.state.drive = drive
    app.state.drive_backup = drive_backup
    app.state.drive_restore = drive_restore

    @app.middleware("http")
    async def security(request, call_next):
        if request.headers.get("host") != api_host:
            return JSONResponse({"code": "HOST", "message": "Host không được phép."}, 403)
        if request.url.path == "/health" and request.method == "GET":
            return await call_next(request)
        if request.headers.get("origin") != origin:
            return JSONResponse(
                {"code": "ORIGIN", "message": "Nguồn truy cập không được phép."}, 403
            )
        header = request.headers.get("authorization", "")
        auth = header[7:] if header.startswith("Bearer ") else ""
        media = request.method in {"GET", "HEAD"} and re.fullmatch(
            r"/api/v1/(assets/[a-f0-9]{64}/(?:content|thumbnail)|outputs/[a-f0-9]{32}|drive/exports/[a-f0-9]{64})",
            request.url.path,
        )
        if not auth and media:
            auth = request.cookies.get("amvs_media", "")
        if not hmac.compare_digest(auth.encode("utf-8"), token.encode("utf-8")):
            return JSONResponse({"code": "SESSION", "message": "Phiên làm việc đã hết hạn."}, 401)
        try:
            response = await call_next(request)
        except RenderInputError as error:
            return JSONResponse({"code": "RENDER_INPUT", "message": str(error)}, 422)
        except StorageQuota as error:
            return JSONResponse({"code": "STORAGE_QUOTA", "message": str(error)}, 507)
        except AIUnavailable as error:
            return JSONResponse({"code": "AI_UNAVAILABLE", "message": str(error)}, 422)
        except DriveError as error:
            return JSONResponse({"code": "DRIVE", "message": str(error)}, 409)
        except (
            ValueError,
            KeyError,
            PermissionError,
            FileNotFoundError,
            Conflict,
            zipfile.BadZipFile,
            TypeError,
            av.FFmpegError,
        ) as error:
            status = (
                413
                if isinstance(error, BudgetExceeded)
                else 409
                if isinstance(error, Conflict)
                else 403
                if isinstance(error, PermissionError)
                else 404
                if isinstance(error, (KeyError, FileNotFoundError))
                else 422
            )
            messages = {
                403: "Không có quyền thao tác thư mục này.",
                404: "Không tìm thấy dữ liệu.",
                409: "Project đã thay đổi. Hãy tải lại để tránh mất chỉnh sửa.",
                413: "File hoặc dữ liệu vượt giới hạn cho phép.",
                422: "Dữ liệu hoặc media không hợp lệ.",
            }
            return JSONResponse({"code": type(error).__name__, "message": messages[status]}, status)
        except OSError:
            return JSONResponse(
                {
                    "code": "STORAGE_IO",
                    "message": "Không thể ghi dữ liệu. Kiểm tra dung lượng và quyền thư mục.",
                },
                507,
            )
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    @app.get("/health")
    def health():
        return {"status": "ok", "application": "AI Music Video Studio"}

    @app.get("/api/v1/session")
    def session():
        response = JSONResponse(
            {
                "scope": "local",
                "cloudEnabled": False,  # Cloud AI remains disabled; Drive is separate opt-in storage.
                "driveConnected": drive.status()["connected"],
                "templates": ["TPL-01", "TPL-02", "TPL-03"],
                "maxUploadBytes": 2 * 1024**3,
            }
        )
        # Native <audio>/<img> cannot attach bearer headers. Read-only streams use
        # an HttpOnly same-site session cookie; all writes still require a header.
        response.set_cookie("amvs_media", token, httponly=True, samesite="strict", path="/api/v1")
        return response

    @app.get("/api/v1/drive")
    def drive_status():
        return {
            **drive.status(),
            "backup": drive_backup.status(),
            "restore": drive_restore.status(),
        }

    def drive_idle():
        if (
            drive_backup.status()["status"] == "running"
            or drive_restore.status()["status"] == "running"
        ):
            raise DriveError("Đang chuyển dữ liệu Drive. Hãy chờ hoàn tất trước khi đổi đăng nhập.")

    @app.post("/api/v1/drive/configure")
    async def drive_configure(request: Request):
        data = await body(request)
        if set(data) != {"credentials", "folder"} or len(json.dumps(data)) > 32768:
            raise ValueError("Cấu hình Drive không hợp lệ.")
        async with drive_control:
            drive_idle()
            return await asyncio.to_thread(drive.configure, data["credentials"], data["folder"])

    @app.post("/api/v1/drive/connect")
    async def drive_connect():
        async with drive_control:
            drive_idle()
            return await asyncio.to_thread(drive.begin)

    @app.post("/api/v1/drive/disconnect")
    async def drive_disconnect():
        async with drive_control:
            drive_idle()
            return await asyncio.to_thread(drive.disconnect)

    @app.post("/api/v1/drive/auto")
    async def drive_auto(request: Request):
        data = await body(request)
        if (
            set(data) != {"enabled", "confirmed"}
            or not isinstance(data["enabled"], bool)
            or data["confirmed"] is not True
        ):
            raise ValueError("Cần đồng ý bật hoặc tắt tự sao lưu Drive.")
        async with drive_control:
            drive_idle()
            return await asyncio.to_thread(drive.set_auto, data["enabled"])

    @app.post("/api/v1/drive/backup")
    async def backup_drive(request: Request):
        if await body(request) != {"confirmed": True}:
            raise ValueError("Cần đồng ý tải bản sao lên Drive.")
        async with drive_control:
            drive_idle()
            return JSONResponse(drive_backup.start(), status_code=202)

    @app.get("/api/v1/drive/backups")
    async def drive_backups():
        return await asyncio.to_thread(drive_restore.list)

    @app.post("/api/v1/drive/restore")
    async def restore_drive(request: Request):
        data = await body(request)
        if set(data) != {"manifestId", "confirmed"} or data["confirmed"] is not True:
            raise ValueError("Cần chọn bản sao lưu để khôi phục.")
        async with drive_control:
            drive_idle()
            return JSONResponse(
                await asyncio.to_thread(drive_restore.start, data["manifestId"]), status_code=202
            )

    @app.get("/api/v1/drive/exports")
    def drive_exports():
        root = contained(store.root / "exports", store.root)
        if not root.is_dir():
            return []
        return [
            {"sha256": p.stem, "bytes": p.stat().st_size}
            for p in root.glob("*.mp4")
            if re.fullmatch(r"[a-f0-9]{64}", p.stem)
        ]

    @app.get("/api/v1/drive/exports/{sha}")
    def download_drive_export(sha: str):
        if not re.fullmatch(r"[a-f0-9]{64}", sha):
            raise ValueError("MP4 ID không hợp lệ.")
        root = contained(store.root / "exports", store.root)
        file = contained(root / (sha + ".mp4"), root)
        if not file.is_file():
            raise FileNotFoundError("MP4 chưa khôi phục.")
        return FileResponse(file, media_type="video/mp4", filename=file.name)

    async def choose(open_file=False, media=False):
        async with picker_lock:
            args = [sys.executable, str(ROOT / "services/local-api/amvs/picker.py")]
            if open_file:
                args.append("--media" if media else "--open")
            process = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1"),
            )
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=300)
            except (TimeoutError, asyncio.CancelledError):
                process.kill()
                await process.wait()
                raise ValueError("Đã hủy chọn thư mục.")
            if process.returncode:
                raise ValueError("Không mở được hộp thoại chọn thư mục.")
            return json.loads(stdout.decode())["path"]

    @app.post("/api/v1/folder-grants")
    async def folder_grant(request: Request):
        data = await body(request)
        if set(data) - {"scope"} or data.get("scope") not in {"project", "export", "backup"}:
            raise ValueError("Scope không hợp lệ.")
        selected = await choose()
        if not selected:
            return {"cancelled": True}
        path = Path(selected).resolve()
        if not path.is_dir():
            raise ValueError("Thư mục không tồn tại.")
        id = uuid.uuid4().hex
        grants[id] = {"scope": data["scope"], "path": path}
        return {"id": id, "label": path.name, "scope": data["scope"]}

    @app.delete("/api/v1/folder-grants/{id}")
    def revoke(id: str):
        grant = grants.pop(id, None)
        if grant:
            for key, job in list(jobs.rows.items()):
                if job.get("grant") == str(grant["path"]):
                    jobs.cancel(key)
        return {"revoked": True}

    def folder(id, scope):
        grant = grants.get(id)
        if not grant or grant["scope"] != scope:
            raise PermissionError("Grant không hợp lệ.")
        return grant["path"]

    @app.post("/api/v1/projects/open")
    async def open_project():
        selected = await choose(True)
        if not selected:
            return {"cancelled": True}
        if str(selected).endswith(".amvs"):
            return await asyncio.to_thread(snapshots.import_package, Path(selected))
        return await asyncio.to_thread(store.open_manual, Path(selected))

    @app.get("/api/v1/projects")
    def list_projects():
        return store.list_projects()

    @app.post("/api/v1/projects")
    async def create(request: Request):
        return store.create(await body(request))

    @app.get("/api/v1/projects/{id}")
    def load(id: str):
        return store.load(id)

    @app.post("/api/v1/projects/{id}/editor-session")
    async def editor_session(id: str, request: Request):
        store.load(id)
        data = await body(request)
        if set(data) - {"assetPins", "pinAllAssets"} != {"takeover"} or not isinstance(
            data["takeover"], bool
        ):
            raise ValueError("Trường không hợp lệ.")
        pins = data.get("assetPins", [])
        if (
            not isinstance(pins, list)
            or len(pins) > 4096
            or any(not isinstance(p, str) or not re.fullmatch(r"[a-f0-9]{64}", p) for p in pins)
            or not isinstance(data.get("pinAllAssets", False), bool)
        ):
            raise ValueError("History pins không hợp lệ.")
        lease = leases.claim(id, request.headers.get("x-amvs-editor"), data["takeover"])
        if lease["canWrite"]:
            store.pin_assets(store.assets().keys() if data.get("pinAllAssets") else pins)
        return lease

    @app.delete("/api/v1/projects/{id}/editor-session")
    def release_editor(id: str, request: Request):
        return leases.release(id, request.headers.get("x-amvs-editor"))

    @app.patch("/api/v1/projects/{id}")
    async def update(id: str, request: Request):
        data = await body(request)
        if set(data) - {"project", "revision", "view"}:
            raise ValueError("Trường không hợp lệ.")
        with leases.guard(id, request.headers.get("x-amvs-editor")):
            return store.update(id, data["project"], data["revision"], data.get("view"))

    @app.delete("/api/v1/projects/{id}")
    def delete(id: str, request: Request):
        with leases.guard(id, request.headers.get("x-amvs-editor")), store.connect() as db:
            db.execute("DELETE FROM projects WHERE id=?", (id,))
        return {"deleted": True, "sharedAssetsPreserved": True}

    @app.post("/api/v1/projects/{id}/save")
    async def save(id: str, request: Request):
        data = await body(request)
        if set(data) - {"project", "revision", "grantId"}:
            raise ValueError("Trường không hợp lệ.")
        editor = request.headers.get("x-amvs-editor")
        destination = folder(data["grantId"], "project")

        def save_owned():
            # Recheck in the thread doing the write; a queued operation cannot
            # retain permission after another tab has taken over.
            with leases.guard(id, editor):
                return store.save(id, data["project"], data["revision"], destination)

        return await asyncio.to_thread(save_owned)

    @app.get("/api/v1/projects/{id}/recoveries")
    def recoveries(id: str):
        return {"snapshots": snapshots.list(id), "warning": snapshots.warning}

    @app.post("/api/v1/projects/{id}/recoveries")
    def capture_recovery(id: str):
        return snapshots.capture(id)

    @app.post("/api/v1/projects/{id}/restore")
    async def restore_recovery(id: str, request: Request):
        data = await body(request)
        if set(data) != {"recoveryId", "revision", "confirmed"} or data["confirmed"] is not True:
            raise ValueError("Cần xác nhận recovery.")
        with leases.guard(id, request.headers.get("x-amvs-editor")):
            return snapshots.restore(id, data["recoveryId"], data["revision"])

    @app.delete("/api/v1/projects/{id}/recoveries")
    async def clear_recovery(id: str, request: Request):
        data = await body(request)
        if set(data) != {"ids", "confirmed"} or data["confirmed"] is not True:
            raise ValueError("Cần xác nhận dọn recovery.")
        with leases.guard(id, request.headers.get("x-amvs-editor")):
            return snapshots.clear(id, data["ids"])

    @app.post("/api/v1/projects/{id}/packages")
    async def package_project(id: str, request: Request):
        data = await body(request)
        if set(data) != {"revision", "grantId"}:
            raise ValueError("Trường không hợp lệ.")
        current = store.load(id)
        if current["revision"] != data["revision"]:
            raise Conflict("Revision cũ.")
        return JSONResponse(jobs.start_package(current, folder(data["grantId"], "backup")), 202)

    @app.get("/api/v1/projects/{id}/media-status")
    def media_status(id: str):
        current = store.load(id)
        assets = store.assets()
        missing = []
        from .store import digest_file

        for key in current["project"]["assetRefs"]:
            try:
                if digest_file(store.asset_path(assets[key])) != key:
                    missing.append(key)
            except (OSError, KeyError):
                missing.append(key)
        return {"missing": missing}

    @app.post("/api/v1/assets/{id}/relink")
    async def relink(id: str, request: Request):
        data = await body(request)
        if data != {"confirmed": True} or id not in store.assets():
            raise ValueError("Cần xác nhận relink media.")
        selected = await choose(True, True)
        if not selected:
            return {"cancelled": True}
        from .store import digest_file

        source = Path(selected)
        if (
            source.stat().st_size > 2 * 1024**3
            or await asyncio.to_thread(digest_file, source) != id
        ):
            raise ValueError("File phải có cùng checksum với media gốc.")
        asset = store.assets()[id]
        library = contained(store.root / "library", store.root)
        target = contained(library / asset["file"], library)
        stage = contained(library / (uuid.uuid4().hex + ".stage"), library)
        import shutil

        try:
            await asyncio.to_thread(shutil.copyfile, source, stage)
            if digest_file(stage) != id:
                raise ValueError("Nguồn đã thay đổi khi copy.")
            os.replace(stage, target)
        finally:
            stage.unlink(missing_ok=True)
        return {"relinked": True}

    @app.get("/api/v1/templates")
    def templates():
        return catalog.templates()

    @app.post("/api/v1/templates")
    async def save_template(request: Request):
        data = await body(request)
        if set(data) != {"projectId", "revision", "name", "itemIds"}:
            raise ValueError("Trường không hợp lệ.")
        current = store.load(data["projectId"])
        if current["revision"] != data["revision"]:
            raise Conflict("Revision cũ.")
        return catalog.save_template(current["project"], data["name"], data["itemIds"])

    @app.post("/api/v1/templates/{id}/instances")
    async def template_instance(id: str, request: Request):
        data = await body(request)
        if set(data) != {"bindings"}:
            raise ValueError("Trường không hợp lệ.")
        return catalog.instantiate(id, data["bindings"])

    @app.patch("/api/v1/assets/{id}/tags")
    async def asset_tags(id: str, request: Request):
        data = await body(request)
        if set(data) != {"tags"}:
            raise ValueError("Trường không hợp lệ.")
        return catalog.tags(id, data["tags"])

    @app.get("/api/v1/assets/{id}/thumbnail")
    def thumbnail(id: str):
        return FileResponse(catalog.thumbnail(id), media_type="image/jpeg")

    @app.post("/api/v1/assets/{id}/suggestions")
    async def suggestions(id: str):
        return await asyncio.to_thread(catalog.suggestions, id)

    @app.get("/api/v1/assets")
    def assets():
        return list(store.assets().values())

    @app.post("/api/v1/assets")
    async def upload(request: Request):
        # Parse one multipart file with a bounded overall body, independent of
        # user supplied Content-Length. python-multipart spools files to disk.
        limit = 2 * 1024**3
        received = 0

        async def bounded_stream():
            nonlocal received
            async for chunk in request.stream():
                received += len(chunk)
                if received > limit + 1024**2:
                    raise BudgetExceeded("File quá lớn (tối đa 2 GiB).")
                yield chunk

        from starlette.formparsers import MultiPartParser

        form = await MultiPartParser(
            request.headers, bounded_stream(), max_files=1, max_fields=1, max_part_size=1024**2
        ).parse()
        try:
            file = form.get("file")
            if not hasattr(file, "read") or form.get("rightsConfirmed") != "true":
                raise ValueError("Cần xác nhận quyền dùng media.")
            library = contained(store.root / "library", store.root)
            stage = contained(library / f"{uuid.uuid4().hex}.stage", library)
            hash = hashlib.sha256()
            count = 0
            try:
                with stage.open("xb") as output:
                    while chunk := await file.read(1024 * 1024):
                        count += len(chunk)
                        if count > limit:
                            raise BudgetExceeded("File quá lớn.")
                        output.write(chunk)
                        hash.update(chunk)
                try:
                    metadata = await asyncio.to_thread(probe, stage)
                except (av.FFmpegError, StopIteration, IndexError, TypeError) as error:
                    raise ValueError("Không đọc được media.") from error
                id = hash.hexdigest()
                name = id + metadata.pop("extension")
                target = contained(library / name, library)
                if not target.exists():
                    os.replace(stage, target)
                else:
                    from .store import digest_file

                    if digest_file(target) != id:
                        raise ValueError(
                            "Bản media local đã hỏng; cần khôi phục hoặc liên kết lại."
                        )
                    stage.unlink()
                asset = {
                    "id": id,
                    "file": name,
                    "name": Path(file.filename or "Media").name[:200],
                    "bytes": count,
                    **metadata,
                }
                store.put_asset(asset)
                return asset
            finally:
                if stage.exists():
                    stage.unlink()
        finally:
            await form.close()

    @app.api_route("/api/v1/assets/{id}/content", methods=["GET", "HEAD"])
    def asset_content(id: str):
        asset = store.assets().get(id)
        if not asset:
            raise KeyError(id)
        return FileResponse(store.asset_path(asset), media_type=asset["mime"])

    @app.get("/api/v1/jobs")
    def list_jobs():
        return [jobs.public(id) for id in reversed(list(jobs.rows))]

    @app.post("/api/v1/jobs")
    async def start_job(request: Request):
        data = await body(request)
        if set(data) - {"projectId", "revision", "grantId"}:
            raise ValueError("Trường không hợp lệ.")
        current = store.load(data["projectId"])
        if current["revision"] != data["revision"]:
            raise Conflict("Revision cũ.")
        return JSONResponse(
            jobs.start(current["project"], folder(data["grantId"], "export")), status_code=202
        )

    @app.get("/api/v1/storage/policy")
    def storage_policy():
        return catalog.storage.status()

    @app.patch("/api/v1/storage/policy")
    async def configure_storage(request: Request):
        return catalog.storage.configure(await body(request))

    @app.post("/api/v1/storage/cache/cleanup")
    async def clear_cache(request: Request):
        if await body(request) != {"confirmed": True}:
            raise ValueError("Cần xác nhận dọn cache.")
        return await asyncio.to_thread(catalog.storage.clear_cache)

    @app.get("/api/v1/storage/source-gc")
    def source_gc_preview():
        return source_gc.preview()

    @app.post("/api/v1/storage/source-gc")
    async def source_gc_collect(request: Request):
        data = await body(request)
        if set(data) != {"ids", "confirmed"} or data["confirmed"] is not True:
            raise ValueError("Cần xem danh sách và xác nhận xóa media.")
        return await asyncio.to_thread(source_gc.collect, data["ids"])

    @app.get("/api/v1/storage/temp")
    def temp_inventory():
        return {"jobs": jobs.temp_inventory(), "assetPolicy": "preserve-all-managed-source-assets"}

    @app.post("/api/v1/storage/temp/cleanup")
    async def temp_cleanup(request: Request):
        data = await body(request)
        if set(data) != {"ids", "confirmed"} or data["confirmed"] is not True:
            raise ValueError("Cần xác nhận dọn temp.")
        return await asyncio.to_thread(jobs.clean_temp, data["ids"])

    @app.get("/api/v1/ai/providers")
    def providers():
        return {
            "default": "local",
            "providers": [p.status() for p in PROVIDERS.values()],
            "cloudEgress": False,
        }

    @app.post("/api/v1/lyrics/jobs")
    async def lyrics_job(request: Request):
        data = await body(request)
        if set(data) - {"provider"} != {
            "projectId",
            "revision",
            "audioItemId",
            "language",
            "model",
        }:
            raise ValueError("Trường không hợp lệ.")
        current = store.load(data["projectId"])
        if current["revision"] != data["revision"]:
            raise Conflict("Revision cũ.")
        return JSONResponse(
            jobs.start_asr(
                current["project"],
                data["audioItemId"],
                data["language"],
                data["model"],
                provider_id=data.get("provider", "local"),
            ),
            202,
        )

    @app.post("/api/v1/lyrics/alignment")
    async def alignment_job(request: Request):
        data = await body(request)
        if set(data) != {"projectId", "revision", "audioItemId", "language", "lines"}:
            raise ValueError("Trường không hợp lệ.")
        current = store.load(data["projectId"])
        if current["revision"] != data["revision"]:
            raise Conflict("Revision cũ.")
        return JSONResponse(
            jobs.start_asr(
                current["project"], data["audioItemId"], data["language"], "small", data["lines"]
            ),
            202,
        )

    @app.get("/api/v1/jobs/{id}/package")
    def package_result(id: str):
        return jobs.package_result(id)

    @app.get("/api/v1/jobs/{id}/lyrics")
    def lyrics_result(id: str):
        return jobs.lyrics_result(id)

    @app.get("/api/v1/jobs/{id}")
    def job(id: str):
        return jobs.public(id)

    @app.post("/api/v1/jobs/{id}/cancel")
    def cancel(id: str):
        return jobs.cancel(id)

    @app.get("/api/v1/outputs/{id}")
    def output(id: str):
        job = jobs.rows[id]
        if job["status"] != "succeeded" or job["kind"] != "render":
            raise ValueError("Video chưa sẵn sàng.")
        target = contained(job["outputFile"], job["grant"])
        return FileResponse(target, media_type="video/mp4", filename=target.name)

    @app.post("/api/v1/outputs/{id}/open-folder")
    def open_output(id: str):
        job = jobs.rows[id]
        if job["status"] != "succeeded" or job["kind"] != "render":
            raise ValueError("Video chưa sẵn sàng.")
        target = contained(job["outputFile"], job["grant"])
        if os.name != "nt":
            raise ValueError("Chức năng chỉ dành cho Windows.")
        os.startfile(str(target.parent))
        return {"opened": True}

    return app
