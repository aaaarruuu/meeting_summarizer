import json
import re
from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseSummarizer(ABC):
    @abstractmethod
    def summarize(self, transcript: str) -> Dict[str, Any]:
        raise NotImplementedError


def parse_json_response(content: str) -> Dict[str, Any]:
    content = content.strip()
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", content, re.DOTALL)
    if fenced:
        return json.loads(fenced.group(1))

    start, end = content.find("{"), content.rfind("}")
    if start != -1 and end != -1 and end > start:
        return json.loads(content[start : end + 1])

    raise ValueError(f"Could not parse a JSON object out of the model's response: {content[:200]!r}")
