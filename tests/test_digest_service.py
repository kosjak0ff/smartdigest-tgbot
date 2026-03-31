from types import SimpleNamespace

from smartdigest_bot.digest.digest_service import DigestRunContext, DigestService
from smartdigest_bot.models import DigestCandidate


class FakePostsRepo:
    def __init__(self) -> None:
        self.calls = []

    def list_for_digest_window(self, window_start: str, window_end: str, limit: int):
        self.calls.append((window_start, window_end, limit))
        return [
            DigestCandidate(
                post_id=1,
                channel_username="example",
                external_post_url="https://t.me/example/1",
                content_text="Hello",
                published_at=None,
                has_audio=False,
                has_video=False,
                has_photo=False,
                is_forwarded=False,
            )
        ]


class FakeDigestWindowsRepo:
    def __init__(self) -> None:
        self.statuses = []
        self.items = []
        self.created = []
        self.latest_sent_window_end = None

    def create_window(self, window_start: str, window_end: str, trigger_type: str, requested_by: str | None) -> int:
        self.created.append((window_start, window_end, trigger_type, requested_by))
        return 1

    def set_status(self, window_id: int, status: str) -> None:
        self.statuses.append((window_id, status))

    def add_item(self, window_id: int, post_id: int) -> None:
        self.items.append((window_id, post_id))

    def get_latest_sent_window_end(self) -> str | None:
        return self.latest_sent_window_end


class FakeDigestsRepo:
    def __init__(self) -> None:
        self.saved = False

    def create_digest(self, **kwargs) -> None:
        del kwargs
        self.saved = True


class FakePerplexityClient:
    async def summarize(self, prompt: str) -> str:
        assert "https://t.me/example/1" in prompt
        assert "строго на русском языке" in prompt
        assert "НЕ добавляй внешние факты" in prompt
        return "Digest text"


class FakeTelegramSender:
    def __init__(self) -> None:
        self.sent = []

    async def send_digest(self, text: str, chat_id: str, thread_id: int | None):
        assert chat_id == "-1001"
        assert thread_id == 7
        self.sent.append(text)
        return SimpleNamespace(message_id=99, text=text)


async def test_digest_service_sends_summary() -> None:
    windows = FakeDigestWindowsRepo()
    digests = FakeDigestsRepo()
    posts_repo = FakePostsRepo()
    service = DigestService(
        posts_repo=posts_repo,
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
    assert posts_repo.calls == [("2026-03-30T00:00:00+00:00", "2026-03-30T12:00:00+00:00", 50)]
    assert digests.saved is True


class RefusalPerplexityClient:
    async def summarize(self, prompt: str) -> str:
        del prompt
        return "Я не могу выполнить этот запрос. Что я могу сделать: ..."


async def test_digest_service_uses_fallback_for_refusal_output() -> None:
    windows = FakeDigestWindowsRepo()
    digests = FakeDigestsRepo()
    sender = FakeTelegramSender()
    service = DigestService(
        posts_repo=FakePostsRepo(),
        digest_windows_repo=windows,
        digests_repo=digests,
        perplexity_client=RefusalPerplexityClient(),
        telegram_sender=sender,
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
    assert digests.saved is True
    assert sender.sent == ["Дайджест по новым текстовым постам:\n1. Hello https://t.me/example/1"]


async def test_digest_service_uses_last_sent_window_end_as_lower_bound() -> None:
    windows = FakeDigestWindowsRepo()
    windows.latest_sent_window_end = "2026-03-30T06:00:00+00:00"
    digests = FakeDigestsRepo()
    posts_repo = FakePostsRepo()
    service = DigestService(
        posts_repo=posts_repo,
        digest_windows_repo=windows,
        digests_repo=digests,
        perplexity_client=FakePerplexityClient(),
        telegram_sender=FakeTelegramSender(),
        target_chat_id="-1001",
        target_thread_id=7,
        model_name="sonar-pro",
        max_posts_per_run=50,
    )

    await service.run(
        DigestRunContext(
            window_start="2026-03-30T00:00:00+00:00",
            window_end="2026-03-30T12:00:00+00:00",
            trigger_type="scheduled",
            requested_by="scheduler",
        )
    )

    assert windows.created[0][0] == "2026-03-30T06:00:00+00:00"
    assert posts_repo.calls[0][0] == "2026-03-30T06:00:00+00:00"
