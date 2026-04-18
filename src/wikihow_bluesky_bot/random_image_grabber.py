from __future__ import annotations

from dataclasses import dataclass

from wikihow_bluesky_bot.types import SelectedImage
from wikihow_bluesky_bot.wikihow import WikiHowSelector


@dataclass(frozen=True, slots=True)
class WikiHowRandomImageGrabber:
    """Fetch a single random image candidate from wikiHow."""

    max_attempts: int

    def fetch_random_image(self) -> SelectedImage:
        selector = WikiHowSelector(max_attempts=self.max_attempts)
        return selector.select_random_image()
