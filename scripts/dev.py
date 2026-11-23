"""Foreground launcher owns UI/API child processes; never persists session tokens."""

import argparse
import json
import os
import secrets
import socket
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

import psutil
from launcher_lifecycle import (
    AlreadyRunning,
    WindowsOwnership,
    record_path,
    stop_owner,
    write_owner,
)

ROOT = Path(__file__).resolve().parents[1]


def port():
    with socket.socket() as server:
        server.bind(("127.0.0.1", 0))
        return server.getsockname()[1]


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--restart", action="store_true")
    parser.add_argument("--stop", action="store_true")
    args = parser.parse_args()
    if args.restart or args.stop:
        stop_owner(ROOT)
    if args.stop:
        print("Đã dừng launcher của workspace nếu có.", flush=True)
        return
    try:
        ownership = WindowsOwnership(ROOT)
    except AlreadyRunning as error:
        print(str(error), flush=True)
        return
    write_owner(ROOT)
    api_port, web_port = port(), port()
    while web_port == api_port:
        web_port = port()
    token = secrets.token_urlsafe(48)
    origin = f"http://127.0.0.1:{web_port}"
    env = dict(
        os.environ,
        AMVS_SESSION=token,
        AMVS_ORIGIN=origin,
        AMVS_API_HOST=f"127.0.0.1:{api_port}",
        AMVS_API_URL=f"http://127.0.0.1:{api_port}",
        PYTHONPATH=str(ROOT / "services/local-api"),
        AMVS_WORKSPACE=str(ROOT / ".local/workspace"),
        NEXT_TELEMETRY_DISABLED="1",
        PYTHONIOENCODING="utf-8",
        PYTHONUTF8="1",
    )
    browser = (
        ROOT
        / "node_modules/.remotion/chrome-headless-shell/win64/chrome-headless-shell-win64/chrome-headless-shell.exe"
    )
    if not browser.is_file():
        ownership.close()
        raise SystemExit("Chưa có browser render. Chạy scripts/setup.ps1 trước.")
    env["AMVS_BROWSER"] = str(browser)
    logs = ROOT / ".local/logs"
    logs.mkdir(parents=True, exist_ok=True)
    processes = []
    files = []
    try:
        for name, command, cwd in [
            (
                "api",
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "amvs.app:create_app",
                    "--factory",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(api_port),
                    "--no-access-log",
                ],
                ROOT,
            ),
            (
                "web",
                [
                    "node",
                    str(ROOT / "node_modules/next/dist/bin/next"),
                    "dev",
                    "--hostname",
                    "127.0.0.1",
                    "--port",
                    str(web_port),
                ],
                ROOT / "apps/web",
            ),
        ]:
            output = (logs / f"{name}.log").open("w", encoding="utf-8")
            files.append(output)
            processes.append(ownership.launch(command, cwd=cwd, env=env, stdout=output, stderr=-2))
        for _ in range(120):
            if any(p.poll() is not None for p in processes):
                raise RuntimeError("Dịch vụ không khởi chạy; xem .local/logs.")
            try:
                urllib.request.build_opener(urllib.request.ProxyHandler({})).open(
                    f"http://127.0.0.1:{api_port}/health", timeout=1
                ).close()
                urllib.request.build_opener(urllib.request.ProxyHandler({})).open(
                    origin, timeout=1
                ).close()
                break
            except OSError:
                time.sleep(1)
        else:
            raise TimeoutError("Khởi chạy quá lâu; xem .local/logs.")
        print(f"Studio local đang chạy tại {origin}. Nhấn Ctrl+C để dừng.", flush=True)
        if args.smoke:
            request = urllib.request.Request(
                origin + "/api/v1/session",
                headers={"Authorization": "Bearer " + token, "Origin": origin},
            )
            with urllib.request.urlopen(request, timeout=10) as response:
                session = json.load(response)
            if session["cloudEnabled"] is not False:
                raise RuntimeError("Unexpected cloud state")
            print("Launcher smoke: UI → API session hợp lệ; đang dừng owned children.", flush=True)
            return
        if not args.no_browser:
            webbrowser.open(origin + "#session=" + token)
        else:
            print("Chế độ không mở browser; token không được in ra log.", flush=True)
        while all(p.poll() is None for p in processes):
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        ownership.close()
        for process in processes:
            if process.poll() is not None:
                continue
            try:
                parent = psutil.Process(process.pid)
                children = parent.children(recursive=True)
                for child in reversed(children):
                    try:
                        child.terminate()
                    except psutil.NoSuchProcess:
                        pass
                parent.terminate()
                _, alive = psutil.wait_procs(children + [parent], timeout=5)
                for member in alive:
                    try:
                        member.kill()
                    except psutil.NoSuchProcess:
                        pass
            except psutil.NoSuchProcess:
                pass
        for output in files:
            output.close()
        path = record_path(ROOT)
        if path.exists() and json.loads(path.read_text()).get("pid") == os.getpid():
            path.unlink()


if __name__ == "__main__":
    main()
