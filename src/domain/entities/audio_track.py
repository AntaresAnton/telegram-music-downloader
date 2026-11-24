from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class DownloadStatus(str, Enum):
    """Outcome status of an audio download attempt."""

    DOWNLOADED = "downloaded"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class AudioMessage:
    """Represents an audio file discovered in a Telegram channel message."""

    channel: str
    message_id: int
    file_name: str
    title: str | None = None
    performer: str | None = None
    duration_seconds: int | None = None
    file_size_bytes: int | None = None
    mime_type: str | None = None
    message_date: datetime | None = None
    caption: str | None = None


@dataclass(frozen=True, slots=True)
class DownloadRecord:
    """Represents a persisted log entry for a processed audio file."""

    channel: str
    message_id: int
    file_name: str
    file_path: str | None
    status: DownloadStatus
    downloaded_at: datetime
    title: str | None = None
    performer: str | None = None
    duration_seconds: int | None = None
    file_size_bytes: int | None = None
    mime_type: str | None = None
    error: str | None = None
