from __future__ import annotations

from datetime import datetime

from bs4 import BeautifulSoup

from smartdigest_bot.models import ParsedPost
from smartdigest_bot.utils.text import normalize_whitespace


def parse_channel_html(html: str) -> list[ParsedPost]:
    soup = BeautifulSoup(html, "html.parser")
    posts: list[ParsedPost] = []

    for node in soup.select("div.tgme_widget_message[data-post]"):
        data_post = node.get("data-post", "")
        if "/" not in data_post:
            continue
        _, post_id_raw = data_post.split("/", 1)
        if not post_id_raw.isdigit():
            continue

        text_node = node.select_one(".tgme_widget_message_text")
        date_node = node.select_one("a.tgme_widget_message_date")
        author_node = node.select_one(".tgme_widget_message_author")

        if date_node is None or not date_node.get("href"):
            continue

        time_node = date_node.select_one("time")
        published_at = None
        if time_node and time_node.get("datetime"):
            published_at = datetime.fromisoformat(time_node["datetime"].replace("Z", "+00:00"))

        text = normalize_whitespace(text_node.get_text("\n", strip=True) if text_node else "")
        if not text:
            continue

        posts.append(
            ParsedPost(
                telegram_post_id=int(post_id_raw),
                external_post_url=date_node["href"],
                content_text=text,
                published_at=published_at,
                author_name=author_node.get_text(strip=True) if author_node else None,
                raw_html=str(node),
            )
        )

    return sorted(posts, key=lambda item: item.telegram_post_id)
