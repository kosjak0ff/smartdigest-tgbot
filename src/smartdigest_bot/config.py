from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from smartdigest_bot.exceptions import ConfigurationError


@dataclass(slots=True)
class AppConfig:
    telegram_bot_token: str
    telegram_forward_chat_id: str
    telegram_forward_thread_id: int | None
    telegram_digest_chat_id: str
    telegram_digest_thread_id: int | None
    telegram_owner_user_id: int | None
    database_path: str
    channels_file: str
    timezone: str
    fetch_interval_minutes: int
    digest_schedule_times: list[str]
    digest_lookback_hours: int
    digest_max_posts_per_run: int
    perplexity_api_key: str
    perplexity_model: str
    perplexity_base_url: str
    http_timeout_seconds: float
    http_user_agent: str
    log_level: str
    log_file_path: str | None
    first_run_mode: str
    first_run_max_posts_per_channel: int
    post_send_delay_seconds: float
    telegram_parse_mode: str


def _required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ConfigurationError(f"Environment variable {name} is required")
    return value


def _optional_int(name: str) -> int | None:
    value = os.getenv(name)
    if value in (None, ""):
        return None
    return int(value)


def load_config(env_file: str = ".env") -> AppConfig:
    env_path = Path(env_file)
    if env_path.exists():
        load_dotenv(env_path)

    forward_chat_id = _required("TELEGRAM_FORWARD_CHAT_ID")
    digest_chat_id = os.getenv("TELEGRAM_DIGEST_CHAT_ID") or forward_chat_id

    digest_times = [item.strip() for item in os.getenv("DIGEST_SCHEDULE_TIMES", "08:00,20:00").split(",") if item.strip()]
    if not digest_times:
        raise ConfigurationError("DIGEST_SCHEDULE_TIMES must contain at least one HH:MM value")

    first_run_mode = os.getenv("FIRST_RUN_MODE", "mark_seen")
    if first_run_mode not in {"mark_seen", "send_recent"}:
        raise ConfigurationError("FIRST_RUN_MODE must be mark_seen or send_recent")

    return AppConfig(
        telegram_bot_token=_required("TELEGRAM_BOT_TOKEN"),
        telegram_forward_chat_id=forward_chat_id,
        telegram_forward_thread_id=_optional_int("TELEGRAM_FORWARD_THREAD_ID"),
        telegram_digest_chat_id=digest_chat_id,
        telegram_digest_thread_id=_optional_int("TELEGRAM_DIGEST_THREAD_ID"),
        telegram_owner_user_id=_optional_int("TELEGRAM_OWNER_USER_ID"),
        database_path=os.getenv("DATABASE_PATH", "data/smartdigest.sqlite3"),
        channels_file=os.getenv("CHANNELS_FILE", "channels.yaml"),
        timezone=os.getenv("TIMEZONE", "UTC"),
        fetch_interval_minutes=int(os.getenv("FETCH_INTERVAL_MINUTES", "10")),
        digest_schedule_times=digest_times,
        digest_lookback_hours=int(os.getenv("DIGEST_LOOKBACK_HOURS", "12")),
        digest_max_posts_per_run=int(os.getenv("DIGEST_MAX_POSTS_PER_RUN", "100")),
        perplexity_api_key=_required("PERPLEXITY_API_KEY"),
        perplexity_model=os.getenv("PERPLEXITY_MODEL", "sonar-pro"),
        perplexity_base_url=os.getenv("PERPLEXITY_BASE_URL", "https://api.perplexity.ai"),
        http_timeout_seconds=float(os.getenv("HTTP_TIMEOUT_SECONDS", "20")),
        http_user_agent=os.getenv("HTTP_USER_AGENT", "smartdigest-bot/0.1"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        log_file_path=os.getenv("LOG_FILE_PATH", "data/logs/smartdigest.log"),
        first_run_mode=first_run_mode,
        first_run_max_posts_per_channel=int(os.getenv("FIRST_RUN_MAX_POSTS_PER_CHANNEL", "0")),
        post_send_delay_seconds=float(os.getenv("POST_SEND_DELAY_SECONDS", "1.0")),
        telegram_parse_mode=os.getenv("TELEGRAM_PARSE_MODE", "HTML"),
    )
