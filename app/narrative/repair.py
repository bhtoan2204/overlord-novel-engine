"""Local repair of a reviewed part. Original chunk rows are kept with a new status."""

import uuid

from sqlalchemy.orm import Session

from app.core.text import word_count
from app.db.models import OutlineNode, ProseChunk
from app.narrative.completion import refresh_rollup
from app.narrative.longform import _maybe_gate_part, _recount

BLOCKED = ("chuôi kiếm", "dark lord", "nông dân loài người")


def _sentences(text: str) -> list[str]:
    parts = []
    current = []
    for char in text:
        current.append(char)
        if char in ".!?…":
            parts.append("".join(current).strip())
            current = []
    tail = "".join(current).strip()
    if tail:
        parts.append(tail)
    return parts


def repair_part(session: Session, project, part: OutlineNode, *, ratio: float = 0.90) -> dict:
    """Drop sentences that introduce blocked inventions. Do not delete the original row."""
    chunks = (
        session.query(ProseChunk)
        .filter(ProseChunk.part_id == part.id, ProseChunk.status == "ACCEPTED")
        .order_by(ProseChunk.ordinal)
        .all()
    )
    changed = 0
    for chunk in chunks:
        lowered = chunk.prose.lower()
        if not any(phrase in lowered for phrase in BLOCKED):
            continue
        kept = [sentence for sentence in _sentences(chunk.prose) if not any(phrase in sentence.lower() for phrase in BLOCKED)]
        revised = " ".join(kept).strip()
        chunk.status = "SUPERSEDED"
        history = list(part.revision_history or [])
        history.append({"chunk_id": chunk.id, "strategy": "excise_blocked_sentences"})
        part.revision_history = history
        if revised:
            last = (
                session.query(ProseChunk)
                .filter(ProseChunk.beat_id == chunk.beat_id)
                .order_by(ProseChunk.ordinal.desc())
                .first()
            )
            session.add(
                ProseChunk(
                    id=str(uuid.uuid4()),
                    project_id=project.id,
                    beat_id=chunk.beat_id,
                    scene_id=chunk.scene_id,
                    part_id=chunk.part_id,
                    ordinal=(last.ordinal + 1) if last else 1,
                    prose=revised,
                    word_count=word_count(revised),
                    finish_reason="repair",
                    status="ACCEPTED",
                )
            )
        changed += 1
    session.flush()
    for beat in session.query(OutlineNode).filter(OutlineNode.project_id == project.id, OutlineNode.level == "beat").all():
        if session.query(ProseChunk).filter(ProseChunk.beat_id == beat.id, ProseChunk.status == "ACCEPTED").count():
            _recount(session, beat)
    scenes = session.query(OutlineNode).filter(OutlineNode.parent_id == part.id, OutlineNode.level == "scene").all()
    for scene in scenes:
        _recount(session, scene)
    _recount(session, part)
    part.continuity = {**(part.continuity or {}), "blocking": []}
    _maybe_gate_part(session, part)
    refresh_rollup(session, project, ratio=ratio)
    if not (part.continuity or {}).get("blocking"):
        open_beats = []
        for scene in scenes:
            open_beats.extend(
                session.query(OutlineNode)
                .filter(OutlineNode.parent_id == scene.id, OutlineNode.level == "beat", OutlineNode.completion_status.notin_(["COMPLETED", "APPROVED"]))
                .all()
            )
        if open_beats and part.completion_status == "NEEDS_REVIEW":
            part.completion_status = "GENERATING"
    return {"changed": changed, "status": part.completion_status, "words": part.actual_words}
