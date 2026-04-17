from __future__ import annotations

import io
from dataclasses import dataclass

import requests
from PIL import Image

from wikihow_bluesky_bot.types import PreparedImage


_BLUESKY_IMAGE_MAX_BYTES = 1_000_000


@dataclass(frozen=True, slots=True)
class ImageProcessor:
    user_agent: str
    timeout_seconds: int

    def prepare_for_bluesky(self, image_url: str) -> PreparedImage:
        source_bytes = self._download(image_url)
        with Image.open(io.BytesIO(source_bytes)) as source_image:
            working_image = source_image.copy()
            return _transcode_to_limit(working_image)

    def _download(self, image_url: str) -> bytes:
        response = requests.get(
            image_url,
            timeout=self.timeout_seconds,
            headers={"User-Agent": self.user_agent},
        )
        response.raise_for_status()
        if not response.content:
            raise RuntimeError("Downloaded image was empty")
        return response.content


def _transcode_to_limit(image: Image.Image) -> PreparedImage:
    preferred_formats = _preferred_formats(image.format)
    scale = 1.0

    for _ in range(8):
        scaled = _scale_image(image, scale)
        for fmt in preferred_formats:
            for quality in _quality_steps_for_format(fmt):
                encoded, mime = _encode_image(scaled, fmt=fmt, quality=quality)
                if len(encoded) <= _BLUESKY_IMAGE_MAX_BYTES:
                    return PreparedImage(
                        data=encoded,
                        mime_type=mime,
                        width=scaled.width,
                        height=scaled.height,
                    )
        scale *= 0.85

    raise RuntimeError("Could not reduce image below Bluesky 1,000,000-byte limit")


def _scale_image(image: Image.Image, scale: float) -> Image.Image:
    if scale >= 0.999:
        return image.copy()

    width = max(1, int(image.width * scale))
    height = max(1, int(image.height * scale))
    resized = image.resize(
        (width, height), Image.Resampling.LANCZOS
    )  # pyright: ignore[reportUnknownMemberType]
    return resized


def _preferred_formats(original: str | None) -> tuple[str, ...]:
    normalized = (original or "").upper()
    if normalized in {"JPEG", "JPG"}:
        return ("JPEG", "WEBP", "PNG")
    if normalized == "PNG":
        return ("PNG", "WEBP", "JPEG")
    if normalized == "WEBP":
        return ("WEBP", "JPEG", "PNG")
    return ("WEBP", "JPEG", "PNG")


def _quality_steps_for_format(fmt: str) -> tuple[int | None, ...]:
    if fmt in {"JPEG", "WEBP"}:
        return (92, 84, 76, 68, 60, 52)
    return (None,)


def _encode_image(
    image: Image.Image, *, fmt: str, quality: int | None
) -> tuple[bytes, str]:
    buffer = io.BytesIO()

    if fmt == "PNG":
        png_image = (
            image.convert("RGBA")
            if image.mode in {"RGBA", "LA"}
            else image.convert("RGB")
        )
        png_image.save(buffer, format="PNG", optimize=True)
        return buffer.getvalue(), "image/png"

    if fmt == "WEBP":
        webp_image = (
            image.convert("RGBA")
            if image.mode in {"RGBA", "LA"}
            else image.convert("RGB")
        )
        webp_image.save(
            buffer,
            format="WEBP",
            quality=quality if quality is not None else 80,
            method=6,
            exif=b"",
        )
        return buffer.getvalue(), "image/webp"

    rgb_image = image.convert("RGB")
    rgb_image.save(
        buffer,
        format="JPEG",
        quality=quality if quality is not None else 80,
        optimize=True,
        progressive=True,
        exif=b"",
    )
    return buffer.getvalue(), "image/jpeg"
