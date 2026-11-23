"""Loopback API with session authentication and backend-owned folder grants."""

import asyncio
import hashlib
import hmac
import json
import os
import re
import sys
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

import av
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse

from .domain import ROOT, parse_json
from .jobs import Jobs
from .media import probe
from .store import Conflict, Store, contained


class BudgetExceeded(ValueError):
    pass


async def body(request):
    content = bytearray()
    async for chunk in request.stream():
        content.extend(chunk)
        if len(content) > 16 * 1024**2:
            raise BudgetExceeded("Dữ liệu vượt giới hạn 16 MiB.")
    return parse_json(content)


def create_app(workspace=None, token=None, origin=None, api_host=None, headroom=4):
    token = token or os.environ.get("AMVS_SESSION")
    if not token or len(token) < 32:
        raise RuntimeError("Launcher phải cấp session token.")
    origin = origin or os.environ.get("AMVS_ORIGIN", "http://127.0.0.1:3000")
    api_host = api_host or os.environ.get("AMVS_API_HOST", "127.0.0.1:8765")
    store = Store(workspace or os.environ.get("AMVS_WORKSPACE", str(ROOT / ".local/workspace")))
    jobs = Jobs(store, headroom=headroom)
    grants = {}
    picker_lock = asyncio.Lock()

    @asynccontextmanager
    async def lifespan(_):
        yield
        await asyncio.to_thread(jobs.shutdown)

    app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
    app.state.store = store
    app.state.jobs = jobs
    app.state.grants = grants

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
            r"/api/v1/(assets/[a-f0-9]{64}/content|outputs/[a-f0-9]{32})", request.url.path
        )
        if not auth and media:
            auth = request.cookies.get("amvs_media", "")
        if not hmac.compare_digest(auth.encode("utf-8"), token.encode("utf-8")):
            return JSONResponse({"code": "SESSION", "message": "Phiên làm việc đã hết hạn."}, 401)
        try:
            response = await call_next(request)
        except (ValueError, KeyError, PermissionError, FileNotFoundError, Conflict) as error:
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
                "cloudEnabled": False,
                "templates": ["TPL-01"],
                "maxUploadBytes": 2 * 1024**3,
            }
        )
        # Native <audio>/<img> cannot attach bearer headers. Read-only streams use
        # an HttpOnly same-site session cookie; all writes still require a header.
        response.set_cookie("amvs_media", token, httponly=True, samesite="strict", path="/api/v1")
        return response

    async def choose(open_file=False):
        async with picker_lock:
            args = [sys.executable, str(ROOT / "services/local-api/amvs/picker.py")]
            if open_file:
                args.append("--open")
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

    @app.patch("/api/v1/projects/{id}")
    async def update(id: str, request: Request):
        data = await body(request)
        if set(data) - {"project", "revision", "view"}:
            raise ValueError("Trường không hợp lệ.")
        return store.update(id, data["project"], data["revision"], data.get("view"))

    @app.delete("/api/v1/projects/{id}")
    def delete(id: str):
        with store.connect() as db:
            db.execute("DELETE FROM projects WHERE id=?", (id,))
        return {"deleted": True, "sharedAssetsPreserved": True}

    @app.post("/api/v1/projects/{id}/save")
    async def save(id: str, request: Request):
        data = await body(request)
        if set(data) - {"project", "revision", "grantId"}:
            raise ValueError("Trường không hợp lệ.")
        return await asyncio.to_thread(
            store.save, id, data["project"], data["revision"], folder(data["grantId"], "project")
        )

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

    @app.get("/api/v1/jobs/{id}")
    def job(id: str):
        return jobs.public(id)

    @app.post("/api/v1/jobs/{id}/cancel")
    def cancel(id: str):
        return jobs.cancel(id)

    @app.get("/api/v1/outputs/{id}")
    def output(id: str):
        job = jobs.rows[id]
        if job["status"] != "succeeded":
            raise ValueError("Video chưa sẵn sàng.")
        target = contained(job["outputFile"], job["grant"])
        return FileResponse(target, media_type="video/mp4", filename=target.name)

    @app.post("/api/v1/outputs/{id}/open-folder")
    def open_output(id: str):
        job = jobs.rows[id]
        if job["status"] != "succeeded":
            raise ValueError("Video chưa sẵn sàng.")
        target = contained(job["outputFile"], job["grant"])
        if os.name != "nt":
            raise ValueError("Chức năng chỉ dành cho Windows.")
        os.startfile(str(target.parent))
        return {"opened": True}

    return app
