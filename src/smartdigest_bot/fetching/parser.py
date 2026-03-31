from __future__ import annotations

from datetime import datetime
from html import escape

from bs4 import BeautifulSoup, NavigableString, Tag

from smartdigest_bot.models import ParsedPost
from smartdigest_bot.utils.text import normalize_message_text, strip_html_tags


def _has_audio(node) -> bool:
    selectors = (
        ".tgme_widget_message_voice_player",
        ".tgme_widget_message_audio",
        ".tgme_widget_message_document audio",
        "audio",
    )
    return any(node.select_one(selector) is not None for selector in selectors)


def _has_video(node) -> bool:
    selectors = (
        ".tgme_widget_message_video_player",
        ".tgme_widget_message_video_wrap",
        ".tgme_widget_message_document video",
        "video",
    )
    return any(node.select_one(selector) is not None for selector in selectors)


def _has_photo(node) -> bool:
    selectors = (
        ".tgme_widget_message_photo_wrap",
        ".tgme_widget_message_grouped_wrap",
    )
    return any(node.select_one(selector) is not None for selector in selectors)


def _is_forwarded(node) -> bool:
    selectors = (
        ".tgme_widget_message_forwarded_from",
        ".tgme_widget_message_forwarded_from_name",
    )
    return any(node.select_one(selector) is not None for selector in selectors)


def _render_node(node) -> str:
    if isinstance(node, NavigableString):
        return escape(str(node))
    if not isinstance(node, Tag):
        return ""

    name = node.name.lower()
    children = "".join(_render_node(child) for child in node.children)

    if name == "br":
        return "\n"
    if name in {"b", "strong"}:
        return f"<b>{children}</b>"
    if name in {"i", "em"}:
        return f"<i>{children}</i>"
    if name == "u":
        return f"<u>{children}</u>"
    if name in {"s", "strike", "del"}:
        return f"<s>{children}</s>"
    if name == "code":
        return f"<code>{children}</code>"
    if name == "pre":
        return f"<pre>{children}</pre>"
    if name == "a":
        href = node.get("href")
        if href:
            return f'<a href="{escape(href, quote=True)}">{children}</a>'
        return children
    if name in {"blockquote", "aside"}:
        return f"<blockquote>{children}</blockquote>"
    return children


def _render_message_html(text_node: Tag | None) -> str:
    if text_node is None:
        return ""
    rendered = "".join(_render_node(child) for child in text_node.children)
    lines = [line.rstrip() for line in rendered.replace("\r\n", "\n").split("\n")]
    normalized: list[str] = []
    previous_blank = False
    for line in lines:
        if not line.strip():
            if not previous_blank and normalized:
                normalized.append("")
            previous_blank = True
            continue
        normalized.append(line.strip())
        previous_blank = False
    return "\n".join(normalized).strip()


def _strip_pinned_boilerplate(value: str) -> str:
    lines = value.split("\n")
    filtered = []
    for line in lines:
        compact = " ".join(line.split())
        lowered = compact.lower()
        if " pinned a " in lowered:
            continue
        filtered.append(line)
    return "\n".join(filtered).strip()


def _is_pinned_service_post(text: str, is_forwarded: bool) -> bool:
    if not is_forwarded:
        return False
    compact = " ".join(text.split()).lower()
    return bool(compact) and " pinned a " in compact and "\n" not in text


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
        has_audio = _has_audio(node)
        has_video = _has_video(node)
        has_photo = _has_photo(node)
        is_forwarded = _is_forwarded(node)

        if date_node is None or not date_node.get("href"):
            continue

        time_node = date_node.select_one("time")
        published_at = None
        if time_node and time_node.get("datetime"):
            published_at = datetime.fromisoformat(time_node["datetime"].replace("Z", "+00:00"))

        content_html = _render_message_html(text_node)
        text = normalize_message_text(strip_html_tags(content_html))
        if _is_pinned_service_post(text, is_forwarded):
            continue
        if is_forwarded and content_html:
            content_html = _strip_pinned_boilerplate(content_html)
            text = normalize_message_text(_strip_pinned_boilerplate(text))
        if not text and has_audio:
            text = "[Audio post without text]"
            content_html = "[Audio post without text]"
        if not text and has_video:
            text = "[Video post without text]"
            content_html = "[Video post without text]"
        if not text:
            continue

        posts.append(
            ParsedPost(
                telegram_post_id=int(post_id_raw),
                external_post_url=date_node["href"],
                content_text=text,
                content_html=content_html,
                published_at=published_at,
                author_name=author_node.get_text(strip=True) if author_node else None,
                has_audio=has_audio,
                has_video=has_video,
                has_photo=has_photo,
                is_forwarded=is_forwarded,
                raw_html=str(node),
            )
        )

    return sorted(posts, key=lambda item: item.telegram_post_id)
