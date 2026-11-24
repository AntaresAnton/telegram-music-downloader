from typing import Protocol

from src.domain.entities.audio_track import DownloadRecord


class DownloadLogPort(Protocol):
    """Port for querying and persisting audio download history."""

    def is_downloaded(self, channel: str, message_id: int) -> bool:
        """Return True if the message from the given channel was already downloaded."""
        ...

    def record(self, entry: DownloadRecord) -> None:
        """Persist a download record."""
        ...

    def get_all(self) -> list[DownloadRecord]:
        """Return all recorded download entries."""
        ...
