# Bengali Book AI Worker

## Current Phase 2 architecture

- GitHub Pages hosts the Bengali question UI and the noindex admin panel.
- Cloudflare Worker validates admin requests, queries D1 and calls an optional OpenAI-compatible AI provider.
- D1 stores book metadata, extracted page text and the FTS5 search index.
- Public GitHub Release assets store permitted PDF files (no R2 payment card required).
- GitHub Actions downloads a selected release PDF, extracts selectable text with PyMuPDF and sends page batches to the Worker.

## Add an authorized book

Only add public-domain books, open-license books, or books for which you have explicit written distribution permission. GitHub Release assets are public.

1. Open [GitHub Releases](https://github.com/ishak6/BengaliBookAI.github.io/releases) and create a release.
2. Attach the permitted PDF and publish the release. Copy the asset URL ending in `.pdf`.
3. In Cloudflare → Workers & Pages → `bengali-book-ai-api` → Settings → Variables and Secrets, add secret `ADMIN_API_TOKEN`. Use a unique random value of at least 32 characters. Never commit or share it.
4. Add the exact same value as a GitHub repository Actions secret named `WORKER_ADMIN_API_TOKEN`.
5. Open [Admin panel](https://ishak6.github.io/BengaliBookAI.github.io/admin.html). Enter the token, book title, rights evidence and PDF asset URL. Submit.
6. The panel returns a Book ID. Open GitHub → Actions → **Index PDF into D1** → Run workflow. Enter that Book ID and the same PDF URL.
7. When the workflow succeeds, check `/api/books`. The book should appear with status ready.

The admin panel does not store the token in localStorage or cookies; it stays in the page's memory and is sent over HTTPS. Clear the field and close the tab after use.

## AI provider

The Worker defaults to OpenRouter's `openrouter/free` model. Add secret `AI_API_KEY` in Cloudflare Worker settings. The key is never stored in GitHub or sent to the browser. The AI answer is generated from retrieved book pages and separates book-grounded answer from general explanation. If the key is absent or provider call fails, the API still returns matching book excerpts and page citations without inventing an AI answer.

Optional non-secret variables:
- `AI_BASE_URL` (default `https://openrouter.ai/api/v1`)
- `AI_MODEL` (default `openrouter/free`)

## API routes

- `GET /health` — Worker, D1, admin, AI and Telegram configuration flags (never secret values).
- `GET /api/books` — list ready books.
- `GET /api/books/:id/file` — stream a public GitHub Release PDF.
- `POST /api/ask` — Bengali FTS5 retrieval and optional AI answer with page references.
- `POST /api/admin/books` — register a book (Bearer `ADMIN_API_TOKEN`).
- `POST /api/admin/books/:id/pages` — insert/update 1–25 extracted pages per batch (admin only).
- `POST /api/admin/books/:id/complete` — mark a book ready only after at least one page is indexed (admin only).
- `POST /telegram/webhook` — optional Telegram webhook.

## PDF extraction limitations

The indexing workflow currently extracts selectable PDF text. It does not yet run OCR on scanned/image-only PDFs. If a PDF has no selectable text, the workflow fails safely and does not mark the book ready. Bengali FTS5 search is a baseline lexical search; it is not semantic/vector search. Chapter headings are currently not inferred reliably and may remain blank.

## Cloudflare setup

1. Keep the D1 binding named `DB` in `wrangler.jsonc`.
2. Apply the existing D1 migration if it has not already been applied:
   `npx wrangler d1 migrations apply bengali-book-ai-db --remote`.
3. Deploy with GitHub Actions **Deploy Bengali Book AI Worker**. Required GitHub secrets: `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID`.
4. Add Worker secrets `ADMIN_API_TOKEN` and `AI_API_KEY` in Cloudflare. Optional Telegram secrets: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_WEBHOOK_SECRET`, `ADMIN_TELEGRAM_ID`.

Never paste any secret into chat, source files, commit messages or screenshots.

## Storage and rights

GitHub Release assets are public and have repository/service limits. Do not upload private, pirated, or restricted books. The project accepts only public-domain, open-license or explicitly permitted content.
