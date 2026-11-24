from pathlib import Path
from typing import AsyncIterator, Protocol

from src.domain.entities.audio_track import AudioMessage
from src.domain.entities.channel import Channel


class TelegramClientPort(Protocol):
    """Port defining Telegram operations required by the application layer."""

    async def __aenter__(self) -> "TelegramClientPort": ...

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None: ...

    def iter_audio_messages(
        self,
        channel: Channel,
        limit: int | None = None,
    ) -> AsyncIterator[AudioMessage]:
        """Yield audio messages from the given channel."""
        ...

    async def download_audio(
        self,
        message: AudioMessage,
        destination_dir: Path,
    ) -> Path:
        """Download the audio file for a message into destination_dir and return its path."""
        ...
