from __future__ import annotations

import random
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from bs4.element import Tag

from wikihow_bluesky_bot.types import ArticleInfo, ImageCandidate, SelectedImage

from whapi import get_html, random_article, return_details  # type: ignore[import-untyped]


_BASE_URL = "https://www.wikihow.com"

_ARTICLE_BODY_SELECTORS: tuple[str, ...] = (
    "article",
    "main",
    "div.mw-parser-output",
    "div#content_wrapper",
    "div#bodycontents",
    "div#mf-section-0",
    "div[id^='mf-section-']",
)

_NON_BODY_CLASS_TOKENS: tuple[str, ...] = (
    "author",
    "avatar",
    "byline",
    "community",
    "footer",
    "header",
    "icon",
    "logo",
    "profile",
    "related",
    "sidebar",
)


@dataclass(frozen=True, slots=True)
class WikiHowSelector:
    max_attempts: int

    def select_random_image(self, *, rng: random.Random | None = None) -> SelectedImage:
        chooser = rng or random.Random()

        for _ in range(self.max_attempts):
            article_id = _coerce_random_article_id(random_article())
            details = return_details(article_id)
            article = ArticleInfo(
                article_id=article_id,
                title=details["title"],
                url=details["url"],
            )

            html = get_html(article_id)
            candidates = extract_image_candidates_from_html(html, article.url)
            if not candidates:
                continue

            chosen = chooser.choice(candidates)
            return SelectedImage(article=article, image=chosen)

        msg = "Could not find an article with at least one valid image"
        raise RuntimeError(msg)


def _coerce_random_article_id(value: int | list[int]) -> int:
    if isinstance(value, int):
        return value
    if not value:
        raise RuntimeError("random_article returned an empty list")
    return int(value[0])


def _normalize_src(src: str, base_url: str) -> str | None:
    trimmed = src.strip()
    if not trimmed or trimmed.startswith("data:"):
        return None

    if trimmed.startswith("//"):
        normalized = f"https:{trimmed}"
    else:
        normalized = urljoin(base_url, trimmed)

    parsed = urlparse(normalized)
    if parsed.scheme not in {"http", "https"}:
        return None

    return normalized


def extract_image_candidates_from_html(
    html: str, base_url: str = _BASE_URL
) -> list[ImageCandidate]:
    soup = BeautifulSoup(html, "html.parser")
    results: list[ImageCandidate] = []
    seen_src_urls: set[str] = set()

    for img in _iter_article_body_images(soup):
        src_value = _extract_preferred_src(img)
        if src_value is None:
            continue

        normalized_src = _normalize_src(src_value, base_url)
        if normalized_src is None:
            continue

        if normalized_src.lower().endswith(".svg"):
            continue

        if normalized_src in seen_src_urls:
            continue

        alt_text = _string_attr(img, "alt")
        results.append(ImageCandidate(src_url=normalized_src, alt_text=alt_text))
        seen_src_urls.add(normalized_src)

    return results


def _iter_article_body_images(soup: BeautifulSoup) -> list[Tag]:
    body_roots = _find_article_body_roots(soup)
    if not body_roots:
        return []

    images: list[Tag] = []
    for root in body_roots:
        for image in root.find_all("img"):
            if not _is_non_body_image(image):
                images.append(image)
    return images


def _find_article_body_roots(soup: BeautifulSoup) -> list[Tag]:
    roots: list[Tag] = []
    for selector in _ARTICLE_BODY_SELECTORS:
        for node in soup.select(selector):
            roots.append(node)

    if roots:
        return roots

    fallback = soup.find("body")
    if isinstance(fallback, Tag):
        return [fallback]
    return []


def _is_non_body_image(image: Tag) -> bool:
    # Exclude utility/profile images commonly outside article content (author cards, avatars, logos).
    classes = _class_tokens(image)
    if any(
        token in class_name
        for token in _NON_BODY_CLASS_TOKENS
        for class_name in classes
    ):
        return True

    src_value = image.get("src")
    if isinstance(src_value, str):
        src_lower = src_value.lower()
        if any(token in src_lower for token in _NON_BODY_CLASS_TOKENS):
            return True

    for ancestor in image.parents:
        ancestor_classes = _class_tokens(ancestor)
        if any(
            token in class_name
            for token in _NON_BODY_CLASS_TOKENS
            for class_name in ancestor_classes
        ):
            return True

    return False


def _class_tokens(node: Tag) -> list[str]:
    raw_classes = node.get("class")
    if raw_classes is None:
        return []
    if isinstance(raw_classes, str):
        return [token.lower() for token in raw_classes.split() if token]
    return [str(value).lower() for value in raw_classes]


def _extract_preferred_src(image: Tag) -> str | None:
    src = _string_attr(image, "src")
    if src and not _looks_like_placeholder_src(src):
        return src

    for attribute in ("data-src", "data-original", "data-lazy-src"):
        value = image.get(attribute)
        if isinstance(value, str) and value.strip():
            return value.strip()

    if src:
        return src
    return None


def _string_attr(node: Tag, attribute: str) -> str:
    value = node.get(attribute)
    if isinstance(value, str):
        return value.strip()
    return ""


def _looks_like_placeholder_src(src: str) -> bool:
    lowered = src.lower()
    placeholder_tokens = (
        "pixel",
        "spacer",
        "placeholder",
        "blank.gif",
        "transparent.gif",
    )
    return any(token in lowered for token in placeholder_tokens)
