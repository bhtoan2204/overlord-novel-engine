"""User-supplied document import. Full text is never fetched from the web."""

import json
import uuid
from pathlib import Path

import pymupdf
from bs4 import BeautifulSoup
from ebooklib import ITEM_DOCUMENT, epub

from app.core.errors import EngineError
from app.core.text import checksum, normalize, word_count


def read_text(path: Path) -> str:
    return normalize(path.read_text(encoding="utf-8"))


def read_markdown(path: Path) -> str:
    return read_text(path)


def read_pdf(path: Path) -> str:
    document = pymupdf.open(path)
    try:
        pages = [page.get_text("text") for page in document]
    finally:
        document.close()
    return normalize("\n\n".join(pages))


def read_epub(path: Path) -> str:
    book = epub.read_epub(str(path))
    chunks: list[str] = []
    for item in book.get_items_of_type(ITEM_DOCUMENT):
        soup = BeautifulSoup(item.get_content(), "lxml")
        text = soup.get_text("\n")
        if text.strip():
            chunks.append(text)
    return normalize("\n\n".join(chunks))


def read_json(path: Path) -> tuple[str, dict | None]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict) and any(key in payload for key in ("characters", "events", "plotlines", "notes")):
        prose = payload.get("notes") or payload.get("summary") or json.dumps(payload, ensure_ascii=False, indent=2)
        return normalize(str(prose)), payload
    return normalize(json.dumps(payload, ensure_ascii=False)), None


READERS = {
    ".txt": lambda path: (read_text(path), None),
    ".md": lambda path: (read_markdown(path), None),
    ".markdown": lambda path: (read_markdown(path), None),
    ".pdf": lambda path: (read_pdf(path), None),
    ".epub": lambda path: (read_epub(path), None),
    ".json": read_json,
}


def load_user_file(path: Path) -> tuple[str, dict | None]:
    reader = READERS.get(path.suffix.lower())
    if reader is None:
        raise EngineError(f"Unsupported file type: {path.suffix}. Use TXT, Markdown, EPUB, JSON, or PDF.")
    text, structured = reader(path)
    if not text:
        raise EngineError("The file did not contain any text.")
    return text, structured


def split_segments(text: str, size: int = 1200, overlap: int = 120) -> list[str]:
    paragraphs = [part.strip() for part in normalize(text).split("\n\n") if part.strip()]
    segments: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if word_count(paragraph) > size:
            words = paragraph.split()
            step = max(1, size - overlap)
            for index in range(0, len(words), step):
                segments.append(" ".join(words[index : index + size]))
            current = ""
            continue
        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if word_count(candidate) > size and current:
            segments.append(current)
            tail = " ".join(current.split()[-overlap:])
            current = f"{tail}\n\n{paragraph}".strip()
        else:
            current = candidate
    if current:
        segments.append(current)
    return segments or [normalize(text)]


def new_id() -> str:
    return str(uuid.uuid4())


def content_checksum(text: str) -> str:
    return checksum(text)
