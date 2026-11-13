"""Quality heuristics for Bengali/English PDF text."""
import re
import unicodedata

_BENGALI = re.compile(r"[\u0980-\u09FF]")
_WORD = re.compile(r"[\w\u0980-\u09FF]+", re.UNICODE)
_BAD = ("\ufffd", "\u25a1", "\u25a0")


def text_metrics(text):
    value = unicodedata.normalize("NFC", str(text or "")).strip()
    visible = [c for c in value if not c.isspace()]
    words = _WORD.findall(value)
    bengali = sum(1 for c in visible if _BENGALI.fullmatch(c))
    bad = sum(1 for c in visible if c in _BAD or unicodedata.category(c) in ("Co", "Cs", "Cn"))
    return {"characters": len(visible), "words": len(words),
            "bengali_ratio": bengali / max(1, len(visible)),
            "bad_ratio": bad / max(1, len(visible))}


def text_quality(text):
    m = text_metrics(text)
    if not m["characters"]:
        return 0.0
    length_score = min(1.0, m["characters"] / 220)
    word_score = min(1.0, m["words"] / 35)
    script_score = min(1.0, m["bengali_ratio"] / 0.12) if m["bengali_ratio"] else 0.65
    penalty = min(0.9, m["bad_ratio"] * 8)
    return max(0.0, 0.42 * length_score + 0.28 * word_score + 0.30 * script_score - penalty)


def needs_ocr(text):
    m = text_metrics(text)
    return (m["characters"] < 90 or m["words"] < 12 or
            m["bad_ratio"] > 0.035 or text_quality(text) < 0.76)


def candidate_score(text, confidence=0.0):
    return text_quality(text) + max(0.0, min(100.0, float(confidence or 0))) / 1000.0


def choose_text(native_text, ocr_text, ocr_confidence=0.0):
    native = str(native_text or "").strip()
    ocr = str(ocr_text or "").strip()
    if not ocr:
        return native
    if not native:
        return ocr
    return ocr if candidate_score(ocr, ocr_confidence) > candidate_score(native) + 0.025 else native
