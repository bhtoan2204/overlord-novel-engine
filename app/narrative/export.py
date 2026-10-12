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
    chapters = session.query(OutlineNode).filter(OutlineNode.project_id == project_id, OutlineNode.level == "chapter").all()
    arcs = {row.id: row for row in session.query(OutlineNode).filter(OutlineNode.project_id == project_id, OutlineNode.level == "arc")}
    chapters.sort(key=lambda row: (arcs[row.parent_id].ordinal if row.parent_id in arcs else 0, row.ordinal))
    collected = []
    for chapter in chapters:
        scenes = (
            session.query(OutlineNode)
            .filter(OutlineNode.parent_id == chapter.id, OutlineNode.level == "scene", OutlineNode.status == "approved")
            .order_by(OutlineNode.ordinal)
            .all()
        )
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


def render_markdown(session: Session, project: Project) -> str:
    lines = [
        f"# {project.title}",
        "",
        f"> {DISCLAIMER}",
        "",
    ]
    current = None
    for chapter, scene, draft in _ordered_scenes(session, project.id):
        if chapter.id != current:
            lines.extend([f"## {chapter.title}", "", chapter.summary, ""])
            current = chapter.id
        lines.extend([f"### {scene.title}", "", draft.prose.strip(), ""])
    if current is None:
        lines.append("_Chưa có cảnh nào được duyệt._")
    return "\n".join(lines)


def write_markdown(session: Session, project: Project, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_markdown(session, project), encoding="utf-8")
    return path


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
    for index, (chapter, scene, draft) in enumerate(_ordered_scenes(session, project.id), start=1):
        page = epub.EpubHtml(title=scene.title, file_name=f"scene-{index}.xhtml", lang="vi")
        paragraphs = "".join(f"<p>{html.escape(part)}</p>" for part in draft.prose.split("\n\n"))
        page.content = f"<h1>{html.escape(chapter.title)}</h1><h2>{html.escape(scene.title)}</h2>{paragraphs}"
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
    for chapter, scene, draft in _ordered_scenes(session, project.id):
        pdf.set_font("DejaVu", size=14)
        pdf.multi_cell(pdf.epw, 8, chapter.title)
        pdf.set_font("DejaVu", size=12)
        pdf.multi_cell(pdf.epw, 7, scene.title)
        pdf.set_font("DejaVu", size=11)
        for paragraph in draft.prose.split("\n"):
            pdf.multi_cell(pdf.epw, 6, paragraph if paragraph.strip() else " ")
        pdf.ln(3)
    pdf.output(str(path))
    return path
