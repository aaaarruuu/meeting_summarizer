from typing import Any, Dict

from ..config import settings
from .base import BaseSummarizer, parse_json_response
from .prompts import SYSTEM_PROMPT, build_user_prompt


class AnthropicSummarizer(BaseSummarizer):
    def summarize(self, transcript: str) -> Dict[str, Any]:
        import anthropic

        if not settings.ANTHROPIC_API_KEY:
            raise RuntimeError(
                "LLM_PROVIDER=anthropic but ANTHROPIC_API_KEY is not set. "
                "Add it to your .env file or switch LLM_PROVIDER=openai."
            )

        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        message = client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=1500,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": build_user_prompt(transcript)}],
        )
        content = "".join(block.text for block in message.content if block.type == "text")
        return parse_json_response(content)
