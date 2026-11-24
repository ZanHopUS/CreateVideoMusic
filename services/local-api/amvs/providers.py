"""Provider boundary. Cloud adapters have no network implementation in Core."""

import os
from pathlib import Path
from typing import Protocol

from .domain import ROOT


class AIUnavailable(ValueError):
    pass


class Provider(Protocol):
    def status(self) -> dict: ...
    def runtime(self, language: str, model: str, alignment: bool = False) -> dict: ...


class LocalProvider:
    def status(self):
        model_root = Path(os.environ.get("AMVS_MODEL_ROOT", str(ROOT / ".poc/models")))
        python = Path(
            os.environ.get("AMVS_ASR_PYTHON", str(ROOT / ".poc/venv-asr/Scripts/python.exe"))
        )
        return {
            "id": "local",
            "enabled": True,
            "offline": True,
            "models": {
                name: python.is_file()
                and (model_root / ("faster-whisper-" + name) / "model.bin").is_file()
                for name in ("small", "medium")
            },
        }

    def runtime(self, language, model, alignment=False):
        if language not in {"vi", "en"} or model not in {"small", "medium"}:
            raise ValueError("Ngôn ngữ/model không hợp lệ.")
        root = Path(os.environ.get("AMVS_MODEL_ROOT", str(ROOT / ".poc/models")))
        if alignment:
            python = Path(
                os.environ.get(
                    "AMVS_ALIGN_PYTHON", str(ROOT / ".poc/venv-align/Scripts/python.exe")
                )
            )
            directory = root / ("align-" + language)
            if not python.is_file() or not directory.is_dir():
                raise AIUnavailable(
                    "Chưa chuẩn bị aligner local. Có thể giữ mốc câu và duyệt thủ công."
                )
        else:
            python = Path(
                os.environ.get("AMVS_ASR_PYTHON", str(ROOT / ".poc/venv-asr/Scripts/python.exe"))
            )
            directory = root / ("faster-whisper-" + model)
            if not python.is_file() or not (directory / "model.bin").is_file():
                raise AIUnavailable(
                    "Chưa chuẩn bị environment/model ASR local. Xem hướng dẫn cấu hình AI local."
                )
        return {
            "python": str(python),
            "modelPath": str(directory),
            "nltkPath": str(ROOT / ".poc/cache/nltk"),
        }


class DisabledProvider:
    def __init__(self, id):
        self.id = id

    def status(self):
        return {
            "id": self.id,
            "enabled": False,
            "reason": "Cloud AI chưa được bật; không có egress hoặc chi phí API.",
        }

    def runtime(self, *args, **kwargs):
        raise AIUnavailable("Provider cloud đang tắt. Dùng AI local hoặc nhập lời thủ công.")


PROVIDERS: dict[str, Provider] = {
    "local": LocalProvider(),
    "gemini": DisabledProvider("gemini"),
    "openai": DisabledProvider("openai"),
}


def provider(id="local"):
    if not isinstance(id, str) or id not in PROVIDERS:
        raise ValueError("Provider không hợp lệ.")
    return PROVIDERS[id]
