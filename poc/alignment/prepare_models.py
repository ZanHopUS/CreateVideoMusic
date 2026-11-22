"""Download revision-pinned alignment models and tokenizer data, no inference."""
import hashlib
import argparse
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOCAL = ROOT / ".poc"
os.environ.update({"HF_HOME": str(LOCAL / "cache/huggingface-align"),
                   "HF_HUB_DISABLE_IMPLICIT_TOKEN": "1", "HF_HUB_DISABLE_TELEMETRY": "1",
                   "HF_HUB_DISABLE_XET": "1", "DO_NOT_TRACK": "1"})


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--models-only", action="store_true")
    parser.add_argument("--tokenizer-only", action="store_true")
    args = parser.parse_args()
    if args.models_only and args.tokenizer_only:
        parser.error("Choose only one preparation scope")
    from huggingface_hub import HfApi, snapshot_download

    if not args.models_only:
        import nltk
        nltk_dir = LOCAL / "cache/nltk"
        if not nltk.download("punkt_tab", download_dir=str(nltk_dir), quiet=True):
            raise RuntimeError("Failed to prepare NLTK punkt_tab for offline alignment")
    if args.tokenizer_only:
        return
    for language, repo in {"vi": "nguyenvulebinh/wav2vec2-base-vi-vlsp2020",
                           "en": "facebook/wav2vec2-base-960h"}.items():
        pinned_revision = {"vi": "50a30dadb3ec98a0d4cdb1eb1ea315aff538f7c2",
                           "en": "22aad52d435eb6dbaf354bdad9b0da84ce7d6156"}[language]
        info = HfApi(token=False).model_info(repo, revision=pinned_revision)
        revision = info.sha
        names = {file.rfilename for file in info.siblings}
        weights = "model.safetensors" if "model.safetensors" in names else "pytorch_model.bin"
        destination = LOCAL / "models" / f"align-{language}"
        snapshot_download(repo_id=repo, revision=revision, token=False, local_dir=destination,
                          max_workers=2, allow_patterns=[weights, "config.json", "preprocessor_config.json",
                            "tokenizer_config.json", "special_tokens_map.json", "vocab.json",
                            "tokenizer.json", "README.md", "LICENSE*"] +
                            (["model_handling.py"] if language == "vi" else []))
        files = [{"path": str(path.relative_to(destination)), "bytes": path.stat().st_size,
                  "sha256": digest(path)} for path in destination.rglob("*") if path.is_file()
                 and ".cache" not in path.relative_to(destination).parts]
        evidence = LOCAL / "evidence/poc-02"
        evidence.mkdir(parents=True, exist_ok=True)
        (evidence / f"model-{language}.json").write_text(json.dumps({
            "language": language, "repo": repo, "revision": revision, "weights": weights,
            "license": "CC-BY-NC-4.0" if language == "vi" else "Apache-2.0",
            "purpose": "approved personal non-commercial PoC", "files": files,
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"language": language, "repo": repo, "revision": revision,
                          "files": len(files)}), flush=True)


if __name__ == "__main__":
    main()
