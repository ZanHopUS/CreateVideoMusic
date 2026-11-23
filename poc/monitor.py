"""Bound a disposable PoC child process and record its process-tree resources."""
import argparse
import json
from pathlib import Path
import subprocess
import time

import psutil


GIB = 1024**3


def admission(minimum_bytes, required_samples, timeout, *, available=None,
              now=time.monotonic, sleep=time.sleep):
    """Observe consecutive headroom samples before starting any workload."""
    available = available or (lambda: psutil.virtual_memory().available)
    started = now()
    samples, consecutive = [], 0
    while True:
        elapsed = now() - started
        free = available()
        consecutive = consecutive + 1 if free >= minimum_bytes else 0
        samples.append({'elapsed_s': elapsed, 'system_available_bytes': free})
        if consecutive >= required_samples:
            return {'allowed': True, 'samples': samples}
        if elapsed >= timeout:
            return {'allowed': False, 'samples': samples}
        sleep(min(1, timeout - elapsed))


def sampled_r0(samples, reason, code):
    # Sampling cannot prove absence of transient peaks or page thrashing.
    return bool(samples) and reason is None and code == 0 and all(
        row['private_bytes'] <= 12 * GIB and row['system_available_bytes'] >= 2 * GIB
        for row in samples)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=900)
    parser.add_argument("--min-start-available-gib", type=float, default=0)
    parser.add_argument("--start-samples", type=int, default=10)
    parser.add_argument("--admission-timeout", type=float, default=30)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("A child command is required")
    if not (0 <= args.min_start_available_gib <= 1024 and args.start_samples >= 1
            and 0 <= args.admission_timeout <= 300 and args.timeout > 0):
        parser.error('Invalid resource thresholds/timeouts')
    args.out.mkdir(parents=True, exist_ok=True)
    if args.min_start_available_gib:
        # Refuse evidence overwrite and never launch on stale or partial admission.
        if any((args.out / name).exists() for name in ('admission.json', 'resources.json', 'stdout.log', 'stderr.log')):
            parser.error('Admission runs require a fresh output directory')
        decision = admission(args.min_start_available_gib * GIB, args.start_samples,
                             args.admission_timeout)
        decision.update({'command': command, 'minimum_available_gib': args.min_start_available_gib,
                         'required_consecutive_samples': args.start_samples,
                         'timeout_s': args.admission_timeout,
                         'scope': 'PoC admission only; does not guarantee R0 during execution'})
        (args.out / 'admission.json').write_text(json.dumps(decision, indent=2), encoding='utf-8')
        if not decision['allowed']:
            print(json.dumps({'started': False, 'reason': 'insufficient stable RAM headroom'}))
            raise SystemExit(4)
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
                      "wall_s": time.monotonic() - start, "samples": samples,
                      "r0_sampled_pass": sampled_r0(samples, reason, code)}
            (args.out / "resources.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("exit_code", "abort_reason", "wall_s")}))
    raise SystemExit(3 if reason else code)


if __name__ == "__main__":
    main()
