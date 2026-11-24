import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True, slots=True)
class Settings:
    """Application settings loaded from environment variables and defaults."""

    telegram_api_id: int
    telegram_api_hash: str
    telegram_session_name: str
    ai_provider: str | None
    together_api_key: str | None
    together_model: str | None
    ollama_base_url: str | None
    ollama_model: str | None
    downloads_dir: Path
    logs_file: Path
    channels_file: Path

    @classmethod
    def from_env(cls, env_path: Path | None = None, base_dir: Path | None = None) -> "Settings":
        """Load settings from a .env file and environment variables."""
        root = base_dir or Path.cwd()
        load_dotenv(dotenv_path=env_path or (root / ".env"))

        raw_api_id = os.getenv("API_ID", "").strip()
        raw_api_hash = os.getenv("API_HASH", "").strip()

        if not raw_api_id:
            raise ValueError("Missing API_ID in environment or .env file.")
        try:
            api_id = int(raw_api_id)
        except ValueError as exc:
            raise ValueError("API_ID must be a valid integer.") from exc

        if not raw_api_hash:
            raise ValueError("Missing API_HASH in environment or .env file.")

        session_name = (
            os.getenv("SESSION_NAME", "telegram_audio_session").strip() or "telegram_audio_session"
        )

        return cls(
            telegram_api_id=api_id,
            telegram_api_hash=raw_api_hash,
            telegram_session_name=session_name,
            ai_provider=os.getenv("AI_PROVIDER") or None,
            together_api_key=os.getenv("TOGETHER_API_KEY") or None,
            together_model=os.getenv("TOGETHER_MODEL") or None,
            ollama_base_url=os.getenv("OLLAMA_BASE_URL") or None,
            ollama_model=os.getenv("OLLAMA_MODEL") or None,
            downloads_dir=root / "downloads",
            logs_file=root / "logs" / "downloads_log.json",
            channels_file=root / "config" / "channels.json",
        )
