import json
import os
from datetime import datetime, timezone
from pathlib import Path

from src.domain.entities.audio_track import DownloadRecord, DownloadStatus


class JsonDownloadLog:
    """JSON-backed implementation of DownloadLogPort with atomic writes."""

    def __init__(self, log_path: Path) -> None:
        self._log_path = log_path
        self._records: dict[tuple[str, int], DownloadRecord] = {}
        self._load()

    def _load(self) -> None:
        if not self._log_path.exists():
            return

        raw = self._log_path.read_text(encoding="utf-8").strip()
        if not raw:
            return

        payload = json.loads(raw)
        for item in payload.get("records", []):
            record = DownloadRecord(
                channel=item["channel"],
                message_id=int(item["message_id"]),
                file_name=item["file_name"],
                file_path=item.get("file_path"),
                status=DownloadStatus(item["status"]),
                downloaded_at=datetime.fromisoformat(item["downloaded_at"]),
                title=item.get("title"),
                performer=item.get("performer"),
                duration_seconds=item.get("duration_seconds"),
                file_size_bytes=item.get("file_size_bytes"),
                mime_type=item.get("mime_type"),
                error=item.get("error"),
            )
            self._records[(record.channel, record.message_id)] = record

    def is_downloaded(self, channel: str, message_id: int) -> bool:
        existing = self._records.get((channel, message_id))
        return existing is not None and existing.status == DownloadStatus.DOWNLOADED

    def record(self, entry: DownloadRecord) -> None:
        self._records[(entry.channel, entry.message_id)] = entry
        self._flush()

    def get_all(self) -> list[DownloadRecord]:
        return list(self._records.values())

    def _flush(self) -> None:
        self._log_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": 1,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "total_records": len(self._records),
            "records": [
                {
                    "channel": r.channel,
                    "message_id": r.message_id,
                    "file_name": r.file_name,
                    "file_path": r.file_path,
                    "status": r.status.value,
                    "downloaded_at": r.downloaded_at.isoformat(),
                    "title": r.title,
                    "performer": r.performer,
                    "duration_seconds": r.duration_seconds,
                    "file_size_bytes": r.file_size_bytes,
                    "mime_type": r.mime_type,
                    "error": r.error,
                }
                for r in self._records.values()
            ],
        }
        tmp_path = self._log_path.with_suffix(".json.tmp")
        tmp_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp_path, self._log_path)
