from pathlib import Path

import pymupdf
from ebooklib import epub

from app.ingestion.files import load_user_file, split_segments
from app.services.library import import_file


def test_split_and_text_import(tmp_path: Path, app, session):
    path = tmp_path / "note.md"
    path.write_text("Nhân vật: Người thử.\n\n" + ("Một câu đủ dài. " * 40), encoding="utf-8")
    text, structured = load_user_file(path)
    assert "Người thử" in text
    assert structured is None
    assert len(split_segments(text, size=30)) >= 2
    source, created = import_file(
        session,
        app.state.settings,
        app.state.embedder,
        app.state.index,
        path,
        title="Ghi chú",
        source_type="user_notes",
        canon_level="USER_INTERPRETATION",
        license_status="original-notes",
    )
    session.commit()
    again, created_again = import_file(
        session,
        app.state.settings,
        app.state.embedder,
        app.state.index,
        path,
        title="Ghi chú",
        source_type="user_notes",
        canon_level="USER_INTERPRETATION",
        license_status="original-notes",
    )
    assert created is True
    assert created_again is False
    assert again.id == source.id


def test_pdf_and_epub(tmp_path: Path):
    pdf_path = tmp_path / "note.pdf"
    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((72, 72), "Ghi chú thử nghiệm về Nazarick.")
    document.save(pdf_path)
    document.close()
    text, _ = load_user_file(pdf_path)
    assert "Nazarick" in text

    book = epub.EpubBook()
    book.set_identifier("test")
    book.set_title("Test")
    book.set_language("vi")
    chapter = epub.EpubHtml(title="Một", file_name="chap.xhtml", lang="vi")
    chapter.content = "<p>Antilene còn ở Ngục Băng.</p>"
    book.add_item(chapter)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ["nav", chapter]
    epub_path = tmp_path / "note.epub"
    epub.write_epub(str(epub_path), book)
    epub_text, _ = load_user_file(epub_path)
    assert "Ngục Băng" in epub_text
