import argparse
import asyncio
import logging
from pathlib import Path

from rich.logging import RichHandler

from src.application.use_cases.download_channel_audios import DownloadChannelAudiosUseCase
from src.domain.entities.channel import Channel
from src.infrastructure.config.settings import Settings
from src.infrastructure.persistence.json_channel_repository import JsonChannelRepository
from src.infrastructure.persistence.json_download_log import JsonDownloadLog
from src.infrastructure.telegram.telethon_downloader import TelethonAudioDownloader


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tg-audio-dl",
        description="Download audio files from Telegram channels with JSON logging.",
    )
    parser.add_argument(
        "--channel",
        action="append",
        dest="channels",
        help="Telegram channel URL, @username, or username (can be passed multiple times).",
    )
    parser.add_argument(
        "--add-channel",
        dest="add_channel",
        help="Add a channel to config/channels.json and exit (unless --channel is also passed).",
    )
    parser.add_argument(
        "--list-channels",
        action="store_true",
        help="List enabled channels in config/channels.json and exit.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of recent messages to inspect per channel.",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=3,
        help="Number of simultaneous audio downloads (default: 3).",
    )
    parser.add_argument(
        "--qr",
        action="store_true",
        help="Authenticate using a QR code in the terminal instead of phone/SMS code.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging.",
    )
    return parser


async def run_downloads(
    settings: Settings,
    channels: list[Channel],
    limit: int | None,
    concurrency: int = 3,
    use_qr: bool = False,
) -> None:
    download_log = JsonDownloadLog(settings.logs_file)
    async with TelethonAudioDownloader(
        api_id=settings.telegram_api_id,
        api_hash=settings.telegram_api_hash,
        session_name=settings.telegram_session_name,
        use_qr=use_qr,
    ) as tg_client:
        use_case = DownloadChannelAudiosUseCase(
            telegram_client=tg_client,
            download_log=download_log,
            downloads_root=settings.downloads_dir,
        )
        for channel in channels:
            print(f"Processing channel: {channel.url} (concurrency={concurrency})")
            summary = await use_case.execute(channel, limit=limit, concurrency=concurrency)
            print(
                f"Done [{summary.channel}]: "
                f"seen={summary.total_seen}, "
                f"downloaded={summary.downloaded}, "
                f"skipped={summary.skipped}, "
                f"failed={summary.failed}"
            )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(message)s",
        handlers=[RichHandler(rich_tracebacks=True, show_path=False)],
    )
    if not args.verbose:
        logging.getLogger("telethon").setLevel(logging.WARNING)

    settings = Settings.from_env(base_dir=Path.cwd())
    channel_repo = JsonChannelRepository(settings.channels_file)

    if args.add_channel:
        new_channel = Channel.from_input(args.add_channel)
        channel_repo.add_channel(new_channel)
        print(f"Added channel: {new_channel.url}")
        if not args.channels:
            return 0

    if args.list_channels:
        for ch in channel_repo.list_enabled_channels():
            print(f"- {ch.username} ({ch.url})")
        return 0

    if args.channels:
        channels = [Channel.from_input(raw) for raw in args.channels]
    else:
        channels = channel_repo.list_enabled_channels()

    if not channels:
        print("No enabled channels found. Add one with --add-channel or pass --channel.")
        return 1

    asyncio.run(
        run_downloads(
            settings,
            channels,
            limit=args.limit,
            concurrency=args.concurrency,
            use_qr=args.qr,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
