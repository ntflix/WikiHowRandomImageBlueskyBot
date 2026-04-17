from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class ArticleInfo:
    article_id: int
    title: str
    url: str


@dataclass(frozen=True, slots=True)
class ImageCandidate:
    src_url: str
    alt_text: str


@dataclass(frozen=True, slots=True)
class SelectedImage:
    article: ArticleInfo
    image: ImageCandidate


@dataclass(frozen=True, slots=True)
class PreparedImage:
    data: bytes
    mime_type: str
    width: int
    height: int


@dataclass(frozen=True, slots=True)
class PublishedPost:
    uri: str
    cid: str


@dataclass(frozen=True, slots=True)
class RunOutcome:
    posted: bool
    skipped_reason: str | None
    article_url: str | None
    image_url: str | None
    post_uri: str | None
    alt_text: str | None
    dry_run_image_path: str | None
    created_at: datetime
