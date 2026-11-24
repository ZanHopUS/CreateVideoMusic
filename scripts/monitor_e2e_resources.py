"""Sample only processes carrying one disposable E2E run id and their children."""

import json
import sys
import time
from pathlib import Path

import psutil

ROOT = Path(__file__).resolve().parents[1]


def main():
    run = Path(sys.argv[1]).resolve()
    parent_pid = int(sys.argv[2])
    assert run.is_relative_to((ROOT / ".local/e2e").resolve())
    parent = psutil.Process(parent_pid)
    created = parent.create_time()
    previous = {}
    last = time.monotonic()
    samples = 0
    summary = {
        "scope": "sampled discovered test runner/UI/API/render descendants plus monitor; unique PIDs, not a peak guarantee",
        "samples": 0,
        "peakPrivateBytes": 0,
        "minimumAvailableBytes": None,
        "environmentProbeDenied": 0,
    }
    with (run / "application-resources.jsonl").open("x", encoding="utf-8") as output:
        while samples < 2700 and not (run / "resource-monitor.stop").exists():
            try:
                if not parent.is_running() or parent.create_time() != created:
                    break
            except psutil.NoSuchProcess:
                break
            owned = {parent.pid: parent}
            try:
                for child in parent.children(recursive=True):
                    owned[child.pid] = child
            except psutil.NoSuchProcess:
                pass
            for process in psutil.process_iter(["name"]):
                if (process.info.get("name") or "").lower() not in {
                    "node.exe",
                    "python.exe",
                    "chrome-headless-shell.exe",
                }:
                    continue
                try:
                    value = process.environ().get("AMVS_TEST_RUN")
                    if value and Path(value).resolve() == run:
                        owned[process.pid] = process
                        for child in process.children(recursive=True):
                            owned[child.pid] = child
                except psutil.AccessDenied:
                    summary["environmentProbeDenied"] += 1
                except psutil.NoSuchProcess:
                    pass
            private = 0
            cpu_delta = 0
            visible = 0
            for process in owned.values():
                try:
                    mem = process.memory_info()
                    private += getattr(mem, "private", mem.rss)
                    visible += 1
                    cpu = process.cpu_times()
                    total = cpu.user + cpu.system
                    key = (process.pid, process.create_time())
                    if key in previous:
                        cpu_delta += max(0, total - previous[key])
                    previous[key] = total
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    pass
            now = time.monotonic()
            available = psutil.virtual_memory().available
            row = {
                "utcMs": round(time.time() * 1000),
                "privateBytes": private,
                "systemAvailableBytes": available,
                "visibleProcessCount": visible,
                "cpuPercentOfOneCore": cpu_delta / max(0.001, now - last) * 100,
            }
            output.write(json.dumps(row) + "\n")
            output.flush()
            last = now
            samples += 1
            summary.update(
                samples=samples,
                peakPrivateBytes=max(summary["peakPrivateBytes"], private),
                minimumAvailableBytes=available
                if summary["minimumAvailableBytes"] is None
                else min(summary["minimumAvailableBytes"], available),
            )
            if samples % 10 == 0:
                (run / "application-resources-partial.json").write_text(
                    json.dumps(summary), encoding="utf-8"
                )
            time.sleep(1)
    (run / "application-resources-summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
