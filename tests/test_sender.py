from types import SimpleNamespace

import pytest
from telegram.error import BadRequest

from smartdigest_bot.models import StoredPost
from smartdigest_bot.telegram.sender import TelegramSender


class FakeBot:
    def __init__(self, fail_first: bool, fail_text: str | None = None) -> None:
        self.fail_first = fail_first
        self.fail_text = fail_text or 'Can\'t parse entities: unsupported start tag "b…"'
        self.calls = []

    async def send_message(self, **kwargs):
        self.calls.append(kwargs)
        if self.fail_first and len(self.calls) == 1:
            raise BadRequest(self.fail_text)
        return SimpleNamespace(message_id=1)


@pytest.mark.asyncio
async def test_sender_falls_back_to_plain_text_on_bad_html() -> None:
    bot = FakeBot(fail_first=True)
    sender = TelegramSender(bot=bot, parse_mode="HTML", post_send_delay_seconds=0)
    post = StoredPost(
        id=1,
        channel_username="example",
        telegram_post_id=10,
        external_post_url="https://t.me/example/10",
        content_text="hello world",
        content_html="<b>broken",
        published_at=None,
        has_audio=False,
        has_video=False,
        has_photo=False,
        is_forwarded=False,
    )

    await sender.send_post(post, chat_id="-1001", thread_id=5)

    assert len(bot.calls) == 2
    assert bot.calls[0]["parse_mode"] == "HTML"
    assert "parse_mode" not in bot.calls[1]
    assert bot.calls[1]["text"].startswith("@example")


@pytest.mark.asyncio
async def test_sender_falls_back_to_plain_text_for_digest_bad_html() -> None:
    bot = FakeBot(fail_first=True, fail_text='Can\'t parse entities: unsupported start tag "100"')
    sender = TelegramSender(bot=bot, parse_mode="HTML", post_send_delay_seconds=0)

    await sender.send_digest("Рост <100% за день", chat_id="-1001", thread_id=5)

    assert len(bot.calls) == 2
    assert bot.calls[0]["parse_mode"] == "HTML"
    assert "parse_mode" not in bot.calls[1]
    assert bot.calls[1]["text"] == "Рост <100% за день"
