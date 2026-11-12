import json
import os
import urllib.error
import urllib.parse
import urllib.request
from urllib.parse import urlparse
import fitz

REPO = "ishak6/BengaliBookAI.github.io"
API = os.environ.get("WORKER_API_URL", "https://bengali-book-ai-api.bengalibookai.workers.dev").rstrip("/")
ADMIN_TOKEN = os.environ.get("WORKER_ADMIN_API_TOKEN", "")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

def github_request(url, method="GET", data=None, content_type="application/vnd.github+json"):
    headers = {
        "Authorization": "Bearer " + GITHUB_TOKEN,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "BengaliBookAI-Cover-Generator/1.0",
        "Content-Type": content_type,
    }
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=90) as response:
            raw = response.read()
            return json.loads(raw.decode("utf-8")) if raw else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API HTTP {exc.code}: {detail[:300]}") from exc

def cover_jpeg(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        if doc.page_count < 1:
            raise RuntimeError("PDF has no pages")
        page = doc.load_page(0)
        rect = page.rect
        scale = min(1000 / max(rect.width, rect.height), 1.5)
        pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
        return pix.tobytes("jpg", jpg_quality=84)
    finally:
        doc.close()

def release_tag(pdf_url):
    u = urlparse(pdf_url)
    if u.scheme != "https" or u.hostname != "github.com":
        raise RuntimeError("Unexpected PDF release URL")
    parts = u.path.split("/")
    try:
        index = parts.index("download")
        return parts[index + 1]
    except (ValueError, IndexError):
        raise RuntimeError("Could not determine GitHub Release tag")

def upload_cover(pdf_bytes, pdf_url):
    if not GITHUB_TOKEN:
        raise RuntimeError("GITHUB_TOKEN is missing; cover upload needs contents:write permission")
    tag = release_tag(pdf_url)
    api = f"https://api.github.com/repos/{REPO}"
    release = github_request(api + "/releases/tags/" + urllib.parse.quote(tag, safe=""))
    asset = next((x for x in release.get("assets", []) if x.get("name") == "cover.jpg"), None)
    if asset:
        github_request(api + "/releases/assets/" + str(asset["id"]), method="DELETE")
    image = cover_jpeg(pdf_bytes)
    upload_url = release["upload_url"].split("{", 1)[0] + "?name=cover.jpg"
    req = urllib.request.Request(
        upload_url, data=image, method="POST",
        headers={
            "Authorization": "Bearer " + GITHUB_TOKEN,
            "Accept": "application/vnd.github+json",
            "Content-Type": "image/jpeg",
            "User-Agent": "BengaliBookAI-Cover-Generator/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as response:
            response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Cover asset upload failed: HTTP {exc.code}: {detail[:300]}") from exc
    print(f"Cover uploaded for release {tag} ({len(image)} bytes)")

def main():
    if len(ADMIN_TOKEN) < 32:
        raise SystemExit("WORKER_ADMIN_API_TOKEN is missing or too short")
    if not GITHUB_TOKEN:
        raise SystemExit("GITHUB_TOKEN is missing")
    req = urllib.request.Request(
        API + "/api/admin/books",
        headers={"Authorization": "Bearer " + ADMIN_TOKEN, "Accept": "application/json",
                 "User-Agent": "BengaliBookAI-Cover-Backfill/1.0"},
    )
    with urllib.request.urlopen(req, timeout=60) as response:
        data = json.loads(response.read().decode("utf-8"))
    books = data.get("books", [])
    print(f"Found {len(books)} books in Admin library")
    for book in books:
        pdf_url = book.get("storage_key") or ""
        if not pdf_url:
            print("Skipping book without PDF URL:", book.get("id", "unknown"))
            continue
        print("Generating cover:", book.get("title", book.get("id", "book")))
        download = urllib.request.Request(pdf_url, headers={"User-Agent": "BengaliBookAI-Cover-Backfill/1.0"})
        with urllib.request.urlopen(download, timeout=180) as response:
            pdf_bytes = response.read(80 * 1024 * 1024 + 1)
        if len(pdf_bytes) > 80 * 1024 * 1024 or not pdf_bytes.startswith(b"%PDF-"):
            raise RuntimeError("Invalid or oversized PDF for " + str(book.get("id")))
        upload_cover(pdf_bytes, pdf_url)

if __name__ == "__main__":
    main()
