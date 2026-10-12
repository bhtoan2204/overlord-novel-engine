"""One committed chunk at a time. A part stays incomplete until its beats and word gate pass."""

import uuid

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.disclaimer import DISCLAIMER
from app.core.errors import InferenceError
from app.core.text import word_count
from app.db.models import OutlineNode, Project, ProseChunk
from app.inference.base import ChatBackend, GenerationSettings
from app.inference.budget import completion_budget
from app.narrative.completion import refresh_rollup
from app.narrative.prose import _duplicate_paragraphs, _long_sentences, _rejects

FINISHED = {"COMPLETED", "APPROVED"}


def _ordered_beats(session: Session, project_id: str) -> list[OutlineNode]:
    beats = session.query(OutlineNode).filter(OutlineNode.project_id == project_id, OutlineNode.level == "beat").all()
    nodes = {row.id: row for row in session.query(OutlineNode).filter(OutlineNode.project_id == project_id).all()}

    def key(beat: OutlineNode):
        scene = nodes.get(beat.parent_id)
        part = nodes.get(scene.parent_id) if scene else None
        chapter = nodes.get(part.parent_id) if part else None
        arc = nodes.get(chapter.parent_id) if chapter else None
        return (
            arc.ordinal if arc else 0,
            chapter.ordinal if chapter else 0,
            part.ordinal if part else 0,
            scene.ordinal if scene else 0,
            beat.ordinal,
        )

    return sorted(beats, key=key)


def next_beat(session: Session, project_id: str) -> OutlineNode | None:
    for beat in _ordered_beats(session, project_id):
        if beat.completion_status in {"NEEDS_REVIEW", "FAILED"}:
            return None
        if beat.completion_status not in FINISHED:
            return beat
    return None


def _accepted_text(session: Session, beat_id: str) -> str:
    rows = (
        session.query(ProseChunk)
        .filter(ProseChunk.beat_id == beat_id, ProseChunk.status == "ACCEPTED")
        .order_by(ProseChunk.ordinal)
        .all()
    )
    return "\n\n".join(row.prose for row in rows)


def _memory(session: Session, beat: OutlineNode) -> str:
    nodes = {row.id: row for row in session.query(OutlineNode).filter(OutlineNode.project_id == beat.project_id).all()}
    scene = nodes.get(beat.parent_id)
    part = nodes.get(scene.parent_id) if scene else None
    chapter = nodes.get(part.parent_id) if part else None
    lines = []
    if chapter and chapter.continuity.get("facts"):
        lines.append("Sự kiện chương: " + " | ".join(chapter.continuity["facts"][-6:]))
    if part and part.continuity.get("facts"):
        lines.append("Sự kiện phần: " + " | ".join(part.continuity["facts"][-6:]))
    if scene and scene.continuity.get("facts"):
        lines.append("Sự kiện cảnh: " + " | ".join(scene.continuity["facts"][-4:]))
    previous = _accepted_text(session, beat.id)
    if previous:
        words = previous.split()
        lines.append("Đoạn liền trước: " + " ".join(words[-120:]))
    return "\n".join(lines)


def _remember(node: OutlineNode, fact: str) -> None:
    facts = list((node.continuity or {}).get("facts") or [])
    if fact and fact not in facts:
        facts.append(fact)
    node.continuity = {**(node.continuity or {}), "facts": facts}


def _recount(session: Session, node: OutlineNode) -> None:
    if node.level == "beat":
        rows = session.query(ProseChunk).filter(ProseChunk.beat_id == node.id, ProseChunk.status == "ACCEPTED").all()
        node.actual_words = sum(row.word_count for row in rows)
        return
    children = session.query(OutlineNode).filter(OutlineNode.parent_id == node.id).all()
    node.actual_words = sum(child.actual_words or 0 for child in children)


