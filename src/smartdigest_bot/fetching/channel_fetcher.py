from __future__ import annotations

import logging

import httpx

from smartdigest_bot.fetching.parser import parse_channel_html
from smartdigest_bot.models import ParsedPost


class ChannelFetcher:
    def __init__(self, timeout_seconds: float, user_agent: str) -> None:
        self.logger = logging.getLogger(__name__)
        self.client = httpx.AsyncClient(
            timeout=timeout_seconds,
            headers={"User-Agent": user_agent},
            follow_redirects=True,
        )

    async def fetch_posts(self, channel_username: str) -> list[ParsedPost]:
        url = f"https://t.me/s/{channel_username}"
        self.logger.info("Fetching channel page: %s", url)
        response = await self.client.get(url)
        response.raise_for_status()
        return parse_channel_html(response.text)

    async def close(self) -> None:
        await self.client.aclose()
