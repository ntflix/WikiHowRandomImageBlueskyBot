from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import cast

from wikihow_bluesky_bot.bot import WikiHowBlueskyBot
from wikihow_bluesky_bot.config import AppConfig, load_config
from wikihow_bluesky_bot.logging_config import configure_logging
from wikihow_bluesky_bot.scheduler import run_scheduler

logger = logging.getLogger(__name__)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="wikiHow random image Bluesky bot")
    _ = parser.add_argument(
        "--dotenv",
        type=Path,
        default=None,
        help="Path to .env file",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    run_once_parser = subparsers.add_parser(
        "run-once", help="Run a single publish attempt"
    )
    _ = run_once_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Override config and run without posting to Bluesky",
    )

    _ = subparsers.add_parser("run-scheduler", help="Run the cron scheduler")
    return parser


def _override_dry_run(config: AppConfig, enabled: bool) -> AppConfig:
    if not enabled:
        return config
    return AppConfig(
        bluesky_identifier=config.bluesky_identifier,
        bluesky_app_password=config.bluesky_app_password,
        cron_expression=config.cron_expression,
        timezone=config.timezone,
        database_path=config.database_path,
        dedup_window_hours=config.dedup_window_hours,
        max_article_attempts=config.max_article_attempts,
        dry_run=True,
        http_timeout_seconds=config.http_timeout_seconds,
        user_agent=config.user_agent,
        alt_gen_enabled=config.alt_gen_enabled,
        alt_gen_endpoint=config.alt_gen_endpoint,
        alt_gen_api_key=config.alt_gen_api_key,
        alt_gen_model=config.alt_gen_model,
        alt_gen_timeout_seconds=config.alt_gen_timeout_seconds,
    )


def main() -> int:
    configure_logging()
    parser = _build_parser()
    args = parser.parse_args()
    dotenv_path = cast(Path | None, getattr(args, "dotenv", None))
    command = cast(str, getattr(args, "command", ""))

    config = load_config(dotenv_path)

    if command == "run-once":
        dry_run_flag = cast(bool, getattr(args, "dry_run", False))
        config = _override_dry_run(config, dry_run_flag)
        bot = WikiHowBlueskyBot(config)
        outcome = bot.run_once()
        logger.info(
            "Run complete posted=%s reason=%s article=%s image=%s post=%s",
            outcome.posted,
            outcome.skipped_reason,
            outcome.article_url,
            outcome.image_url,
            outcome.post_uri,
        )
        if config.dry_run and outcome.alt_text is not None:
            print("Dry-run alt text:")
            print(outcome.alt_text)
        if config.dry_run and outcome.dry_run_image_path is not None:
            print(f"Dry-run image written: {outcome.dry_run_image_path}")
        return 0

    if command == "run-scheduler":
        bot = WikiHowBlueskyBot(config)
        run_scheduler(
            bot=bot, cron_expression=config.cron_expression, timezone=config.timezone
        )
        return 0

    parser.error(f"Unknown command: {command}")


if __name__ == "__main__":
    raise SystemExit(main())
