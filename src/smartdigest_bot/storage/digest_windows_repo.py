from __future__ import annotations

import sqlite3

from smartdigest_bot.utils.datetime import to_iso, utcnow


class DigestWindowsRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def create_window(self, window_start: str, window_end: str, trigger_type: str, requested_by: str | None) -> int:
        self.connection.execute(
            """
            INSERT INTO digest_windows (
                window_start, window_end, trigger_type, status, requested_by, created_at
            ) VALUES (?, ?, ?, 'pending', ?, ?)
            """,
            (window_start, window_end, trigger_type, requested_by, to_iso(utcnow())),
        )
        window_id = self.connection.execute("SELECT last_insert_rowid()").fetchone()[0]
        self.connection.commit()
        return int(window_id)

    def get_latest_sent_window_end(self) -> str | None:
        row = self.connection.execute(
            """
            SELECT window_end
            FROM digest_windows
            WHERE status = 'sent'
            ORDER BY window_end DESC
            LIMIT 1
            """
        ).fetchone()
        if row is None:
            return None
        return row["window_end"]

    def set_status(self, window_id: int, status: str) -> None:
        started_at = to_iso(utcnow()) if status == "running" else None
        finished_at = to_iso(utcnow()) if status in {"sent", "failed", "skipped"} else None
        self.connection.execute(
            """
            UPDATE digest_windows
            SET status = ?,
                started_at = COALESCE(?, started_at),
                finished_at = COALESCE(?, finished_at)
            WHERE id = ?
            """,
            (status, started_at, finished_at, window_id),
        )
        self.connection.commit()

    def add_item(self, window_id: int, post_id: int) -> None:
        self.connection.execute(
            "INSERT OR IGNORE INTO digest_items (digest_window_id, post_id) VALUES (?, ?)",
            (window_id, post_id),
        )
        self.connection.commit()
