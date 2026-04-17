from pathlib import Path
import tempfile
import unittest

from wikihow_bluesky_bot.persistence import StateStore
from wikihow_bluesky_bot.types import PublishedPost


class PersistenceTests(unittest.TestCase):
    def test_recent_duplicate_exists(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "state.sqlite3"
            store = StateStore(db_path)

            self.assertFalse(
                store.recent_duplicate_exists(image_hash="abc", within_hours=24)
            )

            store.record_post(
                image_url="https://img.example/x.jpg",
                article_url="https://www.wikihow.com/Test",
                image_hash="abc",
                published_post=PublishedPost(uri="at://x", cid="cidx"),
            )

            self.assertTrue(
                store.recent_duplicate_exists(image_hash="abc", within_hours=24)
            )
            self.assertFalse(
                store.recent_duplicate_exists(image_hash="different", within_hours=24)
            )


if __name__ == "__main__":
    unittest.main()
