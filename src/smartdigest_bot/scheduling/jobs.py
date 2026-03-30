from __future__ import annotations

from datetime import timedelta
import logging

from smartdigest_bot.bootstrap.first_run import select_first_run_posts
from smartdigest_bot.digest.digest_service import DigestRunContext
from smartdigest_bot.utils.datetime import to_iso, utcnow


class Jobs:
    def __init__(
        self,
        channels_repo,
        posts_repo,
        deliveries_repo,
        fetcher,
        sender,
        digest_service,
        config,
    ) -> None:
        self.logger = logging.getLogger(__name__)
        self.channels_repo = channels_repo
        self.posts_repo = posts_repo
        self.deliveries_repo = deliveries_repo
        self.fetcher = fetcher
        self.sender = sender
        self.digest_service = digest_service
        self.config = config

    def _resolve_delivery_target(self, post) -> tuple[str, int | None]:
        if post.has_audio and self.config.telegram_audio_thread_id is not None:
            return self.config.telegram_audio_chat_id, self.config.telegram_audio_thread_id
        return self.config.telegram_forward_chat_id, self.config.telegram_forward_thread_id

    async def fetch_new_posts(self) -> None:
        for channel in self.channels_repo.list_active():
            self.logger.info("Checking @%s for new posts", channel["username"])
            fetched_posts = await self.fetcher.fetch_posts(channel["username"])
            if not fetched_posts:
                self.channels_repo.update_check_state(channel["id"], channel["last_seen_post_id"])
                self.logger.info("No parsable posts found for @%s", channel["username"])
                continue

            new_posts = [
                post
                for post in fetched_posts
                if channel["last_seen_post_id"] is None or post.telegram_post_id > channel["last_seen_post_id"]
            ]
            deliverable_posts = new_posts

            if channel["last_seen_post_id"] is None:
                deliverable_posts = select_first_run_posts(
                    new_posts,
                    mode=self.config.first_run_mode,
                    max_posts=self.config.first_run_max_posts_per_channel,
                )
                self.logger.info(
                    "First run for @%s: fetched=%s deliverable=%s mode=%s",
                    channel["username"],
                    len(new_posts),
                    len(deliverable_posts),
                    self.config.first_run_mode,
                )

            highest_seen = max(post.telegram_post_id for post in fetched_posts)
            stored_by_post_id = {}
            for post in new_posts:
                stored = self.posts_repo.upsert_post(channel["id"], channel["username"], post)
                stored_by_post_id[post.telegram_post_id] = stored

            for post in deliverable_posts:
                stored = stored_by_post_id[post.telegram_post_id]
                if self.deliveries_repo.is_delivered(stored.id):
                    self.logger.info(
                        "Skipping already delivered post @%s/%s",
                        stored.channel_username,
                        stored.telegram_post_id,
                    )
                    continue
                target_chat_id, target_thread_id = self._resolve_delivery_target(stored)
                message = await self.sender.send_post(
                    stored,
                    chat_id=target_chat_id,
                    thread_id=target_thread_id,
                )
                self.deliveries_repo.mark_delivered(
                    stored.id,
                    target_chat_id=target_chat_id,
                    target_thread_id=target_thread_id,
                    telegram_message_id=getattr(message, "message_id", None),
                )
                self.logger.info(
                    "Forwarded post @%s/%s to chat=%s thread=%s",
                    stored.channel_username,
                    stored.telegram_post_id,
                    target_chat_id,
                    target_thread_id,
                )

            self.channels_repo.update_check_state(channel["id"], highest_seen)

    async def run_scheduled_digest(self) -> str:
        end = utcnow()
        start = end.replace(microsecond=0) - timedelta(hours=self.config.digest_lookback_hours)
        return await self.digest_service.run(
            DigestRunContext(
                window_start=to_iso(start),
                window_end=to_iso(end),
                trigger_type="scheduled",
                requested_by="scheduler",
            )
        )
