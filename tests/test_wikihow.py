import unittest

from wikihow_bluesky_bot.openai_bluesky_uploader import build_post_alt_text
from wikihow_bluesky_bot.wikihow import extract_image_candidates_from_html


class WikiHowTests(unittest.TestCase):
    def test_build_post_alt_text_includes_alt_and_article_url(self) -> None:
        alt = build_post_alt_text(
            wikihow_image_alt="A person planting basil",
            article_url="https://www.wikihow.com/Grow-Basil",
        )
        self.assertEqual(
            alt,
            "A person planting basil\nImage from https://www.wikihow.com/Grow-Basil",
        )

    def test_build_post_alt_text_uses_fallback_when_alt_missing(self) -> None:
        alt = build_post_alt_text(
            wikihow_image_alt="   ",
            article_url="  https://www.wikihow.com/Grow-Basil  ",
        )
        self.assertEqual(
            alt,
            "Image from wikiHow\nImage from https://www.wikihow.com/Grow-Basil",
        )

    def test_extract_image_candidates_filters_invalid_urls(self) -> None:
        html = """
        <html><body>
                <div class="mw-parser-output">
                    <img src="data:image/png;base64,abc" alt="ignore" />
                    <img src="/images/example.jpg" alt="Example image" />
                    <img src="//cdn.wikihow.com/cool.webp" alt="Cool image" />
                    <img src="icon.svg" alt="icon" />
                </div>
        </body></html>
        """

        candidates = extract_image_candidates_from_html(
            html, "https://www.wikihow.com/Test"
        )
        self.assertEqual(len(candidates), 2)
        self.assertEqual(
            candidates[0].src_url, "https://www.wikihow.com/images/example.jpg"
        )
        self.assertEqual(candidates[0].alt_text, "Example image")
        self.assertEqual(candidates[1].src_url, "https://cdn.wikihow.com/cool.webp")
        self.assertEqual(candidates[1].alt_text, "Cool image")

    def test_extract_image_candidates_ignores_non_body_author_images(self) -> None:
        html = """
            <html><body>
                <div class="author-card">
                    <img src="/images/author-avatar.jpg" alt="Author avatar" class="avatar" />
                </div>
                <div class="mw-parser-output">
                    <img src="/images/article-step-1.jpg" alt="Step image" />
                </div>
            </body></html>
            """

        candidates = extract_image_candidates_from_html(
            html, "https://www.wikihow.com/Test"
        )

        self.assertEqual(len(candidates), 1)
        self.assertEqual(
            candidates[0].src_url, "https://www.wikihow.com/images/article-step-1.jpg"
        )
        self.assertEqual(candidates[0].alt_text, "Step image")

    def test_extract_image_candidates_prefers_img_src_over_data_original(self) -> None:
        html = """
        <html><body>
            <div class="mw-parser-output">
                <img
                    src="https://www.wikihow.com/images/thumb/7/7e/Email-a-Tattoo-Artist-Step-4.jpg/v4-460px-Email-a-Tattoo-Artist-Step-4.jpg"
                    data-original="/images/thumb/7/7e/Email-a-Tattoo-Artist-Step-4.jpg/aid13191759-v4-728px-Email-a-Tattoo-Artist-Step-4.jpg"
                    class="whcdn"
                />
            </div>
        </body></html>
        """

        candidates = extract_image_candidates_from_html(
            html, "https://www.wikihow.com/Email-a-Tattoo-Artist"
        )

        self.assertEqual(len(candidates), 1)
        self.assertEqual(
            candidates[0].src_url,
            "https://www.wikihow.com/images/thumb/7/7e/Email-a-Tattoo-Artist-Step-4.jpg/v4-460px-Email-a-Tattoo-Artist-Step-4.jpg",
        )
        self.assertEqual(candidates[0].alt_text, "")

    def test_extract_image_candidates_reads_plain_img_alt(self) -> None:
        html = """
        <html><body>
            <div class="mw-parser-output">
                <img
                    alt="Step 1 Find a small jar with a tight fitting lid."
                    src="https://www.wikihow.com/images/thumb/b/bf/Make-Cream-Eyeshadow-Step-1-Version-5.jpg/v4-460px-Make-Cream-Eyeshadow-Step-1-Version-5.jpg"
                />
            </div>
        </body></html>
        """

        candidates = extract_image_candidates_from_html(
            html, "https://www.wikihow.com/Make-Cream-Eyeshadow"
        )

        self.assertEqual(len(candidates), 1)
        self.assertEqual(
            candidates[0].alt_text,
            "Step 1 Find a small jar with a tight fitting lid.",
        )

    def test_extract_image_candidates_ignores_images_outside_article_body(self) -> None:
        html = """
        <html><body>
            <main>
                <img src="/images/site-icon.png" alt="Site icon" />
            </main>
            <div class="mw-parser-output">
                <img src="/images/article-body.jpg" alt="Article body image" />
            </div>
        </body></html>
        """

        candidates = extract_image_candidates_from_html(
            html, "https://www.wikihow.com/Test"
        )

        self.assertEqual(len(candidates), 1)
        self.assertEqual(
            candidates[0].src_url, "https://www.wikihow.com/images/article-body.jpg"
        )
        self.assertEqual(candidates[0].alt_text, "Article body image")

    def test_extract_image_candidates_ignores_small_utility_images(self) -> None:
        html = """
        <html><body>
            <div class="mw-parser-output">
                <img src="/images/step-icon.png" alt="step icon" width="32" height="32" />
                <img src="/images/step-photo.jpg" alt="Step photo" width="728" height="546" />
            </div>
        </body></html>
        """

        candidates = extract_image_candidates_from_html(
            html, "https://www.wikihow.com/Test"
        )

        self.assertEqual(len(candidates), 1)
        self.assertEqual(
            candidates[0].src_url, "https://www.wikihow.com/images/step-photo.jpg"
        )
        self.assertEqual(candidates[0].alt_text, "Step photo")


if __name__ == "__main__":
    unittest.main()
