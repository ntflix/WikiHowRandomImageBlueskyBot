import io
import unittest

from PIL import Image

from wikihow_bluesky_bot.image_processing import (
    _transcode_to_limit,
)  # pyright: ignore[reportPrivateUsage]


class ImageProcessingTests(unittest.TestCase):
    def test_transcode_to_limit_reduces_large_noisy_image_under_bluesky_limit(
        self,
    ) -> None:
        width = 2200
        height = 2200

        # Generate deterministic high-entropy RGB bytes so compression must work hard.
        rgb_bytes = bytes((i * 37) % 256 for i in range(width * height * 3))
        source = Image.frombytes("RGB", (width, height), rgb_bytes)
        source.format = "PNG"

        prepared = _transcode_to_limit(source)

        self.assertLessEqual(len(prepared.data), 1_000_000)
        self.assertLessEqual(prepared.width, width)
        self.assertLessEqual(prepared.height, height)
        self.assertIn(prepared.mime_type, {"image/jpeg", "image/png", "image/webp"})

    def test_transcode_to_limit_returns_supported_bluesky_mime_type(self) -> None:
        image = Image.new("RGB", (512, 512), color=(10, 200, 30))
        image.format = "WEBP"

        prepared = _transcode_to_limit(image)

        self.assertLessEqual(len(prepared.data), 1_000_000)
        self.assertIn(prepared.mime_type, {"image/jpeg", "image/png", "image/webp"})

        # Ensure encoded bytes are loadable as an image payload.
        decoded = Image.open(io.BytesIO(prepared.data))
        self.assertEqual(decoded.width, prepared.width)
        self.assertEqual(decoded.height, prepared.height)


if __name__ == "__main__":
    unittest.main()
