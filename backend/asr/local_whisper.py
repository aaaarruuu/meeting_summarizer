from typing import Any, Dict

from .base import BaseASR


class LocalWhisperASR(BaseASR):
    """Runs OpenAI's Whisper model locally via faster-whisper (CTranslate2).

    No API key and no internet access required at inference time (only the
    first run needs internet, to download model weights once). This keeps
    the project runnable offline and free, while still using the exact
    model family the assignment names.
    """

    # Shared across instances so the (potentially large) model is only
    # loaded into memory once per process.
    _model = None
    _model_key = None

    def __init__(self, model_size: str = "base", device: str = "cpu", compute_type: str = "int8"):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type

    def _load_model(self):
        key = (self.model_size, self.device, self.compute_type)
        if LocalWhisperASR._model is None or LocalWhisperASR._model_key != key:
            from faster_whisper import WhisperModel

            LocalWhisperASR._model = WhisperModel(
                self.model_size, device=self.device, compute_type=self.compute_type
            )
            LocalWhisperASR._model_key = key
        return LocalWhisperASR._model

    def transcribe(self, audio_path: str) -> Dict[str, Any]:
        model = self._load_model()
        segments_iter, info = model.transcribe(audio_path, beam_size=5)

        segments = []
        text_parts = []
        for seg in segments_iter:
            clean_text = seg.text.strip()
            segments.append({"start": seg.start, "end": seg.end, "text": clean_text})
            text_parts.append(clean_text)

        return {
            "text": " ".join(text_parts).strip(),
            "duration": info.duration,
            "segments": segments,
        }
