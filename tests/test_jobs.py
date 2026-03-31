from types import SimpleNamespace

from smartdigest_bot.models import ParsedPost, StoredPost
from smartdigest_bot.scheduling.jobs import Jobs


class FakeChannelsRepo:
    def list_active(self):
        return [
            {
                "id": 1,
                "username": "example",
                "last_seen_post_id": None,
            }
        ]

    def update_check_state(self, channel_id: int, last_seen_post_id: int | None) -> None:
        self.updated = (channel_id, last_seen_post_id)


class FakePostsRepo:
    def upsert_post(self, channel_id: int, channel_username: str, post: ParsedPost) -> StoredPost:
        del channel_id
        return StoredPost(
            id=100 + post.telegram_post_id,
            channel_username=channel_username,
            telegram_post_id=post.telegram_post_id,
            external_post_url=post.external_post_url,
            content_text=post.content_text,
            content_html=post.content_html,
            published_at=post.published_at,
            has_audio=post.has_audio,
            has_video=post.has_video,
            has_photo=post.has_photo,
            is_forwarded=post.is_forwarded,
        )


class FakeDeliveriesRepo:
    def __init__(self) -> None:
        self.marked = []

    def is_delivered(self, post_id: int) -> bool:
        del post_id
        return False

    def mark_delivered(self, post_id: int, target_chat_id: str, target_thread_id: int | None, telegram_message_id: int | None) -> None:
        self.marked.append((post_id, target_chat_id, target_thread_id, telegram_message_id))


class FakeFetcher:
    async def fetch_posts(self, channel_username: str):
        del channel_username
        return [
            ParsedPost(
                telegram_post_id=10,
                external_post_url="https://t.me/example/10",
                content_text="Audio update",
                content_html="Audio update",
                published_at=None,
                author_name=None,
                has_audio=True,
                has_video=False,
                has_photo=False,
                is_forwarded=False,
                raw_html="<div></div>",
            )
        ]


class FakeSender:
    def __init__(self) -> None:
        self.calls = []

    async def send_post(self, post: StoredPost, chat_id: str, thread_id: int | None):
        self.calls.append((post.telegram_post_id, chat_id, thread_id, post.has_audio, post.has_video))
        return SimpleNamespace(message_id=555)


class FakeDigestService:
    async def run(self, context):
        del context
        return "ok"


async def test_audio_posts_go_to_audio_topic() -> None:
    channels_repo = FakeChannelsRepo()
    posts_repo = FakePostsRepo()
    deliveries_repo = FakeDeliveriesRepo()
    sender = FakeSender()
    jobs = Jobs(
        channels_repo=channels_repo,
        posts_repo=posts_repo,
        deliveries_repo=deliveries_repo,
        fetcher=FakeFetcher(),
        sender=sender,
        digest_service=FakeDigestService(),
        config=SimpleNamespace(
            first_run_mode="send_recent",
            first_run_max_posts_per_channel=1,
            telegram_forward_chat_id="-1001",
            telegram_forward_thread_id=10,
            telegram_audio_chat_id="-1001",
            telegram_audio_thread_id=20,
            digest_lookback_hours=12,
        ),
    )

    await jobs.fetch_new_posts()

    assert sender.calls == [(10, "-1001", 20, True, False)]
    assert deliveries_repo.marked == [(110, "-1001", 20, 555)]


class FakeVideoFetcher:
    async def fetch_posts(self, channel_username: str):
        del channel_username
        return [
            ParsedPost(
                telegram_post_id=11,
                external_post_url="https://t.me/example/11",
                content_text="[Video post without text]",
                content_html="[Video post without text]",
                published_at=None,
                author_name=None,
                has_audio=False,
                has_video=True,
                has_photo=False,
                is_forwarded=False,
                raw_html="<div></div>",
            )
        ]


async def test_video_posts_go_to_audio_topic() -> None:
    channels_repo = FakeChannelsRepo()
    posts_repo = FakePostsRepo()
    deliveries_repo = FakeDeliveriesRepo()
    sender = FakeSender()
    jobs = Jobs(
        channels_repo=channels_repo,
        posts_repo=posts_repo,
        deliveries_repo=deliveries_repo,
        fetcher=FakeVideoFetcher(),
        sender=sender,
        digest_service=FakeDigestService(),
        config=SimpleNamespace(
            first_run_mode="send_recent",
            first_run_max_posts_per_channel=1,
            telegram_forward_chat_id="-1001",
            telegram_forward_thread_id=10,
            telegram_audio_chat_id="-1001",
            telegram_audio_thread_id=20,
            digest_lookback_hours=12,
        ),
    )

    await jobs.fetch_new_posts()

    assert sender.calls == [(11, "-1001", 20, False, True)]
    assert deliveries_repo.marked == [(111, "-1001", 20, 555)]


class FakeFilteredFetcher:
    async def fetch_posts(self, channel_username: str):
        del channel_username
        return [
            ParsedPost(
                telegram_post_id=12,
                external_post_url="https://t.me/example/12",
                content_text="Photo caption",
                content_html="Photo caption",
                published_at=None,
                author_name=None,
                has_audio=False,
                has_video=False,
                has_photo=True,
                is_forwarded=False,
                raw_html="<div></div>",
            ),
            ParsedPost(
                telegram_post_id=13,
                external_post_url="https://t.me/example/13",
                content_text="Forwarded text",
                content_html="Forwarded text",
                published_at=None,
                author_name=None,
                has_audio=False,
                has_video=False,
                has_photo=False,
                is_forwarded=True,
                raw_html="<div></div>",
            ),
        ]


async def test_photo_and_forwarded_posts_are_not_delivered() -> None:
    channels_repo = FakeChannelsRepo()
    posts_repo = FakePostsRepo()
    deliveries_repo = FakeDeliveriesRepo()
    sender = FakeSender()
    jobs = Jobs(
        channels_repo=channels_repo,
        posts_repo=posts_repo,
        deliveries_repo=deliveries_repo,
        fetcher=FakeFilteredFetcher(),
        sender=sender,
        digest_service=FakeDigestService(),
        config=SimpleNamespace(
            first_run_mode="send_recent",
            first_run_max_posts_per_channel=10,
            telegram_forward_chat_id="-1001",
            telegram_forward_thread_id=10,
            telegram_audio_chat_id="-1001",
            telegram_audio_thread_id=20,
            digest_lookback_hours=12,
        ),
    )

    await jobs.fetch_new_posts()

    assert sender.calls == []
    assert deliveries_repo.marked == []
