"""Heuristics for deciding when PDF pages need OCR and selecting better text."""
import unicodedata


def text_quality(value: str) -> float:
    text = str(value or "")
    if not text.strip():
        return 0.0
    visible = [ch for ch in text if not ch.isspace()]
    if not visible:
        return 0.0
    good = sum(ch != "\ufffd" and unicodedata.category(ch)[0] in ("L", "M", "N", "P", "S") for ch in visible)
    bengali = sum("\u0980" <= ch <= "\u09ff" for ch in visible)
    bad = sum(ch == "\ufffd" or unicodedata.category(ch) in ("Co", "Cs", "Cn") for ch in visible)
    base = good / len(visible)
    script_bonus = min(0.12, (bengali / len(visible)) * 0.18)
    penalty = min(0.55, (bad / len(visible)) * 2.5)
    return max(0.0, min(1.0, base + script_bonus - penalty))


def needs_ocr(native_text: str) -> bool:
    text = str(native_text or "").strip()
    if len(text) < 80:
        return True
    visible = [ch for ch in text if not ch.isspace()]
    bad = sum(ch == "\ufffd" or unicodedata.category(ch) in ("Co", "Cs", "Cn") for ch in visible)
    bad_ratio = bad / max(1, len(visible))
    return text_quality(text) < 0.72 or bad_ratio > 0.04


def choose_text(native_text: str, ocr_text: str) -> str:
    native = str(native_text or "").strip()
    ocr = str(ocr_text or "").strip()
    if not native:
        return ocr
    if not ocr:
        return native
    native_score = text_quality(native)
    ocr_score = text_quality(ocr)
    if ocr_score >= native_score + 0.035:
        return ocr
    if ocr_score > native_score and len(ocr) >= len(native) * 0.82:
        return ocr
    return native
