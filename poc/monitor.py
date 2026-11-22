"""Bound a disposable PoC child process and record its process-tree resources."""
import argparse
import json
from pathlib import Path
import subprocess
import time

import psutil


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=900)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("A child command is required")
    args.out.mkdir(parents=True, exist_ok=True)
    samples, reason, low_since = [], None, None
    start = time.monotonic()
    with (args.out / "stdout.log").open("w", encoding="utf-8") as stdout, \
         (args.out / "stderr.log").open("w", encoding="utf-8") as stderr:
        child = subprocess.Popen(command, stdout=stdout, stderr=stderr)
        root = psutil.Process(child.pid)
        try:
            while child.poll() is None:
                now = time.monotonic()
                private = rss = 0
                members = [root, *root.children(recursive=True)]
                for member in members:
                    try:
                        mem = member.memory_info()
                        private += getattr(mem, "private", mem.vms)
                        rss += mem.rss
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                available = psutil.virtual_memory().available
                samples.append({"elapsed_s": now - start, "private_bytes": private,
                                "rss_bytes": rss, "system_available_bytes": available,
                                "process_count": len(members)})
                low_since = (low_since or now) if available < 2 * 1024**3 else None
                if private > 12 * 1024**3:
                    reason = "workload private bytes >12GiB"
                elif low_since is not None and now - low_since >= 10:
                    reason = "system available memory <2GiB for 10 seconds"
                elif now - start > args.timeout:
                    reason = "timebox exceeded"
                if reason:
                    for member in reversed(members):
                        try:
                            member.kill()
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                    break
                time.sleep(1)
        finally:
            code = child.wait(timeout=30)
            result = {"command": command, "exit_code": code, "abort_reason": reason,
                      "wall_s": time.monotonic() - start, "samples": samples}
            (args.out / "resources.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("exit_code", "abort_reason", "wall_s")}))
    raise SystemExit(3 if reason else code)


if __name__ == "__main__":
    main()
