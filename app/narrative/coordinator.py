"""Campaign runner. A slice limit pauses a batch; it does not end the volume."""

import json
import os
import time
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import InferenceError
from app.db.models import Job, OutlineNode, Project, ProseChunk
from app.inference.base import ChatBackend
from app.inference.resources import probe_gpu
from app.narrative.completion import refresh_rollup
from app.narrative.export import write_epub, write_markdown
from app.narrative.longform import generate_next_chunk, next_beat
from app.narrative.repair import repair_part
from app.narrative.volume17_budget import BEAT_ROLES, planned_volume, scene_count_for, split_exact, beat_count_for

DONE = {"COMPLETED", "APPROVED"}


def _ordered_parts(session: Session, project_id: str) -> list[OutlineNode]:
    nodes = {row.id: row for row in session.query(OutlineNode).filter(OutlineNode.project_id == project_id).all()}
    parts = [row for row in nodes.values() if row.level == "part"]

    def key(part: OutlineNode):
        chapter = nodes.get(part.parent_id)
        arc = nodes.get(chapter.parent_id) if chapter else None
        return (arc.ordinal if arc else 0, chapter.ordinal if chapter else 0, part.ordinal)

    return sorted(parts, key=key)


def sync_targets(session: Session, project: Project) -> None:
    """Raise stored targets to the 350k plan. Accepted chunks stay attached to their beats."""
    plan = planned_volume()
    by_title = {
        part["title"]: part
        for arc in plan["arcs"]
        for chapter in arc["chapters"]
        for part in chapter["parts"]
    }
    chapters = {row.id: row for row in session.query(OutlineNode).filter(OutlineNode.project_id == project.id, OutlineNode.level == "chapter").all()}
    for part in session.query(OutlineNode).filter(OutlineNode.project_id == project.id, OutlineNode.level == "part").all():
        spec = by_title.get(part.title)
        if not spec:
            continue
        part.target_words = spec["target_words"]
        existing = []
        for scene in session.query(OutlineNode).filter(OutlineNode.parent_id == part.id, OutlineNode.level == "scene").all():
            existing.extend(session.query(OutlineNode).filter(OutlineNode.parent_id == scene.id, OutlineNode.level == "beat").all())
        have = sum(beat.target_words or 0 for beat in existing)
        gap = spec["target_words"] - have
        if gap < 150 or (part.actual_words or 0) >= int(spec["target_words"] * 0.9):
            continue
        scenes = (
            session.query(OutlineNode)
            .filter(OutlineNode.parent_id == part.id, OutlineNode.level == "scene")
            .order_by(OutlineNode.ordinal)
            .all()
        )
        if not scenes:
            continue
        used = " ".join(scene.title.lower() for scene in scenes)
        missing = [(name, text) for name, text in BEAT_ROLES if name not in used]
        if not missing:
            missing = list(BEAT_ROLES)
        scene_total = max(1, min(len(missing), scene_count_for(gap)))
        sizes = split_exact(gap, scene_total)
        next_scene_ordinal = scenes[-1].ordinal + 1
        for size, (role_name, role_text) in zip(sizes, missing):
            scene_id = os.urandom(16).hex()
            session.add(
                OutlineNode(
                    id=scene_id,
                    project_id=project.id,
                    parent_id=part.id,
                    level="scene",
                    ordinal=next_scene_ordinal,
                    title=f"{part.title} — {role_name}",
                    summary=spec["outcome"],
                    payload={
                        "viewpoint_character": spec["viewpoint"],
                        "location": spec["location"],
                        "objective": f"{role_name}: {spec['conflict']}",
                    },
                    target_words=size,
                    completion_status="PLANNED",
                )
            )
            beat_sizes = split_exact(size, beat_count_for(size))
            for beat_index, beat_words in enumerate(beat_sizes, start=1):
                beat_role, beat_text = BEAT_ROLES[(beat_index - 1) % len(BEAT_ROLES)]
                session.add(
                    OutlineNode(
                        id=os.urandom(16).hex(),
                        project_id=project.id,
                        parent_id=scene_id,
                        level="beat",
                        ordinal=beat_index,
                        title=f"{part.title} — {beat_role} {next_scene_ordinal}.{beat_index}",
                        summary=spec["outcome"],
                        payload={
                            "action": (
                                f"{spec['viewpoint']} tại {spec['location']} thực hiện «{beat_role}» của {part.title}. "
                                f"{beat_text} Xung đột hiện tại: {spec['conflict']}"
                            ),
                            "purpose": beat_role,
                            "new_information": beat_text if beat_index > 1 else spec["conflict"],
                            "objective": spec["outcome"] if beat_index == len(beat_sizes) else beat_text,
                        },
                        target_words=beat_words,
                        completion_status="PLANNED",
                    )
                )
            next_scene_ordinal += 1
    for chapter in chapters.values():
        parts = session.query(OutlineNode).filter(OutlineNode.parent_id == chapter.id, OutlineNode.level == "part").all()
        chapter.target_words = sum(part.target_words or 0 for part in parts)
    volume = session.query(OutlineNode).filter(OutlineNode.project_id == project.id, OutlineNode.level == "volume").one_or_none()
    if volume:
        volume.target_words = sum(chapter.target_words or 0 for chapter in chapters.values())
        volume.continuity = {
            **(volume.continuity or {}),
            "canon_coverage_status": "partial",
            "manuscript_completion_status": volume.completion_status,
        }


