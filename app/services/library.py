"""Import user files and index them. Re-importing the same checksum is a no-op."""

import shutil
import uuid
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.text import word_count
from app.db.models import CatalogEntry, Project, Segment, Source
from app.ingestion.discovery import discover_index
from app.ingestion.files import content_checksum, load_user_file, new_id, split_segments
from app.knowledge.extract import store_source_knowledge
from app.retrieval.embeddings import Embedder
from app.retrieval.hybrid import VectorIndex


def import_file(
    session: Session,
    settings: Settings,
    embedder: Embedder,
    index: VectorIndex,
    path: Path,
    *,
    title: str,
    source_type: str,
    canon_level: str,
    license_status: str,
    language: str = "vi",
    timeline: str = "main",
    volume_number: int | None = None,
    chapter_number: int | None = None,
    source_url: str | None = None,
    training_allowed: bool = False,
    backend=None,
    project: Project | None = None,
) -> tuple[Source, bool]:
    text_body, structured = load_user_file(path)
    digest = content_checksum(text_body)
    existing = session.query(Source).filter(Source.content_checksum == digest).one_or_none()
    if existing:
        return existing, False
    destination_dir = settings.data_dir / "incoming"
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / f"{digest}{path.suffix.lower()}"
    if Path(path).resolve() != destination.resolve():
        shutil.copy(path, destination)
    source = Source(
        id=new_id(),
        title=title,
        source_url=source_url,
        source_type=source_type,
        volume_number=volume_number,
        chapter_number=chapter_number,
        segment_order=0,
        timeline=timeline,
        canon_level=canon_level,
        copyright_or_license_status=license_status,
        language=language,
        content_checksum=digest,
        storage_path=str(destination),
        processing_state="imported",
        training_allowed=training_allowed,
        word_count=word_count(text_body),
    )
    session.add(source)
    session.flush()
    parts = split_segments(text_body)
    rows = []
    for ordinal, part in enumerate(parts):
        rows.append(
            Segment(
                id=str(uuid.uuid4()),
                source_id=source.id,
                ordinal=ordinal,
                text=part,
                canon_level=canon_level,
                timeline=timeline,
                volume_number=volume_number,
            )
        )
    session.add_all(rows)
    session.flush()
    for row in rows:
        session.execute(text("INSERT INTO segment_fts(text, segment_id) VALUES (:text, :id)"), {"text": row.text, "id": row.id})
    vectors = embedder.embed([row.text for row in rows])
    index.add([row.id for row in rows], vectors)
    if structured or backend is not None:
        store_source_knowledge(
            session,
            source.id,
            canon_level,
            timeline,
            structured,
            text_body,
            backend,
            settings,
        )
        source.processing_state = "extracted"
        if project is not None and project.workflow_state in {"NOT_STARTED", "SOURCES_PREPARED"}:
            project.workflow_state = "KNOWLEDGE_EXTRACTED"
    elif project is not None and project.workflow_state == "NOT_STARTED":
        project.workflow_state = "SOURCES_PREPARED"
    return source, True


def discover_and_store(session: Session, url: str, settings: Settings) -> tuple[str, int]:
    status, links = discover_index(url, settings.discovery_user_agent, settings.discovery_rate_limit_seconds)
    for link in links:
        session.add(
            CatalogEntry(
                id=str(uuid.uuid4()),
                title=link.title[:400],
                url=link.url[:1000],
                classification="SECONDARY_REFERENCE",
                robots_status=status,
                notes=link.heading[:500],
            )
        )
    if status != "allowed":
        session.add(
            CatalogEntry(
                id=str(uuid.uuid4()),
                title="Discovery refused",
                url=url,
                robots_status=status,
                notes="robots.txt disallows this URL. No page was fetched.",
            )
        )
    return status, len(links)
