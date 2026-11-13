import json
import os
import random
import time
import urllib.error
import urllib.request
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from urllib.parse import urlparse

import fitz
import pytesseract
from PIL import Image, ImageOps

from ocr_quality import candidate_score, choose_text, needs_ocr
from generate_covers import upload_cover

API = os.environ.get("WORKER_API_URL", "https://bengali-book-ai-api.bengalibookai.workers.dev").rstrip("/")
TOKEN = os.environ.get("WORKER_ADMIN_API_TOKEN", "")
BOOK_ID = os.environ.get("BOOK_ID", "").strip()
PDF_URL = os.environ.get("PDF_URL", "").strip()
MAX_PDF_BYTES = 80 * 1024 * 1024
MAX_PAGES = 2500
BATCH_SIZE = 25
RETRYABLE = {408, 425, 429, 500, 502, 503, 504}


def validate_url(value):
    u = urlparse(value)
    if (u.scheme != "https" or u.hostname != "github.com" or
            not u.path.startswith("/ishak6/BengaliBookAI.github.io/releases/download/") or
            not u.path.lower().endswith(".pdf")):
        raise SystemExit("PDF_URL must be a public PDF asset from this repository's GitHub Releases.")


def post(path, payload, attempts=5):
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        API + path, data=data, method="POST",
        headers={"Content-Type": "application/json", "Accept": "application/json",
                 "User-Agent": "BengaliBookAI-Indexer/2.0",
                 "Authorization": "Bearer " + TOKEN},
    )
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(req, timeout=90) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
            if exc.code not in RETRYABLE or attempt == attempts - 1:
                raise RuntimeError(f"Worker returned HTTP {exc.code}: {detail}") from exc
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            if attempt == attempts - 1:
                raise RuntimeError(f"Worker request failed after {attempts} attempts: {exc}") from exc
        delay = min(20, 2 ** attempt) + random.random()
        print(f"Temporary API failure; retrying in {delay:.1f}s…")
        time.sleep(delay)
    raise RuntimeError("Worker request failed unexpectedly")


def download_pdf(url):
    req = urllib.request.Request(url, headers={"User-Agent": "BengaliBookAI-PDF-Indexer/2.0"})
    with urllib.request.urlopen(req, timeout=180) as response:
        chunks, size = [], 0
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > MAX_PDF_BYTES:
                raise SystemExit("PDF exceeds the 80 MiB indexing workflow limit.")
            chunks.append(chunk)
    data = b"".join(chunks)
    if not data.startswith(b"%PDF-"):
        raise SystemExit("The selected release asset is not a valid PDF.")
    return data


def render_page(page):
    rect = page.rect
    if rect.width <= 0 or rect.height <= 0:
        raise RuntimeError("PDF page has invalid dimensions")
    scale = min(300 / 72, 2.5, (18_000_000 / (rect.width * rect.height)) ** 0.5)
    scale = max(1.0, scale)
    pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False, colorspace=fitz.csGRAY)
    return pix.tobytes("png")


def run_ocr(image_bytes):
    image = Image.open(BytesIO(image_bytes)).convert("L")
    image = ImageOps.autocontrast(image, cutoff=1)
    candidates = []
    for psm in (6, 11):
        data = pytesseract.image_to_data(
            image, lang="ben+eng", config=f"--oem 1 --psm {psm}",
            output_type=pytesseract.Output.DICT, timeout=90,
        )
        words = [w.strip() for w in data.get("text", []) if w and w.strip()]
        confidences = []
        for raw in data.get("conf", []):
            try:
                value = float(raw)
                if value >= 0:
                    confidences.append(value)
            except (TypeError, ValueError):
                pass
        text = " ".join(words).strip()
        confidence = sum(confidences) / len(confidences) if confidences else 0.0
        candidates.append((text, confidence))
    return max(candidates, key=lambda item: candidate_score(*item))


def main():
    if len(TOKEN) < 32:
        raise SystemExit("WORKER_ADMIN_API_TOKEN is missing or too short.")
    if not BOOK_ID or len(BOOK_ID) > 100:
        raise SystemExit("A valid BOOK_ID is required.")
    validate_url(PDF_URL)
    languages = set(pytesseract.get_languages(config=""))
    missing = {"ben", "eng"} - languages
    if missing:
        raise SystemExit("Tesseract language data missing: " + ", ".join(sorted(missing)))

    print("Downloading PDF…")
    pdf_bytes = download_pdf(PDF_URL)
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        if doc.page_count < 1 or doc.page_count > MAX_PAGES:
            raise SystemExit(f"Unsupported page count: {doc.page_count}; allowed range is 1–{MAX_PAGES}.")
        print(f"PDF validated: {doc.page_count} pages.")
        try:
            upload_cover(pdf_bytes, PDF_URL)
        except Exception as exc:
            print(f"Cover generation warning (indexing continues): {exc}")

        batch, indexed = [], 0
        ocr_selected = native_selected = empty_pages = total_chars = 0

        def send_batch():
            nonlocal batch, indexed
            if not batch:
                return
            result = post(f"/api/admin/books/{BOOK_ID}/pages", {"pages": batch})
            received = int(result.get("received_pages", len(batch)))
            if received != len(batch):
                raise RuntimeError(f"Worker accepted {received} of {len(batch)} pages; stopping to avoid incomplete indexing.")
            indexed += received
            print(f"Indexed {indexed} pages…")
            batch = []

        def consume(item):
            number, native, future = item
            if future is None:
                return number, native, False
            ocr_text, confidence = future.result()
            chosen = choose_text(native, ocr_text, confidence)
            return number, chosen, bool(ocr_text and chosen == ocr_text)

        def save(item):
            nonlocal ocr_selected, native_selected, empty_pages, total_chars
            number, text, used_ocr = item
            text = " ".join(str(text or "").split()).strip()
            if used_ocr:
                ocr_selected += 1
            elif text:
                native_selected += 1
            if not text:
                empty_pages += 1
                return
            text = text[:18000]
            batch.append({"page_number": number, "chapter": None, "content": text})
            total_chars += len(text)
            if len(batch) >= BATCH_SIZE:
                send_batch()

        pending = deque()
        # PyMuPDF page access/rendering stays on the main thread; workers receive image bytes only.
        with ThreadPoolExecutor(max_workers=2) as pool:
            for number in range(1, doc.page_count + 1):
                page = doc.load_page(number - 1)
                native = page.get_text("text", sort=True).strip()
                future = pool.submit(run_ocr, render_page(page)) if needs_ocr(native) else None
                pending.append((number, native, future))
                if len(pending) >= 3:
                    save(consume(pending.popleft()))
            while pending:
                save(consume(pending.popleft()))

        send_batch()
        if indexed == 0:
            raise SystemExit("No selectable or OCR text found; the book was not marked ready.")
        result = post(f"/api/admin/books/{BOOK_ID}/complete", {})
        print(json.dumps({
            "ok": True, "book_id": BOOK_ID, "pdf_pages": doc.page_count,
            "indexed_pages": indexed, "ocr_selected_pages": ocr_selected,
            "native_selected_pages": native_selected, "empty_pages": empty_pages,
            "characters_extracted": total_chars, "final": result,
        }, ensure_ascii=False, indent=2))
    finally:
        doc.close()


if __name__ == "__main__":
    main()
