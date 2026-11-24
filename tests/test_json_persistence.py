from datetime import datetime, timezone
from pathlib import Path

from src.domain.entities.audio_track import DownloadRecord, DownloadStatus
from src.domain.entities.channel import Channel
from src.infrastructure.persistence.json_channel_repository import JsonChannelRepository
from src.infrastructure.persistence.json_download_log import JsonDownloadLog


def test_json_download_log_persistence(tmp_path: Path) -> None:
    log_path = tmp_path / "downloads_log.json"
    log = JsonDownloadLog(log_path)

    record = DownloadRecord(
        channel="deathmetal2",
        message_id=42,
        file_name="band - song.mp3",
        file_path=str(tmp_path / "band - song.mp3"),
        status=DownloadStatus.DOWNLOADED,
        downloaded_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        title="Song",
        performer="Band",
        duration_seconds=215,
        file_size_bytes=5_000_000,
        mime_type="audio/mpeg",
    )
    log.record(record)

    reloaded = JsonDownloadLog(log_path)
    assert reloaded.is_downloaded("deathmetal2", 42) is True
    assert reloaded.is_downloaded("deathmetal2", 99) is False
    all_records = reloaded.get_all()
    assert len(all_records) == 1
    assert all_records[0].title == "Song"


def test_json_channel_repository_add_and_deduplicate(tmp_path: Path) -> None:
    cfg_path = tmp_path / "channels.json"
    repo = JsonChannelRepository(cfg_path)

    repo.add_channel(Channel.from_input("https://t.me/deathmetal2"))
    repo.add_channel(Channel.from_input("@otherchannel"))
    repo.add_channel(Channel.from_input("deathmetal2"))

    channels = repo.list_enabled_channels()
    usernames = [c.username for c in channels]
    assert usernames == ["otherchannel", "deathmetal2"]
