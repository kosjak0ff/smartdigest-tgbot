from __future__ import annotations

from dataclasses import dataclass
import logging

from smartdigest_bot.digest.prompt_builder import build_digest_prompt
from smartdigest_bot.storage.digest_windows_repo import DigestWindowsRepository
from smartdigest_bot.storage.digests_repo import DigestsRepository
from smartdigest_bot.storage.posts_repo import PostsRepository


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

    async def run(self, context: DigestRunContext) -> str:
        window_id = self.digest_windows_repo.create_window(
            window_start=context.window_start,
            window_end=context.window_end,
            trigger_type=context.trigger_type,
            requested_by=context.requested_by,
        )
        self.digest_windows_repo.set_status(window_id, "running")

        posts = self.posts_repo.list_for_digest_window(
            window_start=context.window_start,
            window_end=context.window_end,
            limit=self.max_posts_per_run,
        )
        if not posts:
            self.digest_windows_repo.set_status(window_id, "skipped")
            return "No new posts for this digest window."

        for post in posts:
            self.digest_windows_repo.add_item(window_id, post.post_id)

        prompt = build_digest_prompt(posts)
        summary = await self.perplexity_client.summarize(prompt)
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
