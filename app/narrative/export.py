"""Markdown, EPUB, and PDF export. Every file carries the unofficial-work notice."""

import html
from pathlib import Path

from ebooklib import epub
from fpdf import FPDF
from sqlalchemy.orm import Session

from app.core.disclaimer import DISCLAIMER
from app.core.errors import EngineError
from app.db.models import OutlineNode, Project, SceneDraft


def _ordered_scenes(session: Session, project_id: str) -> list[tuple[OutlineNode, OutlineNode, SceneDraft]]:
    nodes = {row.id: row for row in session.query(OutlineNode).filter(OutlineNode.project_id == project_id).all()}
    chapters = [row for row in nodes.values() if row.level == "chapter"]
    chapters.sort(key=lambda row: ((nodes[row.parent_id].ordinal if row.parent_id in nodes else 0), row.ordinal))
    collected = []
    for chapter in chapters:
        parts = [row for row in nodes.values() if row.parent_id == chapter.id and row.level == "part"]
        parts.sort(key=lambda row: row.ordinal)
        scenes = []
        if parts:
            for part in parts:
                scenes.extend(row for row in nodes.values() if row.parent_id == part.id and row.level == "scene" and row.status == "approved")
            scenes.sort(key=lambda row: ((nodes[row.parent_id].ordinal if row.parent_id in nodes else 0), row.ordinal))
        else:
            scenes = [row for row in nodes.values() if row.parent_id == chapter.id and row.level == "scene" and row.status == "approved"]
            scenes.sort(key=lambda row: row.ordinal)
        for scene in scenes:
            draft = (
                session.query(SceneDraft)
                .filter(SceneDraft.node_id == scene.id, SceneDraft.selected.is_(True))
                .order_by(SceneDraft.iteration.desc())
                .first()
            )
            if draft:
                collected.append((chapter, scene, draft))
    return collected


def part_text(session: Session, part_id: str) -> str:
    nodes = {row.id: row for row in session.query(OutlineNode).filter(OutlineNode.project_id == session.get(OutlineNode, part_id).project_id).all()}
    from app.db.models import ProseChunk

    chunks = (
        session.query(ProseChunk)
        .filter(ProseChunk.part_id == part_id, ProseChunk.status == "ACCEPTED")
        .all()
    )

    def order(chunk):
        beat = nodes.get(chunk.beat_id)
        scene = nodes.get(chunk.scene_id)
        return (scene.ordinal if scene else 0, beat.ordinal if beat else 0, chunk.ordinal)

    return "\n\n".join(chunk.prose.strip() for chunk in sorted(chunks, key=order) if chunk.prose.strip())


def render_markdown(session: Session, project: Project) -> str:
    volume = session.query(OutlineNode).filter(OutlineNode.project_id == project.id, OutlineNode.level == "volume").one_or_none()
    finished = bool(volume and volume.completion_status == "COMPLETED")
    lines = [
        f"# {project.title}",
        "",
        f"> {DISCLAIMER}",
        "",
    ]
    if not finished:
        lines.extend(["**Chưa hoàn thành. Đây không phải toàn bộ tập.**", ""])
        if volume and (volume.continuity or {}).get("canon_coverage_status") == "partial":
            lines.extend(["Nguồn chính sử đầy đủ chưa được nhập. Bản này là fanfiction dựa trên ghi chú đã có.", ""])
    from app.db.models import ProseChunk

    has_chunks = session.query(ProseChunk).filter(ProseChunk.project_id == project.id, ProseChunk.status == "ACCEPTED").count() > 0
    current = None
    ordered = [] if has_chunks else _ordered_scenes(session, project.id)
    for chapter, scene, draft in ordered:
        if chapter.id != current:
            lines.extend([f"## {chapter.title}", "", chapter.summary, ""])
            current = chapter.id
        lines.extend([f"### {scene.title}", "", draft.prose.strip(), ""])
    parts = [row for row in session.query(OutlineNode).filter(OutlineNode.project_id == project.id, OutlineNode.level == "part").all()]
    chapters = {row.id: row for row in session.query(OutlineNode).filter(OutlineNode.project_id == project.id, OutlineNode.level == "chapter").all()}
    parts.sort(key=lambda row: ((chapters[row.parent_id].ordinal if row.parent_id in chapters else 0), row.ordinal))
    wrote_part = False
    for part in parts:
        body = part_text(session, part.id).strip()
        if not body:
            continue
        wrote_part = True
        chapter = chapters.get(part.parent_id)
        lines.extend(
            [
                f"## {(chapter.title + ' — ') if chapter else ''}{part.title}",
                "",
                f"_{part.actual_words}/{part.target_words} từ. Trạng thái: {part.completion_status}._",
                "",
                body,
                "",
            ]
        )
    if current is None and not wrote_part:
        lines.append("_Chưa có cảnh nào được duyệt._")
    return "\n".join(lines)


