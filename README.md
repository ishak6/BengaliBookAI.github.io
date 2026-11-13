# Bengali Book AI

বাংলা বই থেকে সূত্রসহ উত্তর খোঁজার ওয়েবসাইট ও Telegram Bot।

## বর্তমান অবস্থা

- GitHub Pages website এবং Cloudflare Worker API repository-তে রয়েছে।
- D1 database-এ বইয়ের metadata, extracted page text এবং FTS5 search রাখা হয়।
- PDF indexing workflow-এ Bengali + English Tesseract OCR, native-text quality checks এবং retry-enabled Worker batch upload আছে।
- Production indexing সফল হয়েছে কি না তা GitHub Actions run এবং Worker/D1 status দেখে নিশ্চিত করতে হবে।

## PDF indexing / OCR

- Workflow: GitHub Actions → **Index PDF into D1**.
- Admin upload থেকে workflow auto-dispatch হওয়ার কথা; প্রয়োজনে Actions থেকে book ID ও public Release PDF URL দিয়ে manual run করা যায়।
- OCR engine: Tesseract Bengali (ben) + English (eng).
- Native PDF text quality কম হলে OCR fallback চলে।
- OCR-এ PSM 6 ও PSM 11 candidate তুলনা করে quality score অনুযায়ী text বেছে নেওয়া হয়।
- Worker-এ সর্বোচ্চ 25 page প্রতি batch পাঠানো হয়; transient HTTP errors retry হয় এবং accepted page count যাচাই করা হয়।
- সীমা: 80 MiB এবং 2,500 PDF pages.
- OCR output মানুষের চোখে যাচাই করা দরকার। Automated tests OCR নির্ভুলতার নিশ্চয়তা নয়।

## Quality Harness

The repository includes automated Worker and PDF OCR tests. The tests use mocked provider responses and do not prove real-world OCR accuracy.

Run locally with Node.js 22 and Python:

    npm test --prefix worker
    node --check worker/src/index.js
    python -m py_compile scripts/index_pdf.py scripts/ocr_quality.py
    python -m unittest discover -s scripts -p 'test_ocr_quality.py' -v

## Architecture

- GitHub Pages — static website.
- Cloudflare Workers — API and Telegram webhook.
- Cloudflare D1 — book metadata, extracted page text and search index.
- GitHub Releases — public PDF assets and generated cover images.
- Telegram Bot API — optional question and admin interface.

## Content and answer policy

Only public-domain, openly licensed, or explicitly permissioned books may be added. A book-grounded answer must be shown separately from general AI explanation. If stored books do not support an answer, the system must say so and must not invent a citation.

## Backend setup

See worker/README.md for Cloudflare resource creation, database migration, secrets, and deployment instructions.

Never commit Telegram bot tokens, webhook secrets, or other credentials.
