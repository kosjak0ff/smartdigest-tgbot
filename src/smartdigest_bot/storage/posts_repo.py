from __future__ import annotations

import sqlite3

from smartdigest_bot.models import DigestCandidate, ParsedPost, StoredPost
from smartdigest_bot.utils.datetime import from_iso, to_iso, utcnow
from smartdigest_bot.utils.text import normalize_whitespace, text_hash


class PostsRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def upsert_post(self, channel_id: int, channel_username: str, post: ParsedPost) -> StoredPost:
        normalized_text = normalize_whitespace(post.content_text)
        self.connection.execute(
            """
            INSERT INTO posts (
                channel_id, telegram_post_id, external_post_url, published_at, author_name,
                content_text, content_hash, raw_html, fetched_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(channel_id, telegram_post_id) DO UPDATE SET
                external_post_url = excluded.external_post_url,
                published_at = excluded.published_at,
                author_name = excluded.author_name,
                content_text = excluded.content_text,
                content_hash = excluded.content_hash,
                raw_html = excluded.raw_html,
                fetched_at = excluded.fetched_at
            """,
            (
                channel_id,
                post.telegram_post_id,
                post.external_post_url,
                to_iso(post.published_at),
                post.author_name,
                normalized_text,
                text_hash(normalized_text),
                post.raw_html,
                to_iso(utcnow()),
            ),
        )
        row = self.connection.execute(
            """
            SELECT p.id, c.username AS channel_username, p.telegram_post_id, p.external_post_url, p.content_text, p.published_at
            FROM posts p
            JOIN channels c ON c.id = p.channel_id
            WHERE p.channel_id = ? AND p.telegram_post_id = ?
            """,
            (channel_id, post.telegram_post_id),
        ).fetchone()
        self.connection.commit()
        return StoredPost(
            id=row["id"],
            channel_username=row["channel_username"],
            telegram_post_id=row["telegram_post_id"],
            external_post_url=row["external_post_url"],
            content_text=row["content_text"],
            published_at=from_iso(row["published_at"]),
        )

    def list_for_digest_window(self, window_start: str, window_end: str, limit: int) -> list[DigestCandidate]:
        rows = self.connection.execute(
            """
            SELECT p.id, c.username AS channel_username, p.external_post_url, p.content_text, p.published_at
            FROM posts p
            JOIN channels c ON c.id = p.channel_id
            WHERE p.fetched_at >= ? AND p.fetched_at < ?
            ORDER BY p.fetched_at ASC
            LIMIT ?
            """,
            (window_start, window_end, limit),
        ).fetchall()
        return [
            DigestCandidate(
                post_id=row["id"],
                channel_username=row["channel_username"],
                external_post_url=row["external_post_url"],
                content_text=row["content_text"],
                published_at=from_iso(row["published_at"]),
            )
            for row in rows
        ]
