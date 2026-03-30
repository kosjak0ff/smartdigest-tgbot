from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class ChannelConfig:
    username: str
    title: str | None = None
    enabled: bool = True
    fetch_interval_minutes: int | None = None


@dataclass(slots=True)
class ParsedPost:
    telegram_post_id: int
    external_post_url: str
    content_text: str
    content_html: str
    published_at: datetime | None
    author_name: str | None
    has_audio: bool
    raw_html: str | None


@dataclass(slots=True)
class StoredPost:
    id: int
    channel_username: str
    telegram_post_id: int
    external_post_url: str
    content_text: str
    content_html: str
    published_at: datetime | None
    has_audio: bool


@dataclass(slots=True)
class DigestCandidate:
    post_id: int
    channel_username: str
    external_post_url: str
    content_text: str
    published_at: datetime | None
    has_audio: bool
