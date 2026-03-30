from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger


def build_scheduler(config, jobs) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=config.timezone)
    scheduler.add_job(
        jobs.fetch_new_posts,
        trigger=IntervalTrigger(minutes=config.fetch_interval_minutes),
        id="fetch_new_posts",
        max_instances=1,
        coalesce=True,
    )

    for index, value in enumerate(config.digest_schedule_times):
        hour_str, minute_str = value.split(":")
        scheduler.add_job(
            jobs.run_scheduled_digest,
            trigger=CronTrigger(hour=int(hour_str), minute=int(minute_str), timezone=config.timezone),
            id=f"digest_{index}",
            max_instances=1,
            coalesce=True,
        )
    return scheduler
