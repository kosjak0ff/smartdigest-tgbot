from __future__ import annotations

import sqlite3

from smartdigest_bot.models import ChannelConfig
from smartdigest_bot.utils.datetime import to_iso, utcnow


class ChannelsRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def sync(self, channels: list[ChannelConfig]) -> None:
        now = to_iso(utcnow())
        for channel in channels:
            self.connection.execute(
                """
                INSERT INTO channels (username, title, is_active, fetch_interval_minutes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(username) DO UPDATE SET
                    title = excluded.title,
                    is_active = excluded.is_active,
                    fetch_interval_minutes = excluded.fetch_interval_minutes,
                    updated_at = excluded.updated_at
                """,
                (
                    channel.username,
                    channel.title,
                    1 if channel.enabled else 0,
                    channel.fetch_interval_minutes,
                    now,
                    now,
                ),
            )
        self.connection.commit()

    def list_active(self) -> list[sqlite3.Row]:
        return list(
            self.connection.execute(
                """
                SELECT *
                FROM channels
                WHERE is_active = 1
                ORDER BY username
                """
            )
        )

    def update_check_state(self, channel_id: int, last_seen_post_id: int | None) -> None:
        self.connection.execute(
            """
            UPDATE channels
            SET last_checked_at = ?, last_seen_post_id = COALESCE(?, last_seen_post_id), updated_at = ?
            WHERE id = ?
            """,
            (to_iso(utcnow()), last_seen_post_id, to_iso(utcnow()), channel_id),
        )
        self.connection.commit()
