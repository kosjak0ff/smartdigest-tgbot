from __future__ import annotations

from smartdigest_bot.models import DigestCandidate
from smartdigest_bot.utils.text import truncate


def build_digest_prompt(posts: list[DigestCandidate]) -> str:
    lines = [
        "Сделай краткий дайджест для Telegram строго на русском языке.",
        "",
        "Жесткие правила:",
        "- используй ТОЛЬКО информацию из постов ниже;",
        "- НЕ добавляй внешние факты, новости, рыночные данные, даты, проекты или выводы, которых нет в исходных постах;",
        "- если данных недостаточно, просто кратко перескажи то, что есть, без догадок;",
        "- не используй английские заголовки вроде 'Key takeaway', 'Market Pressure', 'Active Opportunities' и т.п.;",
        "- не используй таблицы;",
        "- сохрани ссылки на оригинальные посты;",
        "- формат ответа: короткий русский дайджест с буллетами и мини-секциями при необходимости;",
        "- если в постах несколько тем, сгруппируй их аккуратно, но не выдумывай категории, которых нет в материале;",
        "",
        "Исходные посты:",
    ]
    for index, post in enumerate(posts, start=1):
        lines.append(
            f"{index}. @{post.channel_username} | {post.external_post_url}\n"
            f"Текст поста: {truncate(post.content_text, 1200)}"
        )
    return "\n".join(lines)
