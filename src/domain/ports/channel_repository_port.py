from typing import Protocol

from src.domain.entities.channel import Channel


class ChannelRepositoryPort(Protocol):
    """Port for reading and managing configured Telegram channels."""

    def list_enabled_channels(self) -> list[Channel]:
        """Return all enabled channels."""
        ...

    def add_channel(self, channel: Channel) -> None:
        """Add or update a channel in the repository."""
        ...
