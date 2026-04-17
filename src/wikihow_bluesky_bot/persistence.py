from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import cast

from wikihow_bluesky_bot.types import PublishedPost


@dataclass(slots=True)
class StateStore:
    database_path: Path

    def __post_init__(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.database_path) as conn:
            _ = conn.execute(
                """
                CREATE TABLE IF NOT EXISTS posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    image_url TEXT NOT NULL,
                    article_url TEXT NOT NULL,
                    image_hash TEXT NOT NULL,
                    post_uri TEXT NOT NULL,
                    post_cid TEXT NOT NULL
                )
                """
            )
            _ = conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_posts_created_at ON posts(created_at)"
            )
            _ = conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_posts_image_hash ON posts(image_hash)"
            )
            conn.commit()

    def recent_duplicate_exists(self, *, image_hash: str, within_hours: int) -> bool:
        cutoff = datetime.now(tz=UTC) - timedelta(hours=within_hours)
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.execute(
                """
                SELECT 1
                FROM posts
                WHERE image_hash = ? AND created_at >= ?
                LIMIT 1
                """,
                (image_hash, cutoff.isoformat()),
            )
            row_obj = cast(object | None, cursor.fetchone())
        return row_obj is not None

    def record_post(
        self,
        *,
        image_url: str,
        article_url: str,
        image_hash: str,
        published_post: PublishedPost,
    ) -> None:
        with sqlite3.connect(self.database_path) as conn:
            _ = conn.execute(
                """
                INSERT INTO posts(created_at, image_url, article_url, image_hash, post_uri, post_cid)
                VALUES(?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.now(tz=UTC).isoformat(),
                    image_url,
                    article_url,
                    image_hash,
                    published_post.uri,
                    published_post.cid,
                ),
            )
            conn.commit()


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
