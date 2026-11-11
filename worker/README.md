# Bengali Book AI Worker

## No-card book storage: GitHub Releases

This project uses public GitHub Release assets for PDF storage instead of Cloudflare R2. This avoids enabling a paid R2 subscription or adding a payment card. GitHub Releases is suitable for a small initial catalogue, but it is not unlimited storage; check GitHub's current limits and terms.

### Add a book file (manual starter workflow)

1. Open repository Releases: https://github.com/ishak6/BengaliBookAI.github.io/releases
2. Create a release with a tag such as `books-v1`.
3. Upload only books that are public-domain, openly licensed, or for which you have explicit distribution permission.
4. Publish the release and copy the asset browser-download URL. It should look like `https://github.com/OWNER/REPO/releases/download/TAG/filename.pdf`.
5. Add a row to the D1 `books` table. Set `storage_key` to that exact URL and use `status='ready'` only after verifying the URL works.

Example SQL (replace every example value):
```sql
INSERT INTO books
(id, title, author, language, rights_type, rights_note, storage_key, status)
VALUES
('book-001', 'বইয়ের নাম', 'লেখকের নাম', 'bn', 'open_license',
 'লাইসেন্স ও উৎসের বিবরণ', 'https://github.com/OWNER/REPO/releases/download/TAG/FILE.pdf', 'ready');
```

### API routes

- `GET /health` — service status and storage mode.
- `GET /api/books` — list ready books from D1.
- `GET /api/books/:id/file` — streams a public GitHub Release PDF through the Worker.
- `POST /telegram/webhook` — Telegram webhook.
- `POST /api/ask` — remains HTTP 501 until PDF text extraction, page indexing, Bengali retrieval, and AI response generation are implemented.

### Cloudflare setup

1. Keep the D1 binding named `DB` in `wrangler.jsonc`.
2. No R2 bucket or R2 subscription is required.
3. Apply the D1 schema if it has not already been applied: `npx wrangler d1 migrations apply bengali-book-ai-db --remote`.
4. Deploy from the `worker` directory with `npx wrangler deploy`.

### Telegram secrets

Set these as Worker secrets (never commit or send them in chat):
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_WEBHOOK_SECRET`
- `ADMIN_TELEGRAM_ID` (your numeric Telegram user ID)

## Important limitations

- GitHub Release assets are public; do not upload private or restricted books.
- GitHub Releases is a starter workaround, not a guaranteed unlimited object-storage service.
- The Worker does not yet extract PDF pages, perform OCR, build the FTS index, or generate book-grounded AI answers.
- The admin-only upload dashboard is not implemented yet; the documented release + D1 workflow is manual.
