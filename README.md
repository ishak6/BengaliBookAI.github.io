# Bengali Book AI

বাংলা বই থেকে সূত্রসহ উত্তর খোঁজার ওয়েবসাইট ও Telegram Bot।

## বর্তমান অবস্থা

- GitHub Pages-এর প্রাথমিক ওয়েবসাইট তৈরি ও deploy করা হয়েছে।
- Cloudflare Worker-এর Phase 1 API foundation যোগ করা হয়েছে।
- Telegram webhook route এবং /health endpoint যোগ করা হয়েছে।
- D1 database-এর books, pages, full-text search এবং admin audit schema যোগ করা হয়েছে।
- Cloudflare account resources ও secrets এখনো configure করা হয়নি।
- PDF ingestion, OCR, Bengali retrieval এবং AI answer generation এখনো তৈরি হয়নি।

## Quality Harness

A permanent automated test harness runs on pushes and pull requests. It checks Worker request validation, image upload limits and MIME handling, multimodal OCR/answer orchestration with mocked provider responses, book-only evidence behavior, frontend camera/upload wiring, JavaScript syntax, and PDF indexer syntax. Worker and Pages deployment workflows run the same harness before publishing. The tests use placeholder credentials and mocked AI responses; they never call the paid AI provider or modify production books.

Run locally with Node.js 22:

```bash
npm test --prefix worker
node --check worker/src/index.js
python -m py_compile scripts/index_pdf.py
```

## Architecture

- GitHub Pages — static website.
- Cloudflare Workers — API and Telegram webhook.
- Cloudflare D1 — book metadata, extracted page text and search index.
- Cloudflare R2 — permitted book files.
- Telegram Bot API — question and admin interface.

## Content and answer policy

Only public-domain, openly licensed, or explicitly permissioned books may be added. A book-grounded answer must be shown separately from general AI explanation. If stored books do not support an answer, the system must say so and must not invent a citation.

## Backend setup

See worker/README.md for Cloudflare resource creation, database migration, secrets, and deployment instructions.

Never commit Telegram bot tokens, webhook secrets, or other credentials.
