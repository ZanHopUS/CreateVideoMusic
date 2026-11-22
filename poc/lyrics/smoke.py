"""Local CPU executable smoke, using generated non-vocal controls only.

This is NOT a singing accuracy benchmark or an instrumental detection test.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import random
import struct
import threading
import time
import wave

ROOT = Path(__file__).resolve().parents[2]
LOCAL = ROOT / ".poc"
os.environ.update({"HF_HUB_OFFLINE": "1", "HF_HUB_DISABLE_TELEMETRY": "1",
                   "HF_HUB_DISABLE_IMPLICIT_TOKEN": "1", "DO_NOT_TRACK": "1"})


def fixtures():
    directory = LOCAL / "data" / "generated"
    directory.mkdir(parents=True, exist_ok=True)
    rate, seconds = 16000, 20
    rng = random.Random(42)
    generators = {
        "silence": lambda i: 0,
        "tone": lambda i: int(0.05 * 32767 * math.sin(2 * math.pi * 440 * i / rate)),
        "noise": lambda i: int(rng.uniform(-0.02, 0.02) * 32767),
    }
    paths = []
    for name, generate in generators.items():
        path = directory / f"{name}.wav"
        with wave.open(str(path), "wb") as output:
            output.setparams((1, 2, rate, 0, "NONE", "not compressed"))
            output.writeframes(b"".join(struct.pack("<h", generate(i)) for i in range(rate * seconds)))
        paths.append((name, path, seconds))
    return paths


def main():
    import psutil
    from faster_whisper import WhisperModel

    directory = LOCAL / "evidence" / "poc-01" / "generated-smoke"
    directory.mkdir(parents=True, exist_ok=True)
    samples, errors = [], []
    done = threading.Event()
    unsafe = threading.Event()
    process = psutil.Process()

    def monitor():
        low_since = None
        while not done.is_set():
            timestamp = time.perf_counter()
            available = psutil.virtual_memory().available
            private = rss = 0
            for item in [process, *process.children(recursive=True)]:
                try:
                    memory = item.memory_info()
                    private += getattr(memory, "private", memory.vms)
                    rss += memory.rss
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            samples.append({"elapsed_s": timestamp - started, "private_bytes": private,
                            "rss_bytes": rss, "system_available_bytes": available})
            low_since = (low_since or timestamp) if available < 2 * 1024**3 else None
            if private > 12 * 1024**3 or (low_since is not None and timestamp - low_since >= 10):
                unsafe.set()
                (directory / "resource-abort.json").write_text(
                    json.dumps(samples[-1]), encoding="utf-8")
                # Inference can block native threads; terminate this disposable PoC process.
                os._exit(3)
            done.wait(1)

    started = time.perf_counter()
    watcher = threading.Thread(target=monitor, daemon=True)
    watcher.start()
    results = []
    try:
        controls = fixtures()
        load_started = time.perf_counter()
        model = WhisperModel(str(LOCAL / "models" / "faster-whisper-small"),
                             device="cpu", compute_type="int8", cpu_threads=4,
                             num_workers=1, local_files_only=True)
        load_seconds = time.perf_counter() - load_started
        for name, path, duration in controls:
            for language in ("vi", "en"):
                for vad in (False, True):
                    if unsafe.is_set():
                        raise RuntimeError("Resource gate exceeded")
                    run_started = time.perf_counter()
                    segments, info = model.transcribe(str(path), language=language,
                                                      beam_size=5, vad_filter=vad,
                                                      condition_on_previous_text=False)
                    output = [{"start": s.start, "end": s.end, "text": s.text,
                               "avg_logprob": s.avg_logprob, "no_speech_prob": s.no_speech_prob}
                              for s in segments]
                    wall = time.perf_counter() - run_started
                    result = {"sample": name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                              "origin": "generated locally; no lyrics or third-party recording",
                              "language": language, "vad_filter": vad, "duration_s": duration,
                              "inference_s": wall, "rtf": wall / duration, "segments": output,
                              "review_required": True, "automatically_applied": False}
                    results.append(result)
                    print(json.dumps({k: result[k] for k in (
                        "sample", "language", "vad_filter", "inference_s", "rtf")}), flush=True)
                    (directory / "partial-results.json").write_text(
                        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:
        errors.append({"type": type(exc).__name__, "message": str(exc)})
        raise
    finally:
        done.set()
        watcher.join(timeout=2)
        report = {"scope": "executable smoke only; no singing quality evidence",
                  "offline_flags": True, "network_isolation": "not independently enforced",
                  "device": "cpu", "compute_type": "int8", "threads": 4, "beam_size": 5,
                  "model_load_s": locals().get("load_seconds"), "results": results,
                  "errors": errors, "resource_samples": samples}
        (directory / "results.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
