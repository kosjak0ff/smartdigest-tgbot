from __future__ import annotations

import asyncio
import httpx

from smartdigest_bot.exceptions import DigestError


class PerplexityClient:
    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str,
        timeout_seconds: float,
        max_retries: int,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.max_retries = max(1, max_retries)
        self.client = httpx.AsyncClient(
            timeout=timeout_seconds,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )

    async def summarize(self, prompt: str) -> str:
        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = await self.client.post(
                    f"{self.base_url}/chat/completions",
                    json={
                        "model": self.model,
                        "messages": [
                            {
                                "role": "system",
                                "content": (
                                    "Ты пишешь краткие русскоязычные дайджесты для Telegram. "
                                    "Используй только материалы, переданные пользователем. "
                                    "Не добавляй внешние знания, новости, рыночные сводки или домыслы."
                                ),
                            },
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": 0.2,
                    },
                )
                response.raise_for_status()
                payload = response.json()
                return payload["choices"][0]["message"]["content"].strip()
            except httpx.TimeoutException as exc:
                last_error = exc
                if attempt < self.max_retries:
                    await asyncio.sleep(min(2 * attempt, 5))
                    continue
                raise DigestError(
                    f"Perplexity API request timed out after {self.max_retries} attempts."
                ) from exc
            except httpx.HTTPStatusError as exc:
                last_error = exc
                raise DigestError(
                    f"Perplexity API returned HTTP {exc.response.status_code}."
                ) from exc
            except httpx.HTTPError as exc:
                last_error = exc
                if attempt < self.max_retries:
                    await asyncio.sleep(min(2 * attempt, 5))
                    continue
                raise DigestError(
                    f"Perplexity API request failed after {self.max_retries} attempts."
                ) from exc
        raise DigestError("Perplexity API request failed.") from last_error

    async def close(self) -> None:
        await self.client.aclose()
