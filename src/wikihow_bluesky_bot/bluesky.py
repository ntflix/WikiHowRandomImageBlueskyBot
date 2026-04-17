# pyright: reportMissingTypeStubs=false

from __future__ import annotations

from dataclasses import dataclass

from atproto import Client, models

from wikihow_bluesky_bot.types import PreparedImage, PublishedPost


@dataclass(slots=True)
class BlueskyPublisher:
    identifier: str
    app_password: str
    dry_run: bool

    _client: Client | None = None

    def _get_client(self) -> Client:
        if self._client is None:
            client = Client()
            _ = client.login(self.identifier, self.app_password)
            self._client = client
        return self._client

    def publish_image_only(
        self, *, image: PreparedImage, alt_text: str
    ) -> PublishedPost:
        client = self._get_client()

        if self.dry_run:
            return PublishedPost(uri="dry-run://post", cid="dry-run")

        uploaded = client.upload_blob(image.data)
        embed_image = models.AppBskyEmbedImages.Image(
            alt=alt_text,
            image=uploaded.blob,
            aspect_ratio=models.AppBskyEmbedDefs.AspectRatio(
                width=image.width,
                height=image.height,
            ),
        )

        record = models.AppBskyFeedPost.Record(
            text="",
            created_at=client.get_current_time_iso(),
            embed=models.AppBskyEmbedImages.Main(images=[embed_image]),
        )
        if client.me is None:
            raise RuntimeError("Bluesky login succeeded but profile is unavailable")
        response = client.app.bsky.feed.post.create(client.me.did, record=record)
        return PublishedPost(uri=str(response.uri), cid=str(response.cid))