def generate_next_chunk(session: Session, project: Project, settings: Settings, backend: ChatBackend, *, context_tokens: int | None = None) -> dict:
    """Generate and commit at most one chunk. Never marks the volume complete by itself."""
    beat = next_beat(session, project.id)
    if beat is None:
        status = refresh_rollup(session, project, ratio=settings.part_completion_ratio)
        return {"status": "idle", "volume_status": status}
    done = int((project.config or {}).get("chunks_this_job") or 0)
    if done >= settings.max_chunks_per_job:
        beat.completion_status = "PAUSED"
        project.workflow_state = "PAUSED"
        return {"status": "paused", "reason": "chunk budget for this job is exhausted", "beat_id": beat.id}
    scene = session.get(OutlineNode, beat.parent_id)
    part = session.get(OutlineNode, scene.parent_id) if scene else None
    chapter = session.get(OutlineNode, part.parent_id) if part else None
    for node in (beat, scene, part, chapter):
        if node and node.completion_status == "PLANNED":
            node.completion_status = "GENERATING"
    existing = (
        session.query(ProseChunk).filter(ProseChunk.beat_id == beat.id).order_by(ProseChunk.ordinal.desc()).first()
    )
    ordinal = (existing.ordinal + 1) if existing else 1
    action = beat.payload.get("action") or beat.summary
    system = (
        f"Bạn viết fanfiction dark fantasy bằng tiếng Việt. {DISCLAIMER} "
        "Chỉ viết tiếp một đoạn. Không JSON. Không tiêu đề. Không chữ Hán. "
        "Đoạn này phải có hành động hoặc thông tin mới. Cấm lặp câu đã có."
    )
    user = (
        f"Nhịp: {beat.title}\n"
        f"Hành động mới: {action}\n"
        f"Mục đích: {beat.payload.get('purpose', '')}\n"
        f"Thông tin mới: {beat.payload.get('new_information', '')}\n"
        f"Mục tiêu nhân vật: {beat.payload.get('objective', '')}\n"
        f"{_memory(session, beat)}\n"
        f"Viết khoảng {min(settings.chunk_target_words, beat.target_words or settings.chunk_target_words)} từ rồi dừng."
    )
    messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    limit = context_tokens or settings.context_tokens
    prompt_tokens = max(1, word_count(system + user))
    try:
        room = completion_budget(limit, prompt_tokens, min(700, max(200, settings.chunk_target_words * 2)))
    except InferenceError as exc:
        beat.completion_status = "PAUSED"
        return {"status": "paused", "reason": str(exc), "beat_id": beat.id}
    result = backend.generate(
        messages,
        GenerationSettings(
            temperature=settings.temperature_write,
            seed=settings.seed + ordinal,
            max_tokens=room,
            task="write_chunk",
            json_object=False,
        ),
    )
    piece = (result.text or "").strip()
    previous = _accepted_text(session, beat.id)
    rejected = ""
    if result.finish_reason in {"truncation", "length"} and piece and piece[-1] not in ".!?…":
        rejected = "truncated"
    elif not piece:
        rejected = "empty"
    elif _rejects(previous, piece) or _duplicate_paragraphs(([previous] if previous else []) + [piece]):
        rejected = "repetition"
    elif _long_sentences(piece) & _long_sentences(previous):
        rejected = "repetition"
    project.config = {**(project.config or {}), "chunks_this_job": done + 1}
    if rejected:
        retries = int((beat.checkpoint or {}).get("retries") or 0) + 1
        history = list(beat.revision_history or [])
        history.append({"ordinal": ordinal, "reason": rejected})
        beat.revision_history = history
        beat.checkpoint = {**(beat.checkpoint or {}), "retries": retries, "last_reject": rejected}
        session.add(
            ProseChunk(
                id=str(uuid.uuid4()),
                project_id=project.id,
                beat_id=beat.id,
                scene_id=scene.id if scene else "",
                part_id=part.id if part else "",
                ordinal=ordinal,
                prose=piece,
                word_count=word_count(piece),
                prompt_tokens=result.prompt_tokens or prompt_tokens,
                completion_tokens=result.completion_tokens,
                finish_reason=result.finish_reason or rejected,
                status="REJECTED",
            )
        )
        if retries >= 3:
            beat.completion_status = "NEEDS_REVIEW"
            if part:
                part.completion_status = "NEEDS_REVIEW"
            refresh_rollup(session, project, ratio=settings.part_completion_ratio)
        return {"status": "rejected", "reason": rejected, "beat_id": beat.id, "ordinal": ordinal}
    session.add(
        ProseChunk(
            id=str(uuid.uuid4()),
            project_id=project.id,
            beat_id=beat.id,
            scene_id=scene.id if scene else "",
            part_id=part.id if part else "",
            ordinal=ordinal,
            prose=piece,
            word_count=word_count(piece),
            prompt_tokens=result.prompt_tokens or prompt_tokens,
            completion_tokens=result.completion_tokens,
            finish_reason=result.finish_reason or "stop",
            status="ACCEPTED",
        )
    )
    session.flush()
    _recount(session, beat)
    fact = beat.payload.get("new_information") or action
    if beat.actual_words >= (beat.target_words or 1):
        beat.completion_status = "COMPLETED"
        beat.status = "approved"
        _remember(beat, fact)
        if scene:
            _remember(scene, fact)
            _recount(session, scene)
            scene_beats = session.query(OutlineNode).filter(OutlineNode.parent_id == scene.id, OutlineNode.level == "beat").all()
            if scene_beats and all(item.completion_status in FINISHED for item in scene_beats):
                scene.completion_status = "COMPLETED"
                scene.status = "approved"
                if part:
                    _remember(part, fact)
            _recount(session, scene)
        if part:
            _recount(session, part)
        if chapter:
            _remember(chapter, fact)
            _recount(session, chapter)
    else:
        beat.checkpoint = {**(beat.checkpoint or {}), "ordinal": ordinal}
    volume_status = refresh_rollup(session, project, ratio=settings.part_completion_ratio)
    return {
        "status": "accepted",
        "beat_id": beat.id,
        "ordinal": ordinal,
        "words": word_count(piece),
        "volume_status": volume_status,
    }
