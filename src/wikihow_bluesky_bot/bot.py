# pyright: reportMissingTypeStubs=false

from __future__ import annotations

import logging

from wikihow_bluesky_bot.alt_text_generator import (
    OpenAICompatibleAltTextConfig,
    OpenAICompatibleAltTextGenerator,
)
from wikihow_bluesky_bot.bluesky import BlueskyPublisher
from wikihow_bluesky_bot.config import AppConfig
from wikihow_bluesky_bot.image_processing import ImageProcessor
from wikihow_bluesky_bot.openai_bluesky_uploader import OpenAIBlueskyUploader
from wikihow_bluesky_bot.persistence import StateStore
from wikihow_bluesky_bot.random_image_grabber import WikiHowRandomImageGrabber
from wikihow_bluesky_bot.types import RunOutcome


logger = logging.getLogger(__name__)


class WikiHowBlueskyBot:
    _config: AppConfig
    _grabber: WikiHowRandomImageGrabber
    _uploader: OpenAIBlueskyUploader
    _alt_text_generator: OpenAICompatibleAltTextGenerator | None

    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._grabber = WikiHowRandomImageGrabber(
            max_attempts=config.max_article_attempts
        )
        if config.alt_gen_enabled and config.alt_gen_api_key is not None:
            self._alt_text_generator = OpenAICompatibleAltTextGenerator(
                OpenAICompatibleAltTextConfig(
                    endpoint=config.alt_gen_endpoint,
                    api_key=config.alt_gen_api_key,
                    model=config.alt_gen_model,
                    timeout_seconds=config.alt_gen_timeout_seconds,
                )
            )
        else:
            self._alt_text_generator = None

        self._uploader = OpenAIBlueskyUploader(
            image_processor=ImageProcessor(
                user_agent=config.user_agent,
                timeout_seconds=config.http_timeout_seconds,
            ),
            publisher=BlueskyPublisher(
                identifier=config.bluesky_identifier,
                app_password=config.bluesky_app_password,
                dry_run=config.dry_run,
            ),
            store=StateStore(config.database_path),
            dedup_window_hours=config.dedup_window_hours,
            dry_run=config.dry_run,
            alt_text_generator=self._alt_text_generator,
        )

    def run_once(self) -> RunOutcome:
        selected = self._grabber.fetch_random_image()
        return self._uploader.upload_selected_image(selected)
