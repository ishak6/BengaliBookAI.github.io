# Bengali Book AI Worker — Phase 1

This Cloudflare Worker is the initial API and Telegram webhook foundation.

## Routes

- `GET /health` — health and configuration status.
- `POST /telegram/webhook` — Telegram webhook protected by Telegram's secret-token header.
- `POST /api/ask` — intentionally returns HTTP 501 until book ingestion and retrieval are implemented.

## Create Cloudflare resources

1. Create a D1 database named `bengali-book-ai-db`.
2. Create an R2 bucket named `bengali-book-ai-books`.
3. Replace `database_id` in `wrangler.jsonc` with the D1 database ID from Cloudflare.

Apply the database schema:

```bash
npx wrangler d1 migrations apply bengali-book-ai-db --remote
```

Deploy:

```bash
npx wrangler deploy
```

## Worker secrets

Set secrets using Wrangler; never commit them into Git:

```bash
npx wrangler secret put TELEGRAM_BOT_TOKEN
npx wrangler secret put TELEGRAM_WEBHOOK_SECRET
npx wrangler secret put ADMIN_TELEGRAM_ID
```

Use your numeric Telegram user ID for `ADMIN_TELEGRAM_ID`. The webhook secret must be a long random string using only letters, digits, underscore, and hyphen.

## Telegram webhook

After deployment, set the webhook to:

- URL: `https://YOUR-WORKER-SUBDOMAIN.workers.dev/telegram/webhook`
- `secret_token`: the exact value stored as `TELEGRAM_WEBHOOK_SECRET`

Do not post bot tokens or webhook secrets in chat, screenshots, or repository files.

## Current limitations

This is a Phase 1 foundation, not a complete book-answering system. PDF ingestion, OCR, page extraction, Bengali retrieval, AI explanations, and admin book-upload commands are not implemented yet. The API deliberately does not invent book-grounded answers before retrieval exists.
