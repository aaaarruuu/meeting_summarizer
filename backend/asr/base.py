from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseASR(ABC):
    @abstractmethod
    def transcribe(self, audio_path: str) -> Dict[str, Any]:
        raise NotImplementedError
