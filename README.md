# WikiHow Random Image Bluesky Bot

Python 3.14+ bot that:

1. Fetches a random wikiHow article using `whapi`.
2. Picks a random image from that article.
3. Posts image-only to Bluesky (no post text).
4. Uses alt text format: original image alt + newline + article URL.

## Quick Start

1. Install dependencies:

```bash
python3.14 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

2. Configure environment:

```bash
cp .env.example .env
# edit .env with your Bluesky app password
```

3. Dry run once:

```bash
wikihow-bsky-bot run-once --dry-run
```

Dry-run mode authenticates to Bluesky, prepares the image, writes the prepared image file to the current working directory, and prints the final alt text to the console. It does not create a post.

4. Start scheduler:

```bash
wikihow-bsky-bot run-scheduler
```

## Commands

- `wikihow-bsky-bot run-once`
- `wikihow-bsky-bot run-scheduler`

## Notes

- Bluesky image embed requires image file <= 1,000,000 bytes.
- The bot attempts image conversion/compression/downscaling to satisfy the size limit.
- SQLite history is used to avoid duplicate posts in a rolling window.

## Optional Alt Text Generation

Alt text generation is optional. If disabled, the bot uses extracted image alt text.

Set these environment variables to enable generation:

- `ALT_GEN_ENABLED=true`
- `ALT_GEN_API_KEY=<your provider API key>`

Optional tuning variables:

- `ALT_GEN_ENDPOINT` (default: `https://api.openai.com/v1/responses`)
- `ALT_GEN_MODEL` (default: `gpt-4o-mini`)
- `ALT_GEN_TIMEOUT_SECONDS` (default: `BOT_HTTP_TIMEOUT_SECONDS`)

Behavior:

- Uses OpenAI-compatible `responses.create` with `input_image` URL.
- If generation fails for any reason, the bot falls back to extracted alt text.

For GitHub Actions, configure:

- Repository secret: `ALT_GEN_API_KEY`
- Repository variables: `ALT_GEN_ENDPOINT` and `ALT_GEN_MODEL` (optional; workflow has defaults)

## Deployment

- Linux systemd unit/timer: see `deploy/systemd/`
- GitHub Actions schedule: see `.github/workflows/post-random-image.yml`
