# pyright: reportMissingTypeStubs=false

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import requests
from atproto_client.exceptions import RequestException as AtprotoRequestException

from wikihow_bluesky_bot.alt_text_generator import OpenAICompatibleAltTextGenerator
from wikihow_bluesky_bot.bluesky import BlueskyPublisher
from wikihow_bluesky_bot.image_processing import ImageProcessor
from wikihow_bluesky_bot.persistence import StateStore, sha256_hex
from wikihow_bluesky_bot.retry import retry_with_backoff
from wikihow_bluesky_bot.types import RunOutcome, SelectedImage


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class OpenAIBlueskyUploader:
    image_processor: ImageProcessor
    publisher: BlueskyPublisher
    store: StateStore
    dedup_window_hours: int
    dry_run: bool
    alt_text_generator: OpenAICompatibleAltTextGenerator | None = None

    def upload_selected_image(self, selected: SelectedImage) -> RunOutcome:
        source_alt = selected.image.alt_text

        generated_alt = self._safe_generate_alt(selected.image.src_url)
        if generated_alt:
            source_alt = generated_alt + "\n" + source_alt

        prepared = retry_with_backoff(
            lambda: self.image_processor.prepare_for_bluesky(selected.image.src_url),
            retries=3,
            base_delay_seconds=1.0,
            retryable=_is_retryable_exception,
        )

        post_alt = build_post_alt_text(
            wikihow_image_alt=source_alt,
            article_url=selected.article.url,
        )

        image_hash = sha256_hex(prepared.data)
        if (not self.dry_run) and self.store.recent_duplicate_exists(
            image_hash=image_hash,
            within_hours=self.dedup_window_hours,
        ):
            logger.info("Skipping duplicate image hash in dedup window")
            return RunOutcome(
                posted=False,
                skipped_reason="duplicate_image_hash",
                article_url=selected.article.url,
                image_url=selected.image.src_url,
                post_uri=None,
                alt_text=None,
                dry_run_image_path=None,
                created_at=datetime.now(tz=UTC),
            )

        published = retry_with_backoff(
            lambda: self.publisher.publish_image_only(
                image=prepared,
                alt_text=post_alt,
            ),
            retries=3,
            base_delay_seconds=1.0,
            retryable=_is_retryable_exception,
        )

        if not self.dry_run:
            self.store.record_post(
                image_url=selected.image.src_url,
                article_url=selected.article.url,
                image_hash=image_hash,
                published_post=published,
            )
            dry_run_image_path = None
        else:
            dry_run_image_path = _write_dry_run_image(prepared.data, prepared.mime_type)

        logger.info("Published post: %s", published.uri)
        return RunOutcome(
            posted=True,
            skipped_reason=None,
            article_url=selected.article.url,
            image_url=selected.image.src_url,
            post_uri=published.uri,
            alt_text=post_alt,
            dry_run_image_path=dry_run_image_path,
            created_at=datetime.now(tz=UTC),
        )

    def _safe_generate_alt(self, image_url: str) -> str | None:
        if self.alt_text_generator is None:
            return None
        try:
            return self.alt_text_generator.generate_alt_text(
                image_url=image_url,
            )
        except Exception:
            logger.warning(
                "Alt text generation request failed; falling back to extracted alt"
            )
            return None


def _is_retryable_exception(exc: Exception) -> bool:
    if isinstance(exc, requests.RequestException):
        return True
    if isinstance(exc, AtprotoRequestException):
        status_code = getattr(exc, "status_code", None)
        return status_code in {429, 500, 502, 503, 504}
    return False


def _extension_for_mime(mime_type: str) -> str:
    mapping = {
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
    }
    return mapping.get(mime_type.lower(), "img")


def _write_dry_run_image(image_data: bytes, mime_type: str) -> str:
    timestamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    extension = _extension_for_mime(mime_type)
    output_path = Path.cwd() / f"dry-run-image-{timestamp}.{extension}"
    output_path.write_bytes(image_data)
    return str(output_path)


def build_post_alt_text(*, wikihow_image_alt: str, article_url: str) -> str:
    cleaned_alt = wikihow_image_alt.strip() or "Image from wikiHow"
    return f"{cleaned_alt}\nImage from {article_url.strip()}"
