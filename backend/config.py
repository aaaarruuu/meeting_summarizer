import os

from dotenv import load_dotenv

load_dotenv()


def _bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Settings:
    ASR_PROVIDER: str = os.getenv("ASR_PROVIDER", "local")

    WHISPER_MODEL_SIZE: str = os.getenv("WHISPER_MODEL_SIZE", "base")
    WHISPER_DEVICE: str = os.getenv("WHISPER_DEVICE", "cpu")
    WHISPER_COMPUTE_TYPE: str = os.getenv("WHISPER_COMPUTE_TYPE", "int8")

    OPENAI_TRANSCRIBE_MODEL: str = os.getenv("OPENAI_TRANSCRIBE_MODEL", "whisper-1")

    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "local")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5")

    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

    STORAGE_DIR: str = os.getenv("STORAGE_DIR", "storage")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./meetings.db")

    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "*")
    MAX_UPLOAD_MB: int = int(os.getenv("MAX_UPLOAD_MB", "200"))


settings = Settings()