def write_markdown(session: Session, project: Project, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_markdown(session, project), encoding="utf-8")
    return path


def _pages(session: Session, project: Project) -> list[tuple[str, str]]:
    from app.db.models import ProseChunk

    if session.query(ProseChunk).filter(ProseChunk.project_id == project.id, ProseChunk.status == "ACCEPTED").count():
        parts = session.query(OutlineNode).filter(OutlineNode.project_id == project.id, OutlineNode.level == "part").all()
        chapters = {row.id: row for row in session.query(OutlineNode).filter(OutlineNode.project_id == project.id, OutlineNode.level == "chapter").all()}
        parts.sort(key=lambda row: ((chapters[row.parent_id].ordinal if row.parent_id in chapters else 0), row.ordinal))
        pages = []
        for part in parts:
            body = part_text(session, part.id).strip()
            if body:
                pages.append((part.title, body))
        return pages
    return [(scene.title, draft.prose) for _chapter, scene, draft in _ordered_scenes(session, project.id)]


def write_epub(session: Session, project: Project, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    book = epub.EpubBook()
    book.set_identifier(project.id)
    book.set_title(project.title)
    book.set_language(project.language or "vi")
    book.add_author("Unofficial fan continuation")
    intro = epub.EpubHtml(title="Lưu ý", file_name="notice.xhtml", lang="vi")
    intro.content = f"<h1>{html.escape(project.title)}</h1><p>{html.escape(DISCLAIMER)}</p>"
    book.add_item(intro)
    items = [intro]
    for index, (title, body) in enumerate(_pages(session, project), start=1):
        page = epub.EpubHtml(title=title, file_name=f"part-{index}.xhtml", lang="vi")
        paragraphs = "".join(f"<p>{html.escape(part)}</p>" for part in body.split("\n\n"))
        page.content = f"<h1>{html.escape(title)}</h1>{paragraphs}"
        book.add_item(page)
        items.append(page)
    book.toc = items
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ["nav", *items]
    epub.write_epub(str(path), book)
    return path


def write_pdf(session: Session, project: Project, path: Path, font_path: Path) -> Path:
    if not font_path.exists():
        raise EngineError(f"PDF export needs a Unicode font at {font_path}.")
    path.parent.mkdir(parents=True, exist_ok=True)
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.set_left_margin(18)
    pdf.set_right_margin(18)
    pdf.add_font("DejaVu", "", str(font_path))
    pdf.add_page()
    pdf.set_font("DejaVu", size=16)
    pdf.multi_cell(pdf.epw, 10, project.title)
    pdf.set_font("DejaVu", size=11)
    pdf.multi_cell(pdf.epw, 7, DISCLAIMER)
    pdf.ln(4)
    for title, body in _pages(session, project):
        pdf.set_font("DejaVu", size=14)
        pdf.multi_cell(pdf.epw, 8, title)
        pdf.set_font("DejaVu", size=11)
        for paragraph in body.split("\n"):
            pdf.multi_cell(pdf.epw, 6, paragraph if paragraph.strip() else " ")
        pdf.ln(3)
    pdf.output(str(path))
    return path
