import asyncio
from pathlib import Path
from typing import AsyncIterator

from src.application.use_cases.download_channel_audios import DownloadChannelAudiosUseCase
from src.domain.entities.audio_track import AudioMessage, DownloadStatus
from src.domain.entities.channel import Channel
from src.infrastructure.persistence.json_download_log import JsonDownloadLog


class FakeTelegramClient:
    def __init__(self, messages: list[AudioMessage], fail_ids: set[int] | None = None) -> None:
        self._messages = messages
        self._fail_ids = fail_ids or set()
        self.downloaded_ids: list[int] = []

    async def __aenter__(self) -> "FakeTelegramClient":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        return None

    async def iter_audio_messages(
        self,
        channel: Channel,
        limit: int | None = None,
    ) -> AsyncIterator[AudioMessage]:
        items = self._messages[:limit] if limit is not None else self._messages
        for msg in items:
            yield msg

    async def download_audio(self, message: AudioMessage, destination_dir: Path) -> Path:
        if message.message_id in self._fail_ids:
            raise RuntimeError("Simulated network error")
        self.downloaded_ids.append(message.message_id)
        out = destination_dir / message.file_name
        out.write_bytes(b"fake-audio-bytes")
        return out


def test_download_use_case_and_idempotency(tmp_path: Path) -> None:
    channel = Channel.from_input("https://t.me/deathmetal2")
    messages = [
        AudioMessage(
            channel="deathmetal2", message_id=101, file_name="track1.mp3", title="Track 1"
        ),
        AudioMessage(
            channel="deathmetal2", message_id=102, file_name="track2.flac", title="Track 2"
        ),
    ]
    log_path = tmp_path / "logs" / "downloads_log.json"
    downloads_root = tmp_path / "downloads"

    fake_tg = FakeTelegramClient(messages)
    log = JsonDownloadLog(log_path)
    use_case = DownloadChannelAudiosUseCase(fake_tg, log, downloads_root)

    summary_first = asyncio.run(use_case.execute(channel))
    assert summary_first.total_seen == 2
    assert summary_first.downloaded == 2
    assert summary_first.skipped == 0
    assert summary_first.failed == 0
    assert (downloads_root / "deathmetal2" / "track1.mp3").exists()
    assert (downloads_root / "deathmetal2" / "track2.flac").exists()

    # Second run with a fresh log instance should skip both already-downloaded messages
    log_reloaded = JsonDownloadLog(log_path)
    fake_tg_second = FakeTelegramClient(messages)
    use_case_second = DownloadChannelAudiosUseCase(fake_tg_second, log_reloaded, downloads_root)

    summary_second = asyncio.run(use_case_second.execute(channel))
    assert summary_second.total_seen == 2
    assert summary_second.downloaded == 0
    assert summary_second.skipped == 2
    assert summary_second.failed == 0
    assert fake_tg_second.downloaded_ids == []


def test_download_use_case_records_failures_and_continues(tmp_path: Path) -> None:
    channel = Channel.from_input("deathmetal2")
    messages = [
        AudioMessage(channel="deathmetal2", message_id=1, file_name="bad.mp3"),
        AudioMessage(channel="deathmetal2", message_id=2, file_name="good.mp3"),
    ]
    log_path = tmp_path / "logs" / "downloads_log.json"
    downloads_root = tmp_path / "downloads"

    fake_tg = FakeTelegramClient(messages, fail_ids={1})
    log = JsonDownloadLog(log_path)
    use_case = DownloadChannelAudiosUseCase(fake_tg, log, downloads_root)

    summary = asyncio.run(use_case.execute(channel))
    assert summary.total_seen == 2
    assert summary.downloaded == 1
    assert summary.failed == 1
    assert not log.is_downloaded("deathmetal2", 1)
    assert log.is_downloaded("deathmetal2", 2)

    records = {r.message_id: r for r in log.get_all()}
    assert records[1].status == DownloadStatus.FAILED
    assert "Simulated network error" in (records[1].error or "")
    assert records[2].status == DownloadStatus.DOWNLOADED


def test_download_use_case_respects_concurrency_pool(tmp_path: Path) -> None:
    channel = Channel.from_input("deathmetal2")
    messages = [
        AudioMessage(channel="deathmetal2", message_id=i, file_name=f"track_{i}.mp3")
        for i in range(1, 7)
    ]

    class ConcurrentFakeTelegramClient(FakeTelegramClient):
        def __init__(self, msgs: list[AudioMessage]) -> None:
            super().__init__(msgs)
            self.active = 0
            self.max_active = 0

        async def download_audio(self, message: AudioMessage, destination_dir: Path) -> Path:
            self.active += 1
            self.max_active = max(self.max_active, self.active)
            try:
                await asyncio.sleep(0.02)
                return await super().download_audio(message, destination_dir)
            finally:
                self.active -= 1

    fake_tg = ConcurrentFakeTelegramClient(messages)
    log = JsonDownloadLog(tmp_path / "logs" / "downloads_log.json")
    use_case = DownloadChannelAudiosUseCase(fake_tg, log, tmp_path / "downloads")

    summary = asyncio.run(use_case.execute(channel, concurrency=3))
    assert summary.downloaded == 6
    assert fake_tg.max_active == 3
