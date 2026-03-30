from __future__ import annotations

from telegram.ext import Application, ApplicationBuilder, CommandHandler

from smartdigest_bot.telegram.commands import CommandService


def build_application(token: str, commands: CommandService) -> Application:
    application = ApplicationBuilder().token(token).build()
    application.add_handler(CommandHandler("start", commands.start))
    application.add_handler(CommandHandler("status", commands.status))
    application.add_handler(CommandHandler("digest_now", commands.digest_now))
    return application
