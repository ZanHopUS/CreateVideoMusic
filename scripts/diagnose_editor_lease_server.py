"""R0 disposable service supervisor; never changes lease or revision behavior."""

import json
import os
import re
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from launcher_lifecycle import WindowsOwnership

ROOT = Path(__file__).resolve().parents[1]
if sys.argv[1:] == ["--prepare"]:
    import hashlib

    run = ROOT / ".local/evidence/ui-r0" / str(time.time_ns())
    source = run / "source"
    source.mkdir(parents=True)
    tracked = subprocess.check_output(["git", "ls-files", "--cached", "--others", "--exclude-standard"], cwd=ROOT, text=True).splitlines()
    selected = [
        name
        for name in tracked
        if name.startswith(("apps/web/", "packages/", "services/local-api/", "scripts/"))
        or name in ("package.json", "package-lock.json", "tsconfig.json")
    ]
    rows = []
    import shutil

    for name in selected:
        original = ROOT / name
        if original.is_file():
            target = source / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(original, target)
            rows.append({"path": name, "sha256": hashlib.sha256(original.read_bytes()).hexdigest()})
    build = ROOT / "apps/web/.next"
    if not (build / "BUILD_ID").is_file():
        raise SystemExit("Production build missing; prepare an isolated build before diagnosis")
    for original in build.iterdir():
        if original.is_file() or original.name in ("server", "static"):
            target = source / "apps/web/.next" / original.name
            target.parent.mkdir(parents=True, exist_ok=True)
            if original.is_dir():
                shutil.copytree(original, target)
            else:
                shutil.copy2(original, target)
    (run / "source-inventory.json").write_text(
        json.dumps(
            {
                "commit": subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
                ).strip(),
                "sourceFiles": rows,
                "productionBuildId": (build / "BUILD_ID").read_text().strip(),
                "mode": "unchanged sources and existing build; no credentials or production workspace copied",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(json.dumps({"run": str(run)}))
    sys.exit(0)

run, mode = Path(sys.argv[1]).resolve(), sys.argv[2]
assert run.is_relative_to((ROOT / ".local/evidence/ui-r0").resolve())
assert mode in {"production", "development", "development-fixture"}
source = run / "source"
folder = run / mode
folder.mkdir(exist_ok=True)
logs = []
owner = None
processes = []


def port():
    with socket.socket() as server:
        server.bind(("127.0.0.1", 0))
        return server.getsockname()[1]


def start():
    global owner, processes
    owner = WindowsOwnership(folder / "service-owner")
    processes = []
    env = dict(os.environ, NEXT_TELEMETRY_DISABLED="1", PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    for key in ("AMVS_FIDELITY_RUN", "AMVS_TEST_HEADROOM_GIB", "AMVS_TEST_LONG_RUN"):
        env.pop(key, None)
    if mode == "development":
        log = (folder / "launcher.log").open("w", encoding="utf-8")
        logs.append(log)
        processes.append(
            owner.launch(
                [sys.executable, str(source / "scripts/dev.py"), "--no-browser", "--restart"],
                cwd=source,
                env=env,
                stdout=log,
                stderr=subprocess.STDOUT,
            )
        )
        for _ in range(150):
            if processes[0].poll() is not None:
                raise RuntimeError("Disposable launcher exited; inspect local logs")
            text = (folder / "launcher.log").read_text(encoding="utf-8", errors="replace")
            match = re.search(r"http://127\.0\.0\.1:\d+", text)
            if match:
                return match.group()
            time.sleep(1)
        raise TimeoutError("Disposable launcher did not become ready")
    import secrets

    token = secrets.token_urlsafe(48)
    web_port, api_port = port(), port()
    while web_port == api_port:
        api_port = port()
    origin = f"http://127.0.0.1:{web_port}"
    env.update(
        AMVS_SESSION=token,
        AMVS_ORIGIN=origin,
        AMVS_API_HOST=f"127.0.0.1:{api_port}",
        AMVS_API_URL=f"http://127.0.0.1:{api_port}",
        AMVS_TEST_RUN=str(folder),
        PYTHONPATH=str(ROOT / "services/local-api"),
    )
    for name, command, cwd in [
        (
            "api",
            [
                sys.executable,
                "-m",
                "uvicorn",
                "tests.fixtures.api_server:app",
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
                "dev" if mode == "development-fixture" else "start",
                "--hostname",
                "127.0.0.1",
                "--port",
                str(web_port),
            ],
            source / "apps/web",
        ),
    ]:
        log = (folder / f"{name}.log").open("w", encoding="utf-8")
        logs.append(log)
        processes.append(
            owner.launch(command, cwd=cwd, env=env, stdout=log, stderr=subprocess.STDOUT)
        )
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    for _ in range(100):
        if any(p.poll() is not None for p in processes):
            raise RuntimeError("Disposable service exited; inspect logs")
        try:
            opener.open(f"http://127.0.0.1:{api_port}/health", timeout=1).close()
            opener.open(origin, timeout=2).close()
            return origin
        except OSError:
            time.sleep(1)
    raise TimeoutError("Disposable services did not become ready")


def stop():
    global owner
    if owner:
        owner.close()
        owner = None
    for process in processes:
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            raise RuntimeError("Owned service did not stop") from None
    for log in logs:
        log.close()
    logs.clear()


try:
    print(json.dumps({"origin": start(), "mode": mode}), flush=True)
    for line in sys.stdin:
        if line.strip() == "restart" and mode == "development":
            stop()
            print(json.dumps({"origin": start(), "mode": mode, "restarted": True}), flush=True)
        else:
            break
finally:
    stop()
