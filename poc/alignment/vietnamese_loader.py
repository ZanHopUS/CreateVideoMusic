"""Load the checkpoint author's audited architecture, with an exact source hash.

Source: nguyenvulebinh/wav2vec2-base-vi-vlsp2020, revision
50a30dadb3ec98a0d4cdb1eb1ea315aff538f7c2/model_handling.py.
The reviewed module contains imports and a model class; no download/IO entrypoint.
It is prepared explicitly, never fetched or trusted implicitly during inference.
"""
import hashlib
import importlib.util
from pathlib import Path

AUTHOR_SOURCE_SHA256 = "ed4178006be431a3f5b51558ec36e3e3557d51dd83e181d5c0d91c312537f83b"


def verify_source(source):
    source = Path(source)
    actual = hashlib.sha256(source.read_bytes()).hexdigest()
    if actual != AUTHOR_SOURCE_SHA256:
        raise RuntimeError("Vietnamese model source differs from the reviewed pinned source")
    return actual


def load(model_directory):
    directory = Path(model_directory)
    source = directory / "model_handling.py"
    actual = verify_source(source)
    from transformers import Wav2Vec2Processor

    spec = importlib.util.spec_from_file_location("poc_reviewed_vietnamese_model", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    processor = Wav2Vec2Processor.from_pretrained(str(directory), local_files_only=True)
    model, loading = module.Wav2Vec2ForCTC.from_pretrained(
        str(directory), local_files_only=True, weights_only=True, output_loading_info=True)
    if any(loading.get(key) for key in ("missing_keys", "unexpected_keys", "mismatched_keys", "error_msgs")):
        raise RuntimeError(f"Checkpoint architecture mismatch: {loading}")
    model.to("cpu").eval()
    metadata = {"language": "vi", "type": "huggingface",
                "dictionary": {char.lower(): code for char, code in processor.tokenizer.get_vocab().items()}}
    return model, metadata, {"source_sha256": actual, "loading_info": loading,
                             "model_eval_mode": not model.training}
