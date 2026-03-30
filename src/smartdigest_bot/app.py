from __future__ import annotations

import asyncio
import logging
import signal

from smartdigest_bot.bootstrap.channels_loader import load_channels
from smartdigest_bot.config import load_config
from smartdigest_bot.digest.digest_service import DigestRunContext, DigestService
from smartdigest_bot.digest.perplexity_client import PerplexityClient
from smartdigest_bot.fetching.channel_fetcher import ChannelFetcher
from smartdigest_bot.logging_setup import configure_logging
from smartdigest_bot.scheduling.jobs import Jobs
from smartdigest_bot.scheduling.scheduler import build_scheduler
from smartdigest_bot.storage.channels_repo import ChannelsRepository
from smartdigest_bot.storage.db import connect
from smartdigest_bot.storage.deliveries_repo import DeliveriesRepository
from smartdigest_bot.storage.digest_windows_repo import DigestWindowsRepository
from smartdigest_bot.storage.digests_repo import DigestsRepository
from smartdigest_bot.storage.migrations import migrate
from smartdigest_bot.storage.posts_repo import PostsRepository
from smartdigest_bot.telegram.bot import build_application
from smartdigest_bot.telegram.commands import CommandDependencies, CommandService
from smartdigest_bot.telegram.sender import TelegramSender


async def async_main() -> None:
    config = load_config()
    configure_logging(config.log_level, config.log_file_path)
    logger = logging.getLogger(__name__)

    connection = connect(config.database_path)
    migrate(connection)

    channels = load_channels(config.channels_file)
    channels_repo = ChannelsRepository(connection)
    posts_repo = PostsRepository(connection)
    deliveries_repo = DeliveriesRepository(connection)
    digest_windows_repo = DigestWindowsRepository(connection)
    digests_repo = DigestsRepository(connection)
    channels_repo.sync(channels)

    fetcher = ChannelFetcher(config.http_timeout_seconds, config.http_user_agent)
    perplexity_client = PerplexityClient(
        api_key=config.perplexity_api_key,
        model=config.perplexity_model,
        base_url=config.perplexity_base_url,
        timeout_seconds=config.http_timeout_seconds,
    )

    command_placeholder = {}
    application = build_application(
        token=config.telegram_bot_token,
        commands=CommandService(
            CommandDependencies(
                owner_user_id=config.telegram_owner_user_id,
                digest_callback=lambda **kwargs: command_placeholder["digest_callback"](**kwargs),
                health_callback=lambda: command_placeholder["health_callback"](),
                lookback_hours=config.digest_lookback_hours,
            )
        ),
    )
    sender = TelegramSender(
        bot=application.bot,
        parse_mode=config.telegram_parse_mode,
        post_send_delay_seconds=config.post_send_delay_seconds,
    )
    digest_service = DigestService(
        posts_repo=posts_repo,
        digest_windows_repo=digest_windows_repo,
        digests_repo=digests_repo,
        perplexity_client=perplexity_client,
        telegram_sender=sender,
        target_chat_id=config.telegram_digest_chat_id,
        target_thread_id=config.telegram_digest_thread_id,
        model_name=config.perplexity_model,
        max_posts_per_run=config.digest_max_posts_per_run,
    )
    jobs = Jobs(
        channels_repo=channels_repo,
        posts_repo=posts_repo,
        deliveries_repo=deliveries_repo,
        fetcher=fetcher,
        sender=sender,
        digest_service=digest_service,
        config=config,
    )
    scheduler = build_scheduler(config, jobs)

    async def command_digest_callback(**kwargs: str) -> str:
        return await digest_service.run(
            DigestRunContext(
                window_start=kwargs["window_start"],
                window_end=kwargs["window_end"],
                trigger_type=kwargs["trigger_type"],
                requested_by=kwargs["requested_by"],
            )
        )

    async def health_callback() -> str:
        active_channels = len(channels_repo.list_active())
        return (
            "SmartDigest is healthy.\n"
            f"Channels: {active_channels}\n"
            f"Fetch interval: {config.fetch_interval_minutes} min\n"
            f"Digest times: {', '.join(config.digest_schedule_times)}"
        )

    command_placeholder["digest_callback"] = command_digest_callback
    command_placeholder["health_callback"] = health_callback

    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop_event.set)

    logger.info("Starting Telegram application")
    await application.initialize()
    await application.start()
    await application.updater.start_polling()

    logger.info("Running initial channel fetch on startup")
    await jobs.fetch_new_posts()

    logger.info("Starting scheduler")
    scheduler.start()

    try:
        await stop_event.wait()
    finally:
        logger.info("Stopping scheduler and clients")
        scheduler.shutdown(wait=False)
        await application.updater.stop()
        await application.stop()
        await application.shutdown()
        await fetcher.close()
        await perplexity_client.close()
        connection.close()


def run() -> None:
    asyncio.run(async_main())
