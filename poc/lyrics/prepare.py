"""Prepare a local-only ASR PoC; downloads occur only with --download-model."""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import winreg

ROOT = Path(__file__).resolve().parents[2]
LOCAL = ROOT / ".poc"
for name, value in {
    "HF_HOME": str(LOCAL / "cache" / "huggingface"),
    "HF_HUB_DISABLE_IMPLICIT_TOKEN": "1",
    "HF_HUB_DISABLE_TELEMETRY": "1",
    "HF_HUB_DISABLE_XET": "1",
    "DO_NOT_TRACK": "1",
}.items():
    os.environ[name] = value


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--download-model", action="store_true")
    args = parser.parse_args()
    import imageio_ffmpeg
    import psutil

    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                        r"HARDWARE\DESCRIPTION\System\CentralProcessor\0") as key:
        cpu = winreg.QueryValueEx(key, "ProcessorNameString")[0]
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    version = subprocess.run([ffmpeg, "-version"], capture_output=True, text=True, check=True)
    memory = psutil.virtual_memory()
    environment = {
        "platform": platform.platform(), "cpu": cpu,
        "logical_cpus": psutil.cpu_count(), "physical_cpus": psutil.cpu_count(logical=False),
        "ram_total_bytes": memory.total, "ram_available_bytes": memory.available,
        "workspace_disk_free_bytes": shutil.disk_usage(ROOT).free,
        "python": platform.python_version(),
        "packages": {dist.metadata["Name"]: dist.version for dist in importlib.metadata.distributions()},
        "ffmpeg_path": str(Path(ffmpeg).relative_to(ROOT)),
        "ffmpeg_version": version.stdout, "inference_device": "cpu",
        "gpu_requirement": "none; browser rendering not tested",
        "cloud_inference": False,
    }
    save(LOCAL / "evidence" / "poc-00" / "environment.json", environment)
    print(json.dumps({key: environment[key] for key in (
        "platform", "cpu", "ram_total_bytes", "ram_available_bytes", "python")}, indent=2))
    print(version.stdout.splitlines()[0])
    if not args.download_model:
        return
    if memory.available < 2 * 1024**3 or shutil.disk_usage(ROOT).free < 3 * 1024**3:
        raise RuntimeError("Insufficient available RAM/disk for model preparation")
    from huggingface_hub import HfApi, snapshot_download

    repo = "Systran/faster-whisper-small"
    info = HfApi(token=False).model_info(repo)
    revision = info.sha
    destination = LOCAL / "models" / "faster-whisper-small"
    snapshot_download(repo_id=repo, revision=revision, token=False,
                      local_dir=destination, max_workers=2,
                      allow_patterns=["model.bin", "config.json", "tokenizer.json",
                                      "vocabulary.*", "preprocessor_config.json", "README.md"])
    inventory = [{"path": str(path.relative_to(destination)), "bytes": path.stat().st_size,
                  "sha256": sha256(path)} for path in destination.rglob("*")
                 if path.is_file() and ".cache" not in path.relative_to(destination).parts]
    save(LOCAL / "evidence" / "poc-00" / "model-inventory.json",
         {"repo": repo, "revision": revision, "files": inventory,
          "license_source": f"https://huggingface.co/{repo}/blob/{revision}/README.md"})
    print(json.dumps({"repo": repo, "revision": revision, "files": len(inventory)}))


if __name__ == "__main__":
    main()