def write_progress(session: Session, project: Project, path: Path, *, status: str, note: str = "") -> dict:
    def count(level: str, done: bool = False) -> int:
        query = session.query(OutlineNode).filter(OutlineNode.project_id == project.id, OutlineNode.level == level)
        if done:
            query = query.filter(OutlineNode.completion_status.in_(list(DONE)))
        return query.count()

    current_part = next((part for part in _ordered_parts(session, project.id) if part.completion_status not in DONE), None)
    current_chapter = None
    if current_part is not None:
        current_chapter = session.get(OutlineNode, current_part.parent_id)
    current_beat = next_beat(session, project.id)
    recent = (
        session.query(ProseChunk)
        .filter(ProseChunk.project_id == project.id, ProseChunk.status == "ACCEPTED", ProseChunk.completion_tokens > 0)
        .order_by(ProseChunk.created_at.desc())
        .limit(8)
        .all()
    )
    tokens_per_second = 0.0
    if len(recent) >= 2 and recent[0].created_at and recent[-1].created_at:
        span = (recent[0].created_at - recent[-1].created_at).total_seconds()
        fresh = [row for row in recent if recent[0].created_at and row.created_at and (recent[0].created_at - row.created_at).total_seconds() <= 900]
        if len(fresh) >= 2:
            span = (fresh[0].created_at - fresh[-1].created_at).total_seconds()
            recent = fresh
        if span > 0:
            tokens_per_second = round(sum(row.completion_tokens for row in recent[:-1]) / span, 2)
    gpu = probe_gpu()
    accepted = session.query(ProseChunk).filter(ProseChunk.project_id == project.id, ProseChunk.status == "ACCEPTED").count()
    rejected = session.query(ProseChunk).filter(ProseChunk.project_id == project.id, ProseChunk.status == "REJECTED").count()
    words = sum(row.word_count for row in session.query(ProseChunk).filter(ProseChunk.project_id == project.id, ProseChunk.status == "ACCEPTED").all())
    volume = session.query(OutlineNode).filter(OutlineNode.project_id == project.id, OutlineNode.level == "volume").one_or_none()
    payload = {
        "volume_target_words": volume.target_words if volume else 0,
        "actual_accepted_words": words,
        "chapters_completed": count("chapter", True),
        "chapters_total": count("chapter"),
        "parts_completed": count("part", True),
        "parts_total": count("part"),
        "scenes_completed": count("scene", True),
        "scenes_total": count("scene"),
        "beats_completed": count("beat", True),
        "beats_total": count("beat"),
        "current_chapter": current_chapter.title if current_chapter else "",
        "current_part": current_part.title if current_part else "",
        "current_beat": current_beat.title if current_beat else "",
        "status": status,
        "inference_tokens_per_second": tokens_per_second,
        "gpu_memory_used_mb": gpu.used_mb if gpu.available else 0,
        "gpu_memory_free_mb": gpu.free_mb if gpu.available else 0,
        "accepted_chunks": accepted,
        "rejected_chunks": rejected,
        "pending_review": [part.title for part in _ordered_parts(session, project.id) if part.completion_status == "NEEDS_REVIEW"],
        "checkpoint": {"part_id": current_part.id if current_part else "", "note": note},
        "manuscript_finished": bool(volume and volume.completion_status == "COMPLETED"),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    with (path.parent / "campaign.log").open("a", encoding="utf-8") as handle:
        handle.write(
            f"{status}\twords={words}\tpart={payload['current_part']}\tbeat={payload['current_beat']}\tgpu_mb={payload['gpu_memory_used_mb']}\n"
        )
    return payload


def run_campaign(
    session: Session,
    project: Project,
    settings: Settings,
    backend: ChatBackend,
    *,
    until_complete: bool = True,
    repair_reviews: bool = True,
    export_on_completion: bool = True,
    progress_path: Path,
    export_dir: Path | None = None,
    max_slices: int | None = None,
) -> dict:
    sync_targets(session, project)
    session.commit()
    slices = 0
    repairs: dict[str, int] = {}
    while True:
        if max_slices is not None and slices >= max_slices:
            return write_progress(session, project, progress_path, status="slice_paused", note="slice cap for this process")
        refresh_rollup(session, project, ratio=settings.part_completion_ratio)
        volume = session.query(OutlineNode).filter(OutlineNode.project_id == project.id, OutlineNode.level == "volume").one()
        if volume.completion_status == "COMPLETED":
            if export_on_completion and export_dir:
                export_dir.mkdir(parents=True, exist_ok=True)
                write_markdown(session, project, export_dir / "complete-volume17.md")
                write_epub(session, project, export_dir / "complete-volume17.epub")
            return write_progress(session, project, progress_path, status="manuscript_completed")
        part = next((item for item in _ordered_parts(session, project.id) if item.completion_status not in DONE), None)
        if part is None:
            return write_progress(session, project, progress_path, status="blocked", note="no open part and volume is not complete")
        job = session.query(Job).filter(Job.project_id == project.id, Job.kind == "volume_campaign").one_or_none()
        if job and job.state in {"PAUSED", "CANCELLED"}:
            return write_progress(session, project, progress_path, status=job.state.lower())
        if part.completion_status == "NEEDS_REVIEW":
            if not repair_reviews:
                return write_progress(session, project, progress_path, status="needs_review", note=part.title)
            used = repairs.get(part.id, 0)
            if used >= 3:
                return write_progress(session, project, progress_path, status="blocked", note=f"repair attempts exhausted for {part.title}")
            repair_part(session, project, part, ratio=settings.part_completion_ratio)
            repairs[part.id] = used + 1
            session.commit()
            write_progress(session, project, progress_path, status="repairing", note=part.title)
            continue
        project.config = {**(project.config or {}), "chunks_this_job": 0}
        session.commit()
        slices += 1
        for _ in range(settings.max_chunks_per_job):
            if job:
                session.refresh(job)
                if job.state in {"PAUSED", "CANCELLED"}:
                    return write_progress(session, project, progress_path, status=job.state.lower())
            try:
                result = generate_next_chunk(session, project, settings, backend)
            except InferenceError as exc:
                time.sleep(min(30, 2 ** min(repairs.get("errors", 0), 4)))
                repairs["errors"] = repairs.get("errors", 0) + 1
                session.commit()
                if repairs["errors"] >= 5:
                    return write_progress(session, project, progress_path, status="blocked", note=str(exc))
                continue
            session.commit()
            write_progress(session, project, progress_path, status=result.get("status", "running"), note=part.title)
            if result.get("status") == "paused" and "chunk budget" in result.get("reason", ""):
                break
            if result.get("status") == "idle":
                break
            session.refresh(part)
            if part.completion_status in DONE | {"NEEDS_REVIEW"}:
                break
        if not until_complete:
            return write_progress(session, project, progress_path, status="slice_done")
