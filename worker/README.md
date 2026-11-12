# Bengali Book AI Worker

## Current Phase 2 architecture

- GitHub Pages hosts the Bengali question UI and the noindex admin panel.
- Cloudflare Worker validates admin requests, queries D1 and calls an optional OpenAI-compatible AI provider.
- D1 stores book metadata, extracted page text and the FTS5 search index.
- Public GitHub Release assets store permitted PDF files (no R2 payment card required).
- GitHub Actions downloads a selected release PDF, extracts text with PyMuPDF, uses Bengali+English Tesseract OCR for scanned/low-text pages, and sends page batches to the Worker.

## Add an authorized book

Only add public-domain books, open-license books, or books for which you have explicit written distribution permission. GitHub Release assets are public.

1. Open [GitHub Releases](https://github.com/ishak6/BengaliBookAI.github.io/releases) and create a release.
2. Attach the permitted PDF and publish the release. Copy the asset URL ending in `.pdf`.
3. Set GitHub repository Actions secrets `WORKER_ADMIN_API_TOKEN` (internal indexer credential, at least 32 characters), `WORKER_ADMIN_PASSWORD` (your Admin login password, at least 12 characters), and `OPENROUTER_API_KEY`. Do not share these values. The website no longer asks you to enter the internal API token.
4. Create a fine-grained GitHub token restricted to this repository with **Contents: Read and write** and **Actions: Read and write**. Save it as repository secret `BOOK_UPLOAD_TOKEN` (GitHub reserves names beginning with `GITHUB_`). Never paste any token into chat or commit it.
5. Open [Admin panel](https://ishak6.github.io/BengaliBookAI.github.io/admin.html), sign in with the Admin password, choose a permitted PDF, and confirm that you have distribution rights. Upload. The service creates a public GitHub Release asset and queues PDF indexing automatically. The panel keeps only an 8-hour session in sessionStorage; it does not expose the internal API token.
6. Open GitHub → Actions → **Sync Worker Secrets** → Run workflow. This copies `WORKER_ADMIN_API_TOKEN` to Worker secret `ADMIN_API_TOKEN`, `WORKER_ADMIN_PASSWORD` to Worker secret `ADMIN_PASSWORD`, `OPENROUTER_API_KEY` to `AI_API_KEY`, and `BOOK_UPLOAD_TOKEN` to Worker secret `GITHUB_API_TOKEN`. The workflow also needs `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID`.
7. If the upload was attempted before the token sync, retry the PDF upload after the sync completes. After indexing succeeds, the book is automatically published and appears in `/api/books`.

Admin login creates a signed, 8-hour session. The Admin password is never stored in the browser. Logout clears the session from sessionStorage.

## AI provider

The Worker defaults to OpenRouter's `openrouter/free` model. Add secret `AI_API_KEY` in Cloudflare Worker settings. The key is never stored in GitHub or sent to the browser. The AI answer is generated from retrieved book pages and separates book-grounded answer from general explanation. If the key is absent or provider call fails, the API still returns matching book excerpts and page citations without inventing an AI answer.

Optional non-secret variables:
- `AI_BASE_URL` (default `https://openrouter.ai/api/v1`)
- `AI_MODEL` (default `openrouter/free`)

## API routes

- `GET /health` — Worker, D1, admin login, GitHub upload, AI and Telegram configuration flags (never secret values).
- `POST /api/admin/login` — verify Admin password and issue an 8-hour signed session.
- `GET /api/admin/session` — validate the current Admin session.
- `GET /api/books` — list ready books.
- `GET /api/books/:id/file` — stream a public GitHub Release PDF.
- `POST /api/ask` — Bengali FTS5 retrieval and optional AI answer with page references.
- `POST /api/admin/books` — register a book (Bearer `ADMIN_API_TOKEN`).
- `POST /api/admin/books/:id/pages` — insert/update 1–25 extracted pages per batch (admin only).
- `POST /api/admin/books/:id/complete` — mark a book ready only after at least one page is indexed (admin only).
- `POST /telegram/webhook` — optional Telegram webhook.

## PDF extraction limitations

The indexing workflow extracts selectable PDF text and falls back to Bengali+English Tesseract OCR on scanned/low-text pages. OCR quality depends on scan resolution, page orientation and print quality; manually verify citations and page text. PDFs are limited to 80 MiB and 2,500 pages per run. Bengali FTS5 search is a baseline lexical search; it is not semantic/vector search. Chapter headings are currently not inferred reliably and may remain blank.

## Cloudflare setup

1. Keep the D1 binding named `DB` in `wrangler.jsonc`.
2. Apply the existing D1 migration if it has not already been applied:
   `npx wrangler d1 migrations apply bengali-book-ai-db --remote`.
3. Deploy with GitHub Actions **Deploy Bengali Book AI Worker**. Required GitHub secrets: `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID`.
4. Add Worker secrets `ADMIN_API_TOKEN`, `ADMIN_PASSWORD`, `GITHUB_API_TOKEN` and `AI_API_KEY` in Cloudflare, or use the Sync Worker Secrets workflow. Optional Telegram secrets: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_WEBHOOK_SECRET`, `ADMIN_TELEGRAM_ID`.

Never paste any secret into chat, source files, commit messages or screenshots.

## Storage and rights

GitHub Release assets are public and have repository/service limits. Do not upload private, pirated, or restricted books. The project accepts only public-domain, open-license or explicitly permitted content.
