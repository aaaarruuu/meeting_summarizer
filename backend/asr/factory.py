from ..config import settings
from .base import BaseASR
from .local_whisper import LocalWhisperASR
from .openai_whisper import OpenAIWhisperASR


def get_asr_engine() -> BaseASR:
    if settings.ASR_PROVIDER == "openai":
        return OpenAIWhisperASR()
    return LocalWhisperASR(
        model_size=settings.WHISPER_MODEL_SIZE,
        device=settings.WHISPER_DEVICE,
        compute_type=settings.WHISPER_COMPUTE_TYPE,
    )
