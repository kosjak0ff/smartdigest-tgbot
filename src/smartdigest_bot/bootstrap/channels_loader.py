from __future__ import annotations

from pathlib import Path

import yaml

from smartdigest_bot.exceptions import ConfigurationError
from smartdigest_bot.models import ChannelConfig


def load_channels(path: str) -> list[ChannelConfig]:
    file_path = Path(path)
    if not file_path.exists():
        raise ConfigurationError(f"Channels file not found: {path}")

    data = yaml.safe_load(file_path.read_text(encoding="utf-8")) or {}
    items = data.get("channels", [])
    channels: list[ChannelConfig] = []
    seen: set[str] = set()

    for item in items:
        username = str(item["username"]).strip().lstrip("@")
        if not username:
            raise ConfigurationError("Channel username cannot be empty")
        if username in seen:
            raise ConfigurationError(f"Duplicate channel username: {username}")
        seen.add(username)
        channels.append(
            ChannelConfig(
                username=username,
                title=item.get("title"),
                enabled=bool(item.get("enabled", True)),
                fetch_interval_minutes=item.get("fetch_interval_minutes"),
            )
        )
    return channels
