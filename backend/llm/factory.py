from ..config import settings

from .anthropic_summarizer import AnthropicSummarizer
from .base import BaseSummarizer
from .openai_summarizer import OpenAISummarizer
from .local_summarizer import LocalSummarizer


def get_summarizer() -> BaseSummarizer:

    """Returns the configured LLM summarizer."""

    if settings.LLM_PROVIDER == "local":
        return LocalSummarizer()

    if settings.LLM_PROVIDER == "anthropic":
        return AnthropicSummarizer()

    return OpenAISummarizer()