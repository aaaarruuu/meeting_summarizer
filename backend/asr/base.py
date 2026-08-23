from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseASR(ABC):
    """Common interface every speech-to-text backend implements.

    Swapping providers (local Whisper, OpenAI's API, Azure, Google, ...)
    only ever means adding one more class here plus a branch in
    `factory.get_asr_engine`. Nothing else in the app needs to change.
    """

    @abstractmethod
    def transcribe(self, audio_path: str) -> Dict[str, Any]:
        """Transcribe the audio file at `audio_path`.

        Returns:
            {
                "text": str,                 # full transcript
                "duration": float | None,    # audio duration in seconds
                "segments": [                # optional timestamped segments
                    {"start": float, "end": float, "text": str}, ...
                ],
            }
        """
        raise NotImplementedError
