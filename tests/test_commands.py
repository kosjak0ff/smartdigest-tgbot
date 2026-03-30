from types import SimpleNamespace

from smartdigest_bot.telegram.commands import CommandDependencies, CommandService


class FakeMessage:
    def __init__(self) -> None:
        self.sent = []

    async def reply_text(self, text: str) -> None:
        self.sent.append(text)


async def test_commands_reject_non_owner() -> None:
    message = FakeMessage()
    service = CommandService(
        CommandDependencies(
            owner_user_id=1,
            digest_callback=lambda **kwargs: kwargs,
            health_callback=lambda: "ok",
            lookback_hours=12,
        )
    )
    update = SimpleNamespace(
        effective_user=SimpleNamespace(id=2),
        effective_message=message,
    )
    await service.start(update, None)
    assert message.sent == ["This bot accepts commands only from its owner."]
