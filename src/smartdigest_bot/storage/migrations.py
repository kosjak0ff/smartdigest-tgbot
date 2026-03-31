from __future__ import annotations

import sqlite3


SCHEMA = """
CREATE TABLE IF NOT EXISTS channels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    title TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    fetch_interval_minutes INTEGER,
    last_checked_at TEXT,
    last_seen_post_id INTEGER,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id INTEGER NOT NULL,
    telegram_post_id INTEGER NOT NULL,
    external_post_url TEXT NOT NULL,
    published_at TEXT,
    author_name TEXT,
    content_text TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    has_audio INTEGER NOT NULL DEFAULT 0,
    has_video INTEGER NOT NULL DEFAULT 0,
    has_photo INTEGER NOT NULL DEFAULT 0,
    is_forwarded INTEGER NOT NULL DEFAULT 0,
    raw_html TEXT,
    fetched_at TEXT NOT NULL,
    UNIQUE(channel_id, telegram_post_id),
    FOREIGN KEY(channel_id) REFERENCES channels(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS post_deliveries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER NOT NULL UNIQUE,
    target_chat_id TEXT NOT NULL,
    target_thread_id INTEGER,
    telegram_message_id INTEGER,
    delivered_at TEXT NOT NULL,
    FOREIGN KEY(post_id) REFERENCES posts(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS digest_windows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    window_start TEXT NOT NULL,
    window_end TEXT NOT NULL,
    trigger_type TEXT NOT NULL,
    status TEXT NOT NULL,
    requested_by TEXT,
    created_at TEXT NOT NULL,
    started_at TEXT,
    finished_at TEXT,
    UNIQUE(window_start, window_end, trigger_type)
);

CREATE TABLE IF NOT EXISTS digest_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    digest_window_id INTEGER NOT NULL,
    post_id INTEGER NOT NULL,
    UNIQUE(digest_window_id, post_id),
    FOREIGN KEY(digest_window_id) REFERENCES digest_windows(id) ON DELETE CASCADE,
    FOREIGN KEY(post_id) REFERENCES posts(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS digests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    digest_window_id INTEGER NOT NULL UNIQUE,
    target_chat_id TEXT NOT NULL,
    target_thread_id INTEGER,
    telegram_message_id INTEGER,
    model_name TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    summary_text TEXT NOT NULL,
    source_posts_count INTEGER NOT NULL,
    sent_at TEXT,
    FOREIGN KEY(digest_window_id) REFERENCES digest_windows(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS app_state (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_posts_channel_id ON posts(channel_id);
CREATE INDEX IF NOT EXISTS idx_posts_published_at ON posts(published_at);
CREATE INDEX IF NOT EXISTS idx_digest_windows_status ON digest_windows(status);
"""


def migrate(connection: sqlite3.Connection) -> None:
    connection.executescript(SCHEMA)
    columns = {row["name"] for row in connection.execute("PRAGMA table_info(posts)").fetchall()}
    if "has_audio" not in columns:
        connection.execute("ALTER TABLE posts ADD COLUMN has_audio INTEGER NOT NULL DEFAULT 0")
    if "has_video" not in columns:
        connection.execute("ALTER TABLE posts ADD COLUMN has_video INTEGER NOT NULL DEFAULT 0")
    if "has_photo" not in columns:
        connection.execute("ALTER TABLE posts ADD COLUMN has_photo INTEGER NOT NULL DEFAULT 0")
    if "is_forwarded" not in columns:
        connection.execute("ALTER TABLE posts ADD COLUMN is_forwarded INTEGER NOT NULL DEFAULT 0")
    connection.commit()
