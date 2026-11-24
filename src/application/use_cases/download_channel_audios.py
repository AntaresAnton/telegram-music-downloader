import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from src.domain.entities.audio_track import AudioMessage, DownloadRecord, DownloadStatus
from src.domain.entities.channel import Channel
from src.domain.ports.download_log_port import DownloadLogPort
from src.domain.ports.telegram_client_port import TelegramClientPort

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class DownloadSummary:
    """Summary of a channel download execution."""

    channel: str
    total_seen: int
    downloaded: int
    skipped: int
    failed: int


class DownloadChannelAudiosUseCase:
    """Downloads all new audio files from a Telegram channel and logs each result."""

    def __init__(
        self,
        telegram_client: TelegramClientPort,
        download_log: DownloadLogPort,
        downloads_root: Path,
    ) -> None:
        self._telegram_client = telegram_client
        self._download_log = download_log
        self._downloads_root = downloads_root

    async def execute(
        self,
        channel: Channel,
        limit: int | None = None,
        concurrency: int = 3,
    ) -> DownloadSummary:
        """Iterate over channel audio messages and download new files using a worker pool."""
        if concurrency < 1:
            raise ValueError("concurrency must be at least 1.")

        target_dir = self._downloads_root / channel.username
        target_dir.mkdir(parents=True, exist_ok=True)

        total_seen = 0
        downloaded = 0
        skipped = 0
        failed = 0
        semaphore = asyncio.Semaphore(concurrency)
        tasks: list[asyncio.Task[None]] = []

        async def _process_one(audio_msg: AudioMessage) -> None:
            nonlocal downloaded, failed
            try:
                now = datetime.now(timezone.utc)
                try:
                    saved_path = await self._telegram_client.download_audio(audio_msg, target_dir)
                    self._download_log.record(
                        DownloadRecord(
                            channel=channel.username,
                            message_id=audio_msg.message_id,
                            file_name=saved_path.name,
                            file_path=str(saved_path),
                            status=DownloadStatus.DOWNLOADED,
                            downloaded_at=now,
                            title=audio_msg.title,
                            performer=audio_msg.performer,
                            duration_seconds=audio_msg.duration_seconds,
                            file_size_bytes=audio_msg.file_size_bytes,
                            mime_type=audio_msg.mime_type,
                        )
                    )
                    downloaded += 1
                    logger.info("Downloaded [%s] %s", channel.username, saved_path.name)
                except Exception as exc:
                    failed += 1
                    logger.exception(
                        "Failed downloading message_id=%s from channel=%s: %s",
                        audio_msg.message_id,
                        channel.username,
                        exc,
                    )
                    self._download_log.record(
                        DownloadRecord(
                            channel=channel.username,
                            message_id=audio_msg.message_id,
                            file_name=audio_msg.file_name,
                            file_path=None,
                            status=DownloadStatus.FAILED,
                            downloaded_at=now,
                            title=audio_msg.title,
                            performer=audio_msg.performer,
                            duration_seconds=audio_msg.duration_seconds,
                            file_size_bytes=audio_msg.file_size_bytes,
                            mime_type=audio_msg.mime_type,
                            error=str(exc),
                        )
                    )
            finally:
                semaphore.release()

        async for audio_msg in self._telegram_client.iter_audio_messages(channel, limit=limit):
            total_seen += 1

            if self._download_log.is_downloaded(channel.username, audio_msg.message_id):
                skipped += 1
                logger.debug(
                    "Skipping already downloaded message_id=%s in channel=%s",
                    audio_msg.message_id,
                    channel.username,
                )
                continue

            await semaphore.acquire()
            tasks.append(asyncio.create_task(_process_one(audio_msg)))

        if tasks:
            await asyncio.gather(*tasks)

        return DownloadSummary(
            channel=channel.username,
            total_seen=total_seen,
            downloaded=downloaded,
            skipped=skipped,
            failed=failed,
        )
