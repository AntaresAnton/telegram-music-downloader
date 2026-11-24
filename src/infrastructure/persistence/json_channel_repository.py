import json
import os
from pathlib import Path

from src.domain.entities.channel import Channel


class JsonChannelRepository:
    """JSON-backed repository for configured Telegram channels."""

    def __init__(self, config_path: Path) -> None:
        self._config_path = config_path

    def _read_all(self) -> list[Channel]:
        if not self._config_path.exists():
            return []

        raw = self._config_path.read_text(encoding="utf-8").strip()
        if not raw:
            return []

        payload = json.loads(raw)
        channels: list[Channel] = []
        for item in payload.get("channels", []):
            raw_id = item.get("url") or item.get("username", "")
            channels.append(
                Channel.from_input(
                    raw_id,
                    enabled=bool(item.get("enabled", True)),
                )
            )
        return channels

    def list_enabled_channels(self) -> list[Channel]:
        return [ch for ch in self._read_all() if ch.enabled]

    def add_channel(self, channel: Channel) -> None:
        channels = self._read_all()
        updated = [ch for ch in channels if ch.username.lower() != channel.username.lower()]
        updated.append(channel)

        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "channels": [
                {
                    "username": ch.username,
                    "url": ch.url,
                    "enabled": ch.enabled,
                }
                for ch in updated
            ]
        }
        tmp_path = self._config_path.with_suffix(".json.tmp")
        tmp_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp_path, self._config_path)
