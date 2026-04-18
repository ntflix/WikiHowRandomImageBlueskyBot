# WikiHow Random Image Bluesky Bot

Python 3.14+ bot that:

1. Fetches a random wikiHow article using [`whapi`](https://github.com/ntflix/WHAPI).
2. Picks a random image from that article.
3. Posts image-only to Bluesky (no post text).
4. Uses alt text format: [optional generated alt] + original image name.webp + `\n` + article URL.

## Modules

The package has two modules:

1. `wikihow_bluesky_bot.random_image_grabber`
   - Purpose: get a random image from wikiHow.
   - Main entry: `WikiHowRandomImageGrabber.fetch_random_image()`.
2. `wikihow_bluesky_bot.openai_bluesky_uploader`
   - Purpose: generate alt text with OpenAI (optional), prepare image, deduplicate, and upload to Bluesky.
   - Main entry: `OpenAIBlueskyUploader.upload_selected_image(...)`.

`WikiHowBlueskyBot` just uses these modules.

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

- Linux systemd unit/timer:

```bash
# 1) Create service user and app directory
sudo useradd --system --home-dir /opt/wikihow-random-image-bluesky-bot --shell /usr/sbin/nologin wikibot
sudo mkdir -p /opt/wikihow-random-image-bluesky-bot

# 2) Copy project code into /opt
# Avoid copying local .env, .venv, and .git into /opt.
sudo rsync -a --delete \
	--exclude '.git' \
	--exclude '.venv' \
	--exclude '.env' \
	./ /opt/wikihow-random-image-bluesky-bot/
sudo chown -R wikibot:wikibot /opt/wikihow-random-image-bluesky-bot

# 3) Create venv and install
sudo -u wikibot python3.14 -m venv /opt/wikihow-random-image-bluesky-bot/.venv
sudo -u wikibot /opt/wikihow-random-image-bluesky-bot/.venv/bin/pip install -e /opt/wikihow-random-image-bluesky-bot

# 4) Create and edit systemd environment file (do NOT put secrets in unit files)
sudo install -m 600 -o root -g root /dev/null /etc/wikihow-bsky-bot.env
sudo editor /etc/wikihow-bsky-bot.env
```

Example `/etc/wikihow-bsky-bot.env`:

```dotenv
BLUESKY_IDENTIFIER=your-handle.bsky.social
BLUESKY_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
BOT_DRY_RUN=false
BOT_DATABASE_PATH=/var/lib/wikihow-bsky-bot/bot_state.sqlite3
BOT_TIMEZONE=Europe/London
BOT_HTTP_TIMEOUT_SECONDS=20
ALT_GEN_ENABLED=false
ALT_GEN_API_KEY=
ALT_GEN_ENDPOINT=https://api.openai.com/v1/responses
ALT_GEN_MODEL=gpt-4o-mini
```

Important:

- Do not run `install ... /dev/null /etc/wikihow-bsky-bot.env` after editing. That command resets the file to empty.
- Keep `/etc/wikihow-bsky-bot.env` as the source of truth for service configuration.

Install and enable units:

```bash
sudo cp deploy/systemd/wikihow-bsky-bot.service /etc/systemd/system/
sudo cp deploy/systemd/wikihow-bsky-bot.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now wikihow-bsky-bot.timer
```

Operational checks:

```bash
# Shows next and last run times
systemctl list-timers wikihow-bsky-bot.timer

# Run once immediately for validation
sudo systemctl start wikihow-bsky-bot.service

# View recent logs
journalctl -u wikihow-bsky-bot.service -n 200 --no-pager
```

Notes:

- The timer is fixed to local time: daily at `13:00` (`OnCalendar=*-*-* 13:00:00`).
- Persistent state is managed by systemd in `/var/lib/wikihow-bsky-bot/` via `StateDirectory=wikihow-bsky-bot`.
- The service is hardened with common systemd protections for unattended network jobs.
- GitHub Actions schedule: see `.github/workflows/post-random-image.yml`

If the service fails with `Read-only file system` for `.state`:

- Your effective `BOT_DATABASE_PATH` is still relative (for example `.state/...`).
- Set `BOT_DATABASE_PATH=/var/lib/wikihow-bsky-bot/bot_state.sqlite3` in `/etc/wikihow-bsky-bot.env`.
- Run `sudo systemctl daemon-reload` and start the service again.
