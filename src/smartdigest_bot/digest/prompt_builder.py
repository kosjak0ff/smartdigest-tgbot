from __future__ import annotations

from smartdigest_bot.models import DigestCandidate
from smartdigest_bot.utils.text import truncate


def build_digest_prompt(posts: list[DigestCandidate]) -> str:
    lines = [
        "Create a concise Telegram digest in Russian.",
        "Requirements:",
        "- group updates by channel when useful;",
        "- highlight key events and practical implications;",
        "- include markdown-friendly bullet points;",
        "- preserve original post links;",
        "- keep the digest compact and scannable.",
        "",
        "Source posts:",
    ]
    for index, post in enumerate(posts, start=1):
        lines.append(
            f"{index}. @{post.channel_username} | {post.external_post_url}\n"
            f"Text: {truncate(post.content_text, 1200)}"
        )
    return "\n".join(lines)
