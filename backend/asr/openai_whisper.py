from typing import Any, Dict

from ..config import settings
from .base import BaseASR


class OpenAIWhisperASR(BaseASR):
    """Uses OpenAI's hosted transcription API instead of a local model.

    Useful when the machine running this app has no GPU/CPU headroom to
    spare, or you simply want the managed-service accuracy/speed trade-off.
    Requires OPENAI_API_KEY to be set.
    """

    def transcribe(self, audio_path: str) -> Dict[str, Any]:
        from openai import OpenAI

        if not settings.OPENAI_API_KEY:
            raise RuntimeError(
                "ASR_PROVIDER=openai but OPENAI_API_KEY is not set. "
                "Add it to your .env file or switch ASR_PROVIDER=local."
            )

        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        with open(audio_path, "rb") as audio_file:
            response = client.audio.transcriptions.create(
                model=settings.OPENAI_TRANSCRIBE_MODEL,
                file=audio_file,
                response_format="verbose_json",
            )

        segments = []
        for seg in getattr(response, "segments", None) or []:
            segments.append({"start": seg.start, "end": seg.end, "text": seg.text.strip()})

        return {
            "text": response.text.strip(),
            "duration": getattr(response, "duration", None),
            "segments": segments,
        }
