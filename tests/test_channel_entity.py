import pytest

from src.domain.entities.channel import Channel


def test_channel_from_url() -> None:
    ch = Channel.from_input("https://t.me/deathmetal2")
    assert ch.username == "deathmetal2"
    assert ch.url == "https://t.me/deathmetal2"
    assert ch.enabled is True


def test_channel_from_at_handle() -> None:
    ch = Channel.from_input("@deathmetal2")
    assert ch.username == "deathmetal2"
    assert ch.url == "https://t.me/deathmetal2"


def test_channel_from_plain_username() -> None:
    ch = Channel.from_input("deathmetal2")
    assert ch.username == "deathmetal2"
    assert ch.url == "https://t.me/deathmetal2"


def test_channel_empty_raises() -> None:
    with pytest.raises(ValueError):
        Channel.from_input("   ")
