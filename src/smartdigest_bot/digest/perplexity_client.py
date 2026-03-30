from __future__ import annotations

import httpx

from smartdigest_bot.exceptions import DigestError


class PerplexityClient:
    def __init__(self, api_key: str, model: str, base_url: str, timeout_seconds: float) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(
            timeout=timeout_seconds,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )

    async def summarize(self, prompt: str) -> str:
        try:
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You write compact high-signal Telegram digests with source links.",
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
            raise DigestError("Perplexity API request timed out.") from exc
        except httpx.HTTPStatusError as exc:
            raise DigestError(
                f"Perplexity API returned HTTP {exc.response.status_code}."
            ) from exc
        except httpx.HTTPError as exc:
            raise DigestError("Perplexity API request failed.") from exc

    async def close(self) -> None:
        await self.client.aclose()
