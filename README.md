# Bengali Book AI

A Bengali book question-answering website and Telegram bot.

## Project architecture

- `website/` — static frontend published with GitHub Pages.
- `worker/` — Cloudflare Worker API (deployed separately).
- Cloudflare D1 — book metadata and searchable text.
- Cloudflare R2 — permitted book files and extracted page text.

## Content policy

Only public-domain, openly licensed, or explicitly permissioned books may be added. The book-grounded answer must be separated from general AI explanation. If the stored books do not support an answer, the system must say so rather than inventing a citation.

## Status

Repository initialized. Deployment and backend configuration are not yet complete.
