from __future__ import annotations

import logging

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from wikihow_bluesky_bot.bot import WikiHowBlueskyBot

logger = logging.getLogger(__name__)


def run_scheduler(
    *, bot: WikiHowBlueskyBot, cron_expression: str, timezone: str
) -> None:
    scheduler = BlockingScheduler(timezone=timezone)
    trigger = CronTrigger.from_crontab(cron_expression, timezone=timezone)

    scheduler.add_job(
        bot.run_once, trigger=trigger, id="wikihow_bluesky_post", replace_existing=True
    )
    logger.info("Scheduler started with cron=%s timezone=%s", cron_expression, timezone)
    scheduler.start()
