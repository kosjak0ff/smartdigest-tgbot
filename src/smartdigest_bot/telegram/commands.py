from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from telegram import Update
from telegram.ext import ContextTypes

from smartdigest_bot.exceptions import DigestError
from smartdigest_bot.utils.datetime import to_iso, utcnow


@dataclass(slots=True)
class CommandDependencies:
    owner_user_id: int | None
    digest_callback: object
    health_callback: object
    lookback_hours: int


class CommandService:
    def __init__(self, deps: CommandDependencies) -> None:
        self.deps = deps

    def _is_owner(self, update: Update) -> bool:
        if self.deps.owner_user_id is None:
            return True
        user = update.effective_user
        return bool(user and user.id == self.deps.owner_user_id)

    async def _reject_if_needed(self, update: Update) -> bool:
        if self._is_owner(update):
            return False
        if update.effective_message:
            await update.effective_message.reply_text("This bot accepts commands only from its owner.")
        return True

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        del context
        if await self._reject_if_needed(update):
            return
        await update.effective_message.reply_text(
            "SmartDigest bot is running.\nCommands: /status, /digest_now"
        )

    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        del context
        if await self._reject_if_needed(update):
            return
        status_text = await self.deps.health_callback()
        await update.effective_message.reply_text(status_text)

    async def digest_now(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        del context
        if await self._reject_if_needed(update):
            return
        end = utcnow()
        start = end - timedelta(hours=self.deps.lookback_hours)
        try:
            result = await self.deps.digest_callback(
                window_start=to_iso(start),
                window_end=to_iso(end),
                trigger_type="manual",
                requested_by=f"telegram_user:{update.effective_user.id if update.effective_user else 'unknown'}",
            )
        except DigestError as exc:
            result = f"Digest failed: {exc}"
        await update.effective_message.reply_text(result)
