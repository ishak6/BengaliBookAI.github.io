import json
import os
import sys
import urllib.request
import urllib.error
from urllib.parse import urlparse
import fitz
from io import BytesIO
from PIL import Image
import pytesseract

API = os.environ.get("WORKER_API_URL", "https://bengali-book-ai-api.bengalibookai.workers.dev").rstrip("/")
TOKEN = os.environ["WORKER_ADMIN_API_TOKEN"]
BOOK_ID = os.environ["BOOK_ID"].strip()
PDF_URL = os.environ["PDF_URL"].strip()

def validate_url(value: str) -> None:
    u = urlparse(value)
    if (u.scheme != "https" or u.hostname != "github.com" or
        not u.path.startswith("/ishak6/BengaliBookAI.github.io/releases/download/") or
        not u.path.lower().endswith(".pdf")):
        raise SystemExit("PDF_URL must be a public PDF asset from this repository's GitHub Releases.")

def post(path: str, payload: dict) -> dict:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        API + path, data=data, method="POST",
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + TOKEN}
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Worker returned HTTP {exc.code}: {detail}") from exc

def main() -> None:
    if len(TOKEN) < 32:
        raise SystemExit("WORKER_ADMIN_API_TOKEN is missing or too short.")
    if not BOOK_ID:
        raise SystemExit("BOOK_ID is required.")
    validate_url(PDF_URL)
    print("Downloading public release PDF…")
    req = urllib.request.Request(PDF_URL, headers={"User-Agent": "BengaliBookAI-PDF-Indexer/1.0"})
    with urllib.request.urlopen(req, timeout=120) as response:
        pdf_bytes = response.read(80 * 1024 * 1024 + 1)
    if len(pdf_bytes) > 80 * 1024 * 1024:
        raise SystemExit("PDF exceeds the 80 MiB indexing workflow limit.")
    if not pdf_bytes.startswith(b"%PDF-"):
        raise SystemExit("The selected release asset is not a valid PDF.")
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    if doc.page_count < 1 or doc.page_count > 2500:
        raise SystemExit(f"Unsupported page count: {doc.page_count}; allowed range is 1–2500.")
    print(f"Extracting text from {doc.page_count} pages…")
    batch = []
    total_chars = 0
    indexed = 0
    for index, page in enumerate(doc, start=1):
        text = page.get_text("text").strip()
        text = "\n".join(line.rstrip() for line in text.splitlines())
        if not text:
            continue
        if len(text) > 18000:
            text = text[:18000]
        batch.append({"page_number": index, "chapter": None, "content": text})
        total_chars += len(text)
        if len(batch) == 25:
            result = post(f"/api/admin/books/{BOOK_ID}/pages", {"pages": batch})
            indexed += result.get("received_pages", len(batch))
            print(f"Indexed {indexed} text pages…")
            batch = []
    if batch:
        result = post(f"/api/admin/books/{BOOK_ID}/pages", {"pages": batch})
        indexed += result.get("received_pages", len(batch))
    doc.close()
    if indexed == 0:
        raise SystemExit("No selectable text found. This PDF may be scanned; OCR is not yet enabled, so it was not marked ready.")
    result = post(f"/api/admin/books/{BOOK_ID}/complete", {})
    print(json.dumps({"ok": True, "book_id": BOOK_ID, "pages_indexed": indexed, "ocr_pages": ocr_pages,
                      "characters_extracted": total_chars, "final": result}, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
