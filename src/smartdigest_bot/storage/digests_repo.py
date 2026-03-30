from __future__ import annotations

import sqlite3

from smartdigest_bot.utils.datetime import to_iso, utcnow


class DigestsRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def create_digest(
        self,
        window_id: int,
        target_chat_id: str,
        target_thread_id: int | None,
        telegram_message_id: int | None,
        model_name: str,
        summary_text: str,
        source_posts_count: int,
    ) -> None:
        self.connection.execute(
            """
            INSERT INTO digests (
                digest_window_id, target_chat_id, target_thread_id, telegram_message_id,
                model_name, prompt_version, summary_text, source_posts_count, sent_at
            ) VALUES (?, ?, ?, ?, ?, 'v1', ?, ?, ?)
            """,
            (
                window_id,
                target_chat_id,
                target_thread_id,
                telegram_message_id,
                model_name,
                summary_text,
                source_posts_count,
                to_iso(utcnow()),
            ),
        )
        self.connection.commit()
