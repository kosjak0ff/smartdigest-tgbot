from __future__ import annotations

import sqlite3

from smartdigest_bot.utils.datetime import to_iso, utcnow


class DeliveriesRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def is_delivered(self, post_id: int) -> bool:
        row = self.connection.execute(
            "SELECT 1 FROM post_deliveries WHERE post_id = ?",
            (post_id,),
        ).fetchone()
        return row is not None

    def mark_delivered(
        self,
        post_id: int,
        target_chat_id: str,
        target_thread_id: int | None,
        telegram_message_id: int | None,
    ) -> None:
        self.connection.execute(
            """
            INSERT OR IGNORE INTO post_deliveries (
                post_id, target_chat_id, target_thread_id, telegram_message_id, delivered_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (post_id, target_chat_id, target_thread_id, telegram_message_id, to_iso(utcnow())),
        )
        self.connection.commit()
