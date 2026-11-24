import asyncio
import getpass
import logging
import mimetypes
import re
from pathlib import Path
from typing import AsyncIterator

import qrcode
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)
from telethon import TelegramClient
from telethon.errors import FloodWaitError, SessionPasswordNeededError
from telethon.tl.types import DocumentAttributeAudio, DocumentAttributeFilename, Message

from src.domain.entities.audio_track import AudioMessage
from src.domain.entities.channel import Channel

logger = logging.getLogger(__name__)

_AUDIO_EXTENSIONS = {
    ".mp3",
    ".flac",
    ".wav",
    ".ogg",
    ".opus",
    ".m4a",
    ".aac",
    ".wma",
    ".alac",
    ".aiff",
}
_INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def sanitize_filename(name: str) -> str:
    """Sanitize a filename so it is safe on Windows and POSIX filesystems."""
    cleaned = _INVALID_FILENAME_CHARS.sub("_", name).strip().strip(".")
    return cleaned or "audio_file"


class TelethonAudioDownloader:
    """Telethon-based implementation of TelegramClientPort."""

    def __init__(
        self,
        api_id: int,
        api_hash: str,
        session_name: str,
        use_qr: bool = False,
    ) -> None:
        self._client = TelegramClient(session_name, api_id, api_hash)
        self._use_qr = use_qr
        self._message_cache: dict[tuple[str, int], Message] = {}
        self._reserved_paths: set[Path] = set()
        self._progress: Progress | None = None

    async def __aenter__(self) -> "TelethonAudioDownloader":
        if not self._use_qr:
            await self._client.start()
        else:
            await self._client.connect()
            if not await self._client.is_user_authorized():
                await self._login_with_qr()

        self._progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold cyan]{task.description}"),
            BarColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
            transient=True,
        )
        self._progress.start()
        return self

    async def _login_with_qr(self) -> None:
        """Authenticate the Telethon session by displaying a QR code in the terminal."""
        print("\nIniciando sesión por QR...")
        print("En tu celular abre Telegram -> Ajustes -> Dispositivos -> Vincular dispositivo.\n")

        while True:
            qr_login = await self._client.qr_login()
            qr = qrcode.QRCode(border=1)
            qr.add_data(qr_login.url)
            qr.make(fit=True)
            qr.print_ascii(invert=True)
            print("\nEsperando escaneo (expira en 60s)...")

            try:
                await qr_login.wait(timeout=60)
                print("Sesión iniciada correctamente.\n")
                return
            except asyncio.TimeoutError:
                print("El código QR expiró. Generando uno nuevo...\n")
            except SessionPasswordNeededError:
                password = getpass.getpass(
                    "Tu cuenta tiene verificación en 2 pasos. Ingresa tu contraseña: "
                )
                await self._client.sign_in(password=password)
                print("Sesión iniciada correctamente.\n")
                return

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._progress is not None:
            self._progress.stop()
            self._progress = None
        await self._client.disconnect()

    async def iter_audio_messages(
        self,
        channel: Channel,
        limit: int | None = None,
    ) -> AsyncIterator[AudioMessage]:
        """Yield AudioMessage objects for every audio file found in the channel."""
        entity = await self._client.get_entity(channel.url)
        async for msg in self._client.iter_messages(entity, limit=limit):
            if not isinstance(msg, Message) or not msg.document:
                continue

            audio_meta = self._extract_audio_metadata(channel.username, msg)
            if audio_meta is None:
                continue

            self._message_cache[(channel.username, msg.id)] = msg
            yield audio_meta

    async def download_audio(
        self,
        message: AudioMessage,
        destination_dir: Path,
    ) -> Path:
        """Download the cached Telegram message media to destination_dir."""
        tg_msg = self._message_cache.get((message.channel, message.message_id))
        if tg_msg is None:
            raise RuntimeError(
                f"Message {message.message_id} for channel {message.channel} "
                "was not found in session cache."
            )

        target_path = self._resolve_target_path(
            destination_dir, message.file_name, message.message_id
        )
        task_id = None
        if self._progress is not None:
            total_bytes = message.file_size_bytes or 0
            task_id = self._progress.add_task(
                message.file_name[:45],
                total=total_bytes if total_bytes > 0 else None,
            )

        def on_progress(received: int, total: int) -> None:
            if self._progress is None or task_id is None:
                return
            if total > 0:
                self._progress.update(task_id, completed=received, total=total)
            else:
                self._progress.update(task_id, completed=received)

        try:
            while True:
                try:
                    downloaded = await self._client.download_media(
                        tg_msg,
                        file=str(target_path),
                        progress_callback=on_progress,
                    )
                    if not downloaded:
                        raise RuntimeError(
                            f"Telethon returned empty path for message_id={message.message_id}"
                        )
                    return Path(downloaded)
                except FloodWaitError as exc:
                    wait_seconds = exc.seconds + 1
                    logger.warning("Telegram FloodWait hit; sleeping %s seconds...", wait_seconds)
                    await asyncio.sleep(wait_seconds)
        finally:
            if self._progress is not None and task_id is not None:
                self._progress.remove_task(task_id)

    def _extract_audio_metadata(self, channel_username: str, msg: Message) -> AudioMessage | None:
        doc = msg.document
        if doc is None:
            return None

        mime_type: str | None = getattr(doc, "mime_type", None)
        file_name: str | None = None
        title: str | None = None
        performer: str | None = None
        duration: int | None = None

        for attr in getattr(doc, "attributes", []):
            if isinstance(attr, DocumentAttributeFilename):
                file_name = attr.file_name
            elif isinstance(attr, DocumentAttributeAudio):
                if getattr(attr, "voice", False):
                    continue
                title = attr.title
                performer = attr.performer
                duration = int(attr.duration) if attr.duration is not None else None

        ext = Path(file_name).suffix.lower() if file_name else ""
        is_audio_mime = bool(mime_type and mime_type.lower().startswith("audio/"))
        is_audio_ext = ext in _AUDIO_EXTENSIONS

        if not (is_audio_mime or is_audio_ext):
            return None

        if not file_name:
            guessed_ext = mimetypes.guess_extension(mime_type or "") or ".mp3"
            if performer and title:
                file_name = f"{performer} - {title}{guessed_ext}"
            elif title:
                file_name = f"{title}{guessed_ext}"
            else:
                file_name = f"audio_{msg.id}{guessed_ext}"

        return AudioMessage(
            channel=channel_username,
            message_id=msg.id,
            file_name=sanitize_filename(file_name),
            title=title,
            performer=performer,
            duration_seconds=duration,
            file_size_bytes=getattr(doc, "size", None),
            mime_type=mime_type,
            message_date=msg.date,
            caption=msg.message or None,
        )

    def _resolve_target_path(self, destination_dir: Path, file_name: str, message_id: int) -> Path:
        candidate = destination_dir / file_name
        if not candidate.exists() and candidate not in self._reserved_paths:
            self._reserved_paths.add(candidate)
            return candidate
        stem = candidate.stem
        suffix = candidate.suffix
        unique = destination_dir / f"{stem}_{message_id}{suffix}"
        self._reserved_paths.add(unique)
        return unique
