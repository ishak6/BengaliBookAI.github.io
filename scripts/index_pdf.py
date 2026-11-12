import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from collections import deque
import urllib.request
import urllib.error
from urllib.parse import urlparse
import fitz
from io import BytesIO
from PIL import Image, ImageOps
import pytesseract
from ocr_quality import needs_ocr, choose_text
from generate_covers import upload_cover

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
        headers={"Content-Type": "application/json", "Accept": "application/json", "User-Agent": "BengaliBookAI-Indexer/1.0 (+https://github.com/ishak6/BengaliBookAI.github.io)", "Authorization": "Bearer " + TOKEN}
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
    print("Generating a persistent first-page cover thumbnail…")
    try:
        upload_cover(pdf_bytes, PDF_URL)
    except Exception as cover_error:
        print(f"Cover generation warning (PDF indexing will continue): {cover_error}")
    if doc.page_count < 1 or doc.page_count > 2500:
        raise SystemExit(f"Unsupported page count: {doc.page_count}; allowed range is 1–2500.")
    print(f"Extracting text from {doc.page_count} pages with native-text quality checks…")
    batch = []
    total_chars = 0
    indexed = 0
    ocr_pages = 0
    # Extract native text serially, but overlap OCR for image-only pages.
    # A small bounded queue keeps memory predictable on large PDFs.
    def run_ocr(png_bytes: bytes) -> str:
        image = Image.open(BytesIO(png_bytes)).convert("L")
        image = ImageOps.autocontrast(image)
        return pytesseract.image_to_string(image, lang="ben+eng", config="--oem 1 --psm 6").strip()

    pending = deque()
    def consume(item):
        nonlocal_dummy = None
        page_number, native_text, future = item
        ocr_text = future.result() if future else ""
        chosen = choose_text(native_text, ocr_text) if future else native_text
        return page_number, chosen, bool(future and ocr_text and chosen == ocr_text)

    def save_page(item):
        nonlocal_state = item
        nonlocal total_chars, indexed, ocr_pages, batch
        page_number, text, used_ocr = item
        if used_ocr:
            ocr_pages += 1
        if not text:
            return
        text = text[:18000]
        batch.append({"page_number": page_number, "chapter": None, "content": text})
        total_chars += len(text)
        if len(batch) >= 25:
            result = post(f"/api/admin/books/{BOOK_ID}/pages", {"pages": batch})
            indexed += result.get("received_pages", len(batch))
            print(f"Indexed {indexed} text pages…")
            batch = []

    with ThreadPoolExecutor(max_workers=3) as pool:
        for index, page in enumerate(doc, start=1):
            native = "\n".join(line.rstrip() for line in page.get_text("text").strip().splitlines())
            future = None
            if needs_ocr(native):
                # 2.0x gives Tesseract more glyph detail for Bengali matras and conjuncts.
                pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0), alpha=False, colorspace=fitz.csGRAY)
                future = pool.submit(run_ocr, pix.tobytes("png"))
            pending.append((index, native, future))
            if len(pending) >= 4:
                save_page(consume(pending.popleft()))
        while pending:
            save_page(consume(pending.popleft()))
    if batch:
        result = post(f"/api/admin/books/{BOOK_ID}/pages", {"pages": batch})
        indexed += result.get("received_pages", len(batch))
    doc.close()
    if indexed == 0:
        raise SystemExit("No selectable or OCR text found in this PDF; it was not marked ready.")
    print(f"OCR used on {ocr_pages} pages; extracted {total_chars} characters.")
    result = post(f"/api/admin/books/{BOOK_ID}/complete", {})
    print(json.dumps({"ok": True, "book_id": BOOK_ID, "pages_indexed": indexed, "ocr_pages": ocr_pages,
                      "characters_extracted": total_chars, "final": result}, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
