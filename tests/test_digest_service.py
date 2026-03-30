from types import SimpleNamespace

from smartdigest_bot.digest.digest_service import DigestRunContext, DigestService
from smartdigest_bot.models import DigestCandidate


class FakePostsRepo:
    def list_for_digest_window(self, window_start: str, window_end: str, limit: int):
        del window_start, window_end, limit
        return [
            DigestCandidate(
                post_id=1,
                channel_username="example",
                external_post_url="https://t.me/example/1",
                content_text="Hello",
                published_at=None,
                has_audio=False,
            )
        ]


class FakeDigestWindowsRepo:
    def __init__(self) -> None:
        self.statuses = []
        self.items = []

    def create_window(self, window_start: str, window_end: str, trigger_type: str, requested_by: str | None) -> int:
        del window_start, window_end, trigger_type, requested_by
        return 1

    def set_status(self, window_id: int, status: str) -> None:
        self.statuses.append((window_id, status))

    def add_item(self, window_id: int, post_id: int) -> None:
        self.items.append((window_id, post_id))


class FakeDigestsRepo:
    def __init__(self) -> None:
        self.saved = False

    def create_digest(self, **kwargs) -> None:
        del kwargs
        self.saved = True


class FakePerplexityClient:
    async def summarize(self, prompt: str) -> str:
        assert "https://t.me/example/1" in prompt
        return "Digest text"


class FakeTelegramSender:
    async def send_digest(self, text: str, chat_id: str, thread_id: int | None):
        assert text == "Digest text"
        assert chat_id == "-1001"
        assert thread_id == 7
        return SimpleNamespace(message_id=99)


async def test_digest_service_sends_summary() -> None:
    windows = FakeDigestWindowsRepo()
    digests = FakeDigestsRepo()
    service = DigestService(
        posts_repo=FakePostsRepo(),
        digest_windows_repo=windows,
        digests_repo=digests,
        perplexity_client=FakePerplexityClient(),
        telegram_sender=FakeTelegramSender(),
        target_chat_id="-1001",
        target_thread_id=7,
        model_name="sonar-pro",
        max_posts_per_run=50,
    )
    result = await service.run(
        DigestRunContext(
            window_start="2026-03-30T00:00:00+00:00",
            window_end="2026-03-30T12:00:00+00:00",
            trigger_type="scheduled",
            requested_by="scheduler",
        )
    )
    assert result == "Digest sent with 1 posts."
    assert windows.statuses[-1] == (1, "sent")
    assert digests.saved is True
