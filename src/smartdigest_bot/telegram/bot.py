from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import Application, ApplicationBuilder, CommandHandler, ContextTypes

from smartdigest_bot.telegram.commands import CommandService


def build_application(token: str, commands: CommandService) -> Application:
    logger = logging.getLogger(__name__)

    async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        logger.exception("Unhandled Telegram update error", exc_info=context.error)
        if isinstance(update, Update) and update.effective_message:
            await update.effective_message.reply_text("Command failed. Please try again later.")

    application = ApplicationBuilder().token(token).build()
    application.add_handler(CommandHandler("start", commands.start))
    application.add_handler(CommandHandler("status", commands.status))
    application.add_handler(CommandHandler("digest_now", commands.digest_now))
    application.add_error_handler(error_handler)
    return application
