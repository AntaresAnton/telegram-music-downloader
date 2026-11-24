from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

from telethon.tl.types import DocumentAttributeAudio, DocumentAttributeFilename

from src.infrastructure.telegram.telethon_downloader import TelethonAudioDownloader


def _make_fake_message(
    msg_id: int,
    mime_type: str,
    attributes: list[object],
    size: int = 1024,
) -> SimpleNamespace:
    doc = SimpleNamespace(mime_type=mime_type, attributes=attributes, size=size)
    return SimpleNamespace(
        id=msg_id,
        document=doc,
        date=datetime(2026, 1, 1, tzinfo=timezone.utc),
        message="Album info",
    )


def test_extract_audio_metadata_valid_mp3() -> None:
    downloader = TelethonAudioDownloader(api_id=1, api_hash="hash", session_name="test_sess")
    msg = _make_fake_message(
        msg_id=10,
        mime_type="audio/mpeg",
        attributes=[
            DocumentAttributeFilename("01 - Song.mp3"),
            DocumentAttributeAudio(duration=180, title="Song", performer="Band"),
        ],
    )
    meta = downloader._extract_audio_metadata("deathmetal2", msg)
    assert meta is not None
    assert meta.file_name == "01 - Song.mp3"
    assert meta.title == "Song"
    assert meta.performer == "Band"
    assert meta.duration_seconds == 180


def test_extract_audio_metadata_skips_non_audio_document() -> None:
    downloader = TelethonAudioDownloader(api_id=1, api_hash="hash", session_name="test_sess")
    msg = _make_fake_message(
        msg_id=11,
        mime_type="image/jpeg",
        attributes=[DocumentAttributeFilename("cover.jpg")],
    )
    assert downloader._extract_audio_metadata("deathmetal2", msg) is None


def test_resolve_target_path_avoids_concurrent_collisions(tmp_path: Path) -> None:
    downloader = TelethonAudioDownloader(api_id=1, api_hash="hash", session_name="test_sess")
    p1 = downloader._resolve_target_path(tmp_path, "track.mp3", message_id=1)
    p2 = downloader._resolve_target_path(tmp_path, "track.mp3", message_id=2)
    assert p1 == tmp_path / "track.mp3"
    assert p2 == tmp_path / "track_2.mp3"
