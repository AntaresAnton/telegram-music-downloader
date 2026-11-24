from pathlib import Path

import pytest

from src.infrastructure.config.settings import Settings
from src.infrastructure.telegram.telethon_downloader import sanitize_filename


def test_sanitize_filename_windows_chars() -> None:
    assert sanitize_filename('Band: "Track" <1>?.mp3') == "Band_ _Track_ _1__.mp3"


def test_settings_from_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "API_ID=123456\nAPI_HASH=abcdef123456\nSESSION_NAME=my_session\nTOGETHER_API_KEY=tg_key\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("API_ID", raising=False)
    monkeypatch.delenv("API_HASH", raising=False)

    settings = Settings.from_env(env_path=env_file, base_dir=tmp_path)
    assert settings.telegram_api_id == 123456
    assert settings.telegram_api_hash == "abcdef123456"
    assert settings.telegram_session_name == "my_session"
    assert settings.together_api_key == "tg_key"
