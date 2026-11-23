"""Opt-in Drive connection. OAuth callback is isolated from the authenticated API.

No credentials are shared with the chat connector. No arbitrary Google URLs,
browser tokens, live databases, or automatic source deletion.
"""

import base64
import ctypes
import hashlib
import hmac
import json
import os
import re
import secrets
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlencode, urlparse

import httpx

from .store import contained

SCOPE = "https://www.googleapis.com/auth/drive.file"
API = "https://www.googleapis.com/drive/v3/files"
FOLDER = "application/vnd.google-apps.folder"


class DriveError(Exception):
    """Only safe, user-facing messages; never propagate provider response bodies."""


def folder_id(value):
    if not isinstance(value, str):
        raise ValueError("Cần link thư mục Drive.")
    if value.startswith("https://drive.google.com/"):
        value = urlparse(value).path.removeprefix("/drive/folders/").rstrip("/")
    if not re.fullmatch(r"[A-Za-z0-9_-]{10,200}", value):
        raise ValueError("Link thư mục Drive không hợp lệ.")
    return value


def protect(data, decrypt=False):
    """Windows DPAPI, current-user scope; intentionally no plaintext fallback."""
    if os.name != "nt":
        raise DriveError("Kết nối Drive hiện cần Windows để bảo vệ thông tin đăng nhập.")

    class Blob(ctypes.Structure):
        _fields_ = [("size", ctypes.c_ulong), ("data", ctypes.POINTER(ctypes.c_ubyte))]

    buffer = ctypes.create_string_buffer(data)
    source = Blob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte)))
    target = Blob()
    crypt = ctypes.WinDLL("crypt32", use_last_error=True)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    function = crypt.CryptUnprotectData if decrypt else crypt.CryptProtectData
    function.argtypes = [
        ctypes.POINTER(Blob),
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_ulong,
        ctypes.POINTER(Blob),
    ]
    function.restype = ctypes.c_int
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.restype = ctypes.c_void_p
    if not function(ctypes.byref(source), None, None, None, None, 1, ctypes.byref(target)):
        raise DriveError("Không thể mở kho đăng nhập Drive của tài khoản Windows này.")
    try:
        return ctypes.string_at(target.data, target.size)
    finally:
        kernel.LocalFree(target.data)


