from __future__ import annotations

import asyncio
from typing import Any

from telegram import Bot

from smartdigest_bot.models import StoredPost
from smartdigest_bot.utils.text import escape_html, truncate


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

    async def send_post(
        self,
        post: StoredPost,
        chat_id: str,
        thread_id: int | None,
    ) -> Any:
        header = f"<b>@{escape_html(post.channel_username)}</b>"
        if post.has_audio:
            header += " <i>[audio]</i>"
        body = (
            f"{header}\n\n"
            f"{truncate(post.content_html, 3500)}\n\n"
            f"<a href=\"{post.external_post_url}\">Original post</a>"
        )
        message = await self.bot.send_message(
            chat_id=chat_id,
            text=body,
            message_thread_id=thread_id,
            parse_mode=self.parse_mode,
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
