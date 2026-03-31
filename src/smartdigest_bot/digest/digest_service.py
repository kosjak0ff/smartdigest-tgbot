from __future__ import annotations

from dataclasses import dataclass
import logging

from smartdigest_bot.digest.prompt_builder import build_digest_prompt
from smartdigest_bot.exceptions import DigestError
from smartdigest_bot.storage.digest_windows_repo import DigestWindowsRepository
from smartdigest_bot.storage.digests_repo import DigestsRepository
from smartdigest_bot.storage.posts_repo import PostsRepository
from smartdigest_bot.utils.datetime import from_iso, to_iso


@dataclass(slots=True)
class DigestRunContext:
    window_start: str
    window_end: str
    trigger_type: str
    requested_by: str | None


class DigestService:
    def __init__(
        self,
        posts_repo: PostsRepository,
        digest_windows_repo: DigestWindowsRepository,
        digests_repo: DigestsRepository,
        perplexity_client,
        telegram_sender,
        target_chat_id: str,
        target_thread_id: int | None,
        model_name: str,
        max_posts_per_run: int,
    ) -> None:
        self.logger = logging.getLogger(__name__)
        self.posts_repo = posts_repo
        self.digest_windows_repo = digest_windows_repo
        self.digests_repo = digests_repo
        self.perplexity_client = perplexity_client
        self.telegram_sender = telegram_sender
        self.target_chat_id = target_chat_id
        self.target_thread_id = target_thread_id
        self.model_name = model_name
        self.max_posts_per_run = max_posts_per_run

    @staticmethod
    def _is_refusal_like(summary: str) -> bool:
        normalized = " ".join(summary.lower().split())
        markers = (
            "не могу выполнить",
            "не могу создать",
            "не могу составить",
            "в переданных материалах",
            "что я могу сделать",
            "уточните, какой вариант",
            "предоставьте полный текст",
            "невозможно извлечь информацию",
            "недостаточно данных",
        )
        return any(marker in normalized for marker in markers)

    @staticmethod
    def _build_fallback_summary(posts) -> str:
        lines = ["Дайджест по новым текстовым постам:"]
        for index, post in enumerate(posts, start=1):
            compact = " ".join(post.content_text.split())
            if len(compact) > 280:
                compact = compact[:277].rstrip() + "..."
            lines.append(f"{index}. {compact} {post.external_post_url}")
        return "\n".join(lines)

    def _resolve_window_start(self, requested_start: str) -> str:
        latest_sent_window_end = self.digest_windows_repo.get_latest_sent_window_end()
        if latest_sent_window_end is None:
            return requested_start
        requested_dt = from_iso(requested_start)
        latest_sent_dt = from_iso(latest_sent_window_end)
        if requested_dt is None or latest_sent_dt is None:
            return latest_sent_window_end
        return to_iso(max(requested_dt, latest_sent_dt)) or requested_start

    async def run(self, context: DigestRunContext) -> str:
        window_start = self._resolve_window_start(context.window_start)
        window_id = self.digest_windows_repo.create_window(
            window_start=window_start,
            window_end=context.window_end,
            trigger_type=context.trigger_type,
            requested_by=context.requested_by,
        )
        self.digest_windows_repo.set_status(window_id, "running")

        posts = self.posts_repo.list_for_digest_window(
            window_start=window_start,
            window_end=context.window_end,
            limit=self.max_posts_per_run,
        )
        if not posts:
            self.digest_windows_repo.set_status(window_id, "skipped")
            return "No new eligible text posts for this digest window."

        for post in posts:
            self.digest_windows_repo.add_item(window_id, post.post_id)

        try:
            prompt = build_digest_prompt(posts)
            summary = await self.perplexity_client.summarize(prompt)
            summary = summary.strip()
            if not summary:
                raise DigestError("Model returned an empty digest.")
            if self._is_refusal_like(summary):
                self.logger.warning("Model returned refusal-like digest output; using fallback summary.")
                summary = self._build_fallback_summary(posts)
            message = await self.telegram_sender.send_digest(
                text=summary,
                chat_id=self.target_chat_id,
                thread_id=self.target_thread_id,
            )
            self.digests_repo.create_digest(
                window_id=window_id,
                target_chat_id=self.target_chat_id,
                target_thread_id=self.target_thread_id,
                telegram_message_id=getattr(message, "message_id", None),
                model_name=self.model_name,
                summary_text=summary,
                source_posts_count=len(posts),
            )
            self.digest_windows_repo.set_status(window_id, "sent")
            self.logger.info("Digest sent for window %s..%s", context.window_start, context.window_end)
            return f"Digest sent with {len(posts)} posts."
        except Exception:
            self.digest_windows_repo.set_status(window_id, "failed")
            raise
