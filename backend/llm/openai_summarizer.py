from typing import Any, Dict

from ..config import settings
from .base import BaseSummarizer, parse_json_response
from .prompts import SYSTEM_PROMPT, build_user_prompt


class OpenAISummarizer(BaseSummarizer):
    def summarize(self, transcript: str) -> Dict[str, Any]:
        from openai import OpenAI

        if not settings.OPENAI_API_KEY:
            raise RuntimeError(
                "LLM_PROVIDER=openai but OPENAI_API_KEY is not set. "
                "Add it to your .env file or switch LLM_PROVIDER=anthropic."
            )

        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_prompt(transcript)},
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        return parse_json_response(content)
