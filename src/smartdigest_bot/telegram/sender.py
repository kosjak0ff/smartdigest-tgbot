from __future__ import annotations

import asyncio
from typing import Any

from telegram import Bot
from telegram.error import BadRequest

from smartdigest_bot.models import StoredPost
from smartdigest_bot.utils.text import escape_html, strip_html_tags, truncate


class TelegramSender:
    def __init__(
        self,
        bot: Bot,
        parse_mode: str,
        post_send_delay_seconds: float,
    ) -> None:
        self.bot = bot
        self.parse_mode = parse_mode
        self.post_send_delay_seconds = post_send_delay_seconds

    def _build_html_body(self, post: StoredPost, limit: int) -> str:
        header = f"<b>@{escape_html(post.channel_username)}</b>"
        if post.has_audio:
            header += " <i>[audio]</i>"

        link_block = f'<a href="{post.external_post_url}">Original post</a>'
        reserved = len(header) + len(link_block) + 4
        content_limit = max(0, limit - reserved)
        content_html = post.content_html
        if len(content_html) > content_limit:
            content_html = escape_html(truncate(post.content_text, max(0, content_limit)))
        return f"{header}\n\n{content_html}\n\n{link_block}"

    def _build_plaintext_body(self, post: StoredPost, limit: int) -> str:
        header = f"@{post.channel_username}"
        if post.has_audio:
            header += " [audio]"
        body = (
            f"{header}\n\n"
            f"{truncate(post.content_text, max(0, limit - len(header) - len(post.external_post_url) - 4))}\n\n"
            f"{post.external_post_url}"
        )
        return body

    async def send_post(
        self,
        post: StoredPost,
        chat_id: str,
        thread_id: int | None,
    ) -> Any:
        html_body = self._build_html_body(post, 4096)
        try:
            message = await self.bot.send_message(
                chat_id=chat_id,
                text=html_body,
                message_thread_id=thread_id,
                parse_mode=self.parse_mode,
                disable_web_page_preview=False,
            )
        except BadRequest:
            fallback_text = self._build_plaintext_body(
                StoredPost(
                    id=post.id,
                    channel_username=post.channel_username,
                    telegram_post_id=post.telegram_post_id,
                    external_post_url=post.external_post_url,
                    content_text=strip_html_tags(post.content_html) or post.content_text,
                    content_html=post.content_html,
                    published_at=post.published_at,
                    has_audio=post.has_audio,
                ),
                4096,
            )
            message = await self.bot.send_message(
                chat_id=chat_id,
                text=fallback_text,
                message_thread_id=thread_id,
                disable_web_page_preview=False,
            )
        if self.post_send_delay_seconds > 0:
            await asyncio.sleep(self.post_send_delay_seconds)
        return message

    async def send_digest(
        self,
        text: str,
        chat_id: str,
        thread_id: int | None,
    ) -> Any:
        return await self.bot.send_message(
            chat_id=chat_id,
            text=truncate(text, 4096),
            message_thread_id=thread_id,
            parse_mode=self.parse_mode,
            disable_web_page_preview=False,
        )
