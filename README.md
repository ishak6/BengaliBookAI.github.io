# Bengali Book AI

বাংলা বই থেকে সূত্রসহ উত্তর খোঁজার ওয়েবসাইট ও Telegram Bot।

## বর্তমান অবস্থা

- GitHub Pages-এর প্রাথমিক ওয়েবসাইট তৈরি ও deploy করা হয়েছে।
- Cloudflare Worker-এর Phase 1 API foundation যোগ করা হয়েছে।
- Telegram webhook route এবং /health endpoint যোগ করা হয়েছে।
- D1 database-এর books, pages, full-text search এবং admin audit schema যোগ করা হয়েছে।
- Cloudflare account resources ও secrets এখনো configure করা হয়নি।
- PDF ingestion, OCR, Bengali retrieval এবং AI answer generation এখনো তৈরি হয়নি।

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
