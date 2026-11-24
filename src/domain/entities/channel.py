import re
from dataclasses import dataclass

_TELEGRAM_URL_RE = re.compile(r"^(?:https?://)?(?:t\.me|telegram\.me)/([^/?#]+)")


@dataclass(frozen=True, slots=True)
class Channel:
    """Represents a Telegram channel configured for audio downloads."""

    username: str
    url: str
    enabled: bool = True

    @classmethod
    def from_input(cls, raw: str, enabled: bool = True) -> "Channel":
        """Normalize a channel URL, @handle, or username into a Channel entity."""
        cleaned = raw.strip()
        if not cleaned:
            raise ValueError("Channel identifier cannot be empty.")

        match = _TELEGRAM_URL_RE.match(cleaned)
        if match:
            username = match.group(1).lstrip("@").strip()
        else:
            username = cleaned.lstrip("@").strip("/")

        if not username:
            raise ValueError(f"Invalid Telegram channel identifier: {raw!r}")

        return cls(
            username=username,
            url=f"https://t.me/{username}",
            enabled=enabled,
        )