class Drive:
    def __init__(self, root, transport=None):
        self.path = contained(root / "runtime/drive.dpapi", root)
        self.lock = threading.RLock()
        self.client = httpx.Client(timeout=60, follow_redirects=False, transport=transport)
        self.pending = None
        self.server = None
        self.message = "Chưa kết nối Google Drive."
        self.data = {}
        preference = contained(root / "runtime/drive-folder.json", root)
        if preference.is_file() and preference.stat().st_size < 2048:
            try:
                self.data["folder"] = folder_id(json.loads(preference.read_text())["folder"])
            except (ValueError, KeyError):
                pass
        if self.path.exists():
            try:
                self.data = json.loads(protect(self.path.read_bytes(), decrypt=True))
            except (ValueError, OSError, DriveError):
                self.message = "Không mở được đăng nhập cũ. Hãy cấu hình lại Drive."

    def persist(self):
        stage = self.path.with_suffix(".stage")
        with stage.open("wb") as output:
            output.write(protect(json.dumps(self.data).encode()))
            output.flush()
            os.fsync(output.fileno())
        os.replace(stage, self.path)

    def status(self):
        with self.lock:
            return {
                "configured": bool(self.data.get("client")),
                "connected": bool(self.data.get("tokens")),
                "pending": bool(self.pending and self.pending["expires"] > time.monotonic()),
                "folderId": self.data.get("folder", ""),
                "folderName": self.data.get("name", ""),
                "message": self.message,
                "lastBackup": self.data.get("lastBackup"),
                "autoSync": bool(self.data.get("autoSync")),
            }

    def configure(self, credentials, folder):
        with self.lock:
            if self.pending:
                raise DriveError("Hãy hoàn tất hoặc hủy đăng nhập trước khi đổi cấu hình.")
            client = credentials.get("installed", {}) if isinstance(credentials, dict) else {}
            if not isinstance(client, dict) or any(
                not isinstance(client.get(key, ""), str) or len(client.get(key, "")) > 1024
                for key in ("client_id", "client_secret")
            ):
                raise DriveError("Cấu hình OAuth client không hợp lệ.")
            if not re.fullmatch(
                r"[A-Za-z0-9_-]+\.apps\.googleusercontent\.com", str(client.get("client_id", ""))
            ):
                raise DriveError("Cần file OAuth client JSON loại Desktop app từ Google Cloud.")
            self.data = {
                "client": {
                    key: client[key] for key in ("client_id", "client_secret") if key in client
                },
                "folder": folder_id(folder),
            }
            self.persist()
            self.message = "Đã cấu hình. Bấm đăng nhập và chọn đúng thư mục trên Google."
            return self.status()

    def begin(self):
        with self.lock:
            if not self.data.get("client"):
                raise DriveError("Cần cấu hình OAuth client trước khi đăng nhập Google.")
            if self.server:
                raise DriveError("Đang chờ đăng nhập. Hãy hủy hoặc hoàn tất cửa sổ Google.")
            owner = self

            class Callback(BaseHTTPRequestHandler):
                def setup(self):
                    super().setup()
                    self.connection.settimeout(10)

                def log_message(self, *_):
                    pass  # OAuth codes and state must never enter access logs.

                def do_GET(self):
                    parsed = urlparse(self.path)
                    expected = f"127.0.0.1:{self.server.server_port}"
                    if parsed.path != "/oauth/callback" or self.headers.get("Host") != expected:
                        self.send_error(404)
                        return
                    success = False
                    try:
                        owner.complete(parse_qs(parsed.query))
                        success = True
                        text = "Đã kết nối Drive. Bạn có thể đóng tab này và quay lại Studio."
                    except DriveError as error:
                        text = str(error)
                    payload = text.encode()
                    self.send_response(200 if success else 400)
                    self.send_header("Content-Type", "text/plain; charset=utf-8")
                    self.send_header("Cache-Control", "no-store")
                    self.send_header("Referrer-Policy", "no-referrer")
                    self.send_header("Content-Length", str(len(payload)))
                    self.end_headers()
                    self.wfile.write(payload)

            server = HTTPServer(("127.0.0.1", 0), Callback)
            server.timeout = 1
            self.server = server
            verifier = secrets.token_urlsafe(64)
            redirect = f"http://127.0.0.1:{server.server_port}/oauth/callback"
            self.pending = {
                "state": secrets.token_urlsafe(32),
                "verifier": verifier,
                "redirect": redirect,
                "expires": time.monotonic() + 600,
            }
            parameters = {
                "client_id": self.data["client"]["client_id"],
                "redirect_uri": redirect,
                "response_type": "code",
                "scope": SCOPE,
                "access_type": "offline",
                "prompt": "consent",
                "trigger_onepick": "true",
                "allow_folder_selection": "true",
                "file_ids": self.data["folder"],
                "mimetypes": FOLDER,
                "state": self.pending["state"],
                "code_challenge_method": "S256",
                "code_challenge": base64.urlsafe_b64encode(
                    hashlib.sha256(verifier.encode()).digest()
                )
                .rstrip(b"=")
                .decode(),
            }

            def listen():
                try:
                    while self.pending and self.pending["expires"] > time.monotonic():
                        server.handle_request()
                finally:
                    server.server_close()
                    with self.lock:
                        self.pending = None
                        self.server = None

            threading.Thread(target=listen, daemon=True).start()
            self.message = "Đang chờ đăng nhập và chọn thư mục trên Google."
            return {"url": "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(parameters)}

    def complete(self, query):
        with self.lock:
            pending = self.pending
            if (
                not pending
                or pending["expires"] <= time.monotonic()
                or not hmac.compare_digest(
                    query.get("state", [""])[0].encode("utf-8"), pending["state"].encode("utf-8")
                )
            ):
                raise DriveError("Phiên đăng nhập không hợp lệ hoặc đã hết hạn.")
            self.pending = None  # A valid state is consumed even when consent is denied.
            try:
                if query.get("error") or query.get("picked_file_ids") != [self.data["folder"]]:
                    raise DriveError(
                        "Chưa cấp quyền cho đúng thư mục đã cấu hình. Hãy kết nối lại."
                    )
                code = query.get("code", [])
                if len(code) != 1:
                    raise DriveError("Google không trả mã đăng nhập hợp lệ.")
                tokens = self.request(
                    "POST",
                    "https://oauth2.googleapis.com/token",
                    data={
                        **self.data["client"],
                        "code": code[0],
                        "code_verifier": pending["verifier"],
                        "redirect_uri": pending["redirect"],
                        "grant_type": "authorization_code",
                    },
                ).json()
                self.check_tokens(tokens)
                self.data["tokens"] = {**tokens, "expires_at": time.time() + tokens["expires_in"]}
                folder = self.request(
                    "GET",
                    API + "/" + self.data["folder"],
                    headers=self.auth(),
                    params={"fields": "id,name,mimeType,trashed,capabilities(canAddChildren)"},
                ).json()
                if (
                    folder.get("mimeType") != FOLDER
                    or folder.get("trashed")
                    or not folder.get("capabilities", {}).get("canAddChildren")
                ):
                    raise DriveError("Thư mục Drive không tồn tại hoặc chưa có quyền ghi.")
                self.data["name"] = folder["name"]
                self.persist()
                self.message = "Đã kết nối. Chưa tự tải dữ liệu lên Drive."
            except (DriveError, KeyError, ValueError) as error:
                self.data.pop("tokens", None)
                self.persist()
                self.message = (
                    str(error) if isinstance(error, DriveError) else "Đăng nhập chưa hoàn tất."
                )
                raise DriveError(self.message) from None

    def request(self, method, url, **kwargs):
        try:
            response = self.client.request(method, url, **kwargs)
        except httpx.HTTPError:
            raise DriveError("Không kết nối được Google. Kiểm tra mạng rồi thử lại.") from None
        if response.status_code not in {200, 201, 308}:
            messages = {
                401: "Đăng nhập Drive hết hạn; hãy kết nối lại.",
                403: "Google từ chối quyền ghi hoặc đã hết quota.",
                404: "Không tìm thấy thư mục hoặc file Drive được cấp quyền.",
                429: "Google đang giới hạn tốc độ. Hãy thử lại sau.",
            }
            raise DriveError(
                messages.get(response.status_code, "Google chưa hoàn tất thao tác. Hãy thử lại.")
            )
        return response

    @staticmethod
    def check_tokens(tokens):
        if (
            not tokens.get("access_token")
            or tokens.get("token_type", "").lower() != "bearer"
            or (tokens.get("scope", SCOPE).split() != [SCOPE])
            or not isinstance(tokens.get("expires_in"), (int, float))
        ):
            raise DriveError("Google trả quyền truy cập không đúng phạm vi Drive đã yêu cầu.")

    def auth(self):
        tokens = self.data.get("tokens")
        if not tokens:
            raise DriveError("Hãy đăng nhập Google Drive trước.")
        if tokens["expires_at"] < time.time() + 60:
            if not tokens.get("refresh_token"):
                raise DriveError("Đăng nhập Drive hết hạn; hãy kết nối lại.")
            updated = self.request(
                "POST",
                "https://oauth2.googleapis.com/token",
                data={
                    **self.data["client"],
                    "refresh_token": tokens["refresh_token"],
                    "grant_type": "refresh_token",
                },
            ).json()
            self.check_tokens(updated)
            self.data["tokens"] = {
                **tokens,
                **updated,
                "expires_at": time.time() + updated["expires_in"],
            }
            self.persist()
        return {"Authorization": "Bearer " + self.data["tokens"]["access_token"]}

    def disconnect(self):
        with self.lock:
            self.pending = None
            self.data.pop("tokens", None)
            self.data["autoSync"] = False
            self.persist()
            self.message = "Đã ngắt kết nối trên máy. Có thể thu hồi quyền tại tài khoản Google."
            return self.status()

    def set_auto(self, enabled):
        with self.lock:
            if enabled and not self.data.get("tokens"):
                raise DriveError("Hãy kết nối Drive trước khi bật tự sao lưu.")
            self.data["autoSync"] = bool(enabled)
            self.persist()
            return self.status()

    def close(self):
        self.pending = None
        # Callback handler may still be exchanging a token; finish before closing HTTP client.
        with self.lock:
            self.client.close()

    def child_folder(self, parent, name):
        result = self.request(
            "GET",
            API,
            headers=self.auth(),
            params={
                "q": f"'{parent}' in parents and trashed=false and mimeType='{FOLDER}' "
                f"and name='{name}' and appProperties has {{ key='amvs' and value='1' }}",
                "fields": "files(id)",
                "pageSize": 100,
            },
        ).json()["files"]
        if result:
            return result[0]["id"]
        return self.request(
            "POST",
            API,
            headers=self.auth(),
            json={
                "name": name,
                "mimeType": FOLDER,
                "parents": [parent],
                "appProperties": {"amvs": "1"},
            },
            params={"fields": "id"},
        ).json()["id"]

    def upload(self, path, parent, name, mime):
        """Bounded resumable upload. Only verified bytes enter a snapshot manifest."""
        size = path.stat().st_size
        md5 = hashlib.md5(usedforsecurity=False)
        with path.open("rb") as source:
            for chunk in iter(lambda: source.read(1024**2), b""):
                md5.update(chunk)
        started = self.request(
            "POST",
            "https://www.googleapis.com/upload/drive/v3/files",
            params={"uploadType": "resumable", "fields": "id,size,md5Checksum"},
            headers={
                **self.auth(),
                "X-Upload-Content-Type": mime,
                "X-Upload-Content-Length": str(size),
            },
            json={
                "name": name,
                "parents": [parent],
                "appProperties": {"amvs": "1"},
            },
        )
        location = started.headers.get("location", "")
        url = urlparse(location)
        if (
            url.scheme != "https"
            or url.netloc != "www.googleapis.com"
            or not url.path.startswith("/upload/drive/v3/files")
        ):
            raise DriveError("Google trả địa chỉ upload không hợp lệ.")
        with path.open("rb") as source:
            offset = 0
            while chunk := source.read(8 * 1024**2):
                end = offset + len(chunk)
                response = self.request(
                    "PUT",
                    location,
                    headers={
                        **self.auth(),
                        "Content-Type": mime,
                        "Content-Range": f"bytes {offset}-{end - 1}/{size}",
                    },
                    content=chunk,
                )
                if end < size:
                    if (
                        response.status_code != 308
                        or response.headers.get("range") != f"bytes=0-{end - 1}"
                    ):
                        raise DriveError("Upload chưa đủ dữ liệu. Bản local vẫn được giữ nguyên.")
                elif response.status_code not in {200, 201}:
                    raise DriveError("Google chưa xác nhận hoàn tất file.")
                offset = end
        if not size:
            raise DriveError("Không sao lưu file rỗng.")
        result = response.json()
        if int(result.get("size", -1)) != size or result.get("md5Checksum") != md5.hexdigest():
            raise DriveError(
                "Checksum hoặc kích thước trên Drive không khớp; snapshot chưa hoàn tất."
            )
        return {"fileId": result["id"], "bytes": size, "md5": md5.hexdigest()}

    def download(self, file_id, target, expected_bytes, expected_md5, expected_sha256=None):
        if not re.fullmatch(r"[A-Za-z0-9_-]{10,200}", str(file_id)):
            raise DriveError("ID file Drive không hợp lệ.")
        if (
            not isinstance(expected_bytes, int)
            or expected_bytes < 0
            or expected_bytes > 2 * 1024**3
        ):
            raise DriveError("Kích thước bản sao lưu không hợp lệ.")
        md5, sha = hashlib.md5(usedforsecurity=False), hashlib.sha256()
        count = 0
        created = False
        try:
            with self.client.stream(
                "GET", API + "/" + file_id, params={"alt": "media"}, headers=self.auth()
            ) as response:
                if response.status_code != 200:
                    raise DriveError("Không đọc được file Drive đã sao lưu.")
                with target.open("xb") as output:
                    created = True
                    for chunk in response.iter_bytes(1024**2):
                        count += len(chunk)
                        if count > expected_bytes:
                            raise DriveError("File Drive lớn hơn manifest; đã dừng tải.")
                        output.write(chunk)
                        md5.update(chunk)
                        sha.update(chunk)
            if (
                count != expected_bytes
                or md5.hexdigest() != expected_md5
                or (expected_sha256 and sha.hexdigest() != expected_sha256)
            ):
                raise DriveError("Checksum file Drive không khớp manifest.")
        except httpx.HTTPError:
            raise DriveError("Không tải được Drive. Kiểm tra mạng rồi thử lại.") from None
        except BaseException:
            if created:
                target.unlink(missing_ok=True)
            raise
        return sha.hexdigest()
