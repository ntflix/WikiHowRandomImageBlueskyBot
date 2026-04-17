from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


class ConfigError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class AppConfig:
    bluesky_identifier: str
    bluesky_app_password: str
    cron_expression: str
    timezone: str
    database_path: Path
    dedup_window_hours: int
    max_article_attempts: int
    dry_run: bool
    http_timeout_seconds: int
    user_agent: str
    alt_gen_enabled: bool
    alt_gen_endpoint: str
    alt_gen_api_key: str | None
    alt_gen_model: str
    alt_gen_timeout_seconds: int


def _parse_bool(raw: str, *, key: str) -> bool:
    normalized = raw.strip().lower()
    truthy = {"1", "true", "yes", "on"}
    falsy = {"0", "false", "no", "off"}
    if normalized in truthy:
        return True
    if normalized in falsy:
        return False
    msg = f"Invalid boolean value for {key}: {raw!r}"
    raise ConfigError(msg)


def _read_required(name: str, *, allow_empty_in_dry_run: bool, dry_run: bool) -> str:
    raw = os.getenv(name, "")
    if raw or (allow_empty_in_dry_run and dry_run):
        return raw
    msg = f"Missing required environment variable: {name}"
    raise ConfigError(msg)


def load_config(dotenv_path: Path | None = None) -> AppConfig:
    _ = load_dotenv(dotenv_path=dotenv_path)

    dry_run = _parse_bool(os.getenv("BOT_DRY_RUN", "false"), key="BOT_DRY_RUN")

    bluesky_identifier = _read_required(
        "BLUESKY_IDENTIFIER",
        allow_empty_in_dry_run=True,
        dry_run=dry_run,
    )
    bluesky_app_password = _read_required(
        "BLUESKY_APP_PASSWORD",
        allow_empty_in_dry_run=True,
        dry_run=dry_run,
    )

    cron_expression = os.getenv("BOT_CRON", "0 */6 * * *").strip()
    if not cron_expression:
        raise ConfigError("BOT_CRON must not be empty")

    timezone = os.getenv("BOT_TIMEZONE", "UTC").strip()
    if not timezone:
        raise ConfigError("BOT_TIMEZONE must not be empty")

    database_path = Path(os.getenv("BOT_DATABASE_PATH", ".state/bot_state.sqlite3"))

    try:
        dedup_window_hours = int(os.getenv("BOT_DEDUP_WINDOW_HOURS", "168"))
    except ValueError as exc:
        raise ConfigError("BOT_DEDUP_WINDOW_HOURS must be an integer") from exc
    if dedup_window_hours < 1:
        raise ConfigError("BOT_DEDUP_WINDOW_HOURS must be >= 1")

    try:
        max_article_attempts = int(os.getenv("BOT_MAX_ARTICLE_ATTEMPTS", "6"))
    except ValueError as exc:
        raise ConfigError("BOT_MAX_ARTICLE_ATTEMPTS must be an integer") from exc
    if max_article_attempts < 1:
        raise ConfigError("BOT_MAX_ARTICLE_ATTEMPTS must be >= 1")

    try:
        http_timeout_seconds = int(os.getenv("BOT_HTTP_TIMEOUT_SECONDS", "20"))
    except ValueError as exc:
        raise ConfigError("BOT_HTTP_TIMEOUT_SECONDS must be an integer") from exc
    if http_timeout_seconds < 1:
        raise ConfigError("BOT_HTTP_TIMEOUT_SECONDS must be >= 1")

    user_agent = os.getenv(
        "BOT_USER_AGENT", "wikihow-random-image-bluesky-bot/0.1.0"
    ).strip()
    if not user_agent:
        raise ConfigError("BOT_USER_AGENT must not be empty")

    alt_gen_enabled = _parse_bool(
        os.getenv("ALT_GEN_ENABLED", "false"),
        key="ALT_GEN_ENABLED",
    )
    alt_gen_endpoint = os.getenv(
        "ALT_GEN_ENDPOINT", "https://api.openai.com/v1/responses"
    ).strip()
    if not alt_gen_endpoint:
        raise ConfigError("ALT_GEN_ENDPOINT must not be empty")

    alt_gen_api_key = os.getenv("ALT_GEN_API_KEY") or None
    alt_gen_model = os.getenv("ALT_GEN_MODEL", "gpt-4o-mini").strip()
    if not alt_gen_model:
        raise ConfigError("ALT_GEN_MODEL must not be empty")

    try:
        alt_gen_timeout_seconds = int(
            os.getenv("ALT_GEN_TIMEOUT_SECONDS", str(http_timeout_seconds))
        )
    except ValueError as exc:
        raise ConfigError("ALT_GEN_TIMEOUT_SECONDS must be an integer") from exc
    if alt_gen_timeout_seconds < 1:
        raise ConfigError("ALT_GEN_TIMEOUT_SECONDS must be >= 1")

    if alt_gen_enabled and not alt_gen_api_key:
        raise ConfigError("ALT_GEN_ENABLED=true requires ALT_GEN_API_KEY")

    return AppConfig(
        bluesky_identifier=bluesky_identifier,
        bluesky_app_password=bluesky_app_password,
        cron_expression=cron_expression,
        timezone=timezone,
        database_path=database_path,
        dedup_window_hours=dedup_window_hours,
        max_article_attempts=max_article_attempts,
        dry_run=dry_run,
        http_timeout_seconds=http_timeout_seconds,
        user_agent=user_agent,
        alt_gen_enabled=alt_gen_enabled,
        alt_gen_endpoint=alt_gen_endpoint,
        alt_gen_api_key=alt_gen_api_key,
        alt_gen_model=alt_gen_model,
        alt_gen_timeout_seconds=alt_gen_timeout_seconds,
    )
