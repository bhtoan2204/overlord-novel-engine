"""Text helpers shared by ingestion, retrieval, and export."""

import hashlib
import re
import unicodedata

from app.core.logging import strip_think

TOKEN_RE = re.compile(r"\w+", re.UNICODE)


def normalize(text: str) -> str:
    return unicodedata.normalize("NFC", text or "").replace("\r\n", "\n").replace("\r", "\n").strip()


def checksum(text: str) -> str:
    return hashlib.sha256(normalize(text).encode("utf-8")).hexdigest()


def word_count(text: str) -> int:
    return len([part for part in normalize(text).split() if part])


def tokens(text: str) -> list[str]:
    return [match.group(0).lower() for match in TOKEN_RE.finditer(normalize(text))]


def estimate_tokens(text: str) -> int:
    """Rough budget counter. Vietnamese syllables are short, so words are scaled up."""
    return max(1, int(word_count(text) * 1.6))


def extract_json_blob(text: str) -> str:
    cleaned = strip_think(text)
    fenced = re.search(r"```(?:json)?\s*(.+?)```", cleaned, re.DOTALL | re.IGNORECASE)
    if fenced:
        return fenced.group(1).strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start >= 0 and end > start:
        return cleaned[start : end + 1]
    start = cleaned.find("[")
    end = cleaned.rfind("]")
    if start >= 0 and end > start:
        return cleaned[start : end + 1]
    return cleaned
