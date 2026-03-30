from __future__ import annotations

from smartdigest_bot.models import ParsedPost


def select_first_run_posts(posts: list[ParsedPost], mode: str, max_posts: int) -> list[ParsedPost]:
    ordered = sorted(posts, key=lambda item: item.telegram_post_id)
    if mode == "mark_seen":
        return []
    if max_posts <= 0:
        return ordered[-1:] if ordered else []
    return ordered[-max_posts:]
