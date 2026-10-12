"""Completion is explicit. A missing next scene is not a finished volume."""

from sqlalchemy.orm import Session

from app.db.models import OutlineNode, Project

TERMINAL_OK = {"COMPLETED", "APPROVED"}


def _children(session: Session, parent_id: str, level: str) -> list[OutlineNode]:
    return (
        session.query(OutlineNode)
        .filter(OutlineNode.parent_id == parent_id, OutlineNode.level == level)
        .order_by(OutlineNode.ordinal)
        .all()
    )


def part_is_complete(part: OutlineNode, scenes: list[OutlineNode], beats: list[OutlineNode], *, ratio: float = 0.90) -> bool:
    if not scenes or not beats:
        return False
    if any(scene.completion_status not in TERMINAL_OK for scene in scenes):
        return False
    if any(beat.completion_status not in TERMINAL_OK for beat in beats):
        return False
    if part.completion_status in {"NEEDS_REVIEW", "NEEDS_EXPANSION", "FAILED"}:
        return False
    if (part.continuity or {}).get("blocking"):
        return False
    target = part.target_words or 0
    if part.payload.get("editorial_override"):
        return True
    if part.payload.get("short_transition"):
        return part.actual_words >= int(part.payload.get("minimum_words") or 1)
    if target <= 0:
        return False
    lower = int(target * ratio)
    upper = int(target * 1.2)
    return lower <= part.actual_words <= upper


def refresh_rollup(session: Session, project: Project, *, ratio: float = 0.90) -> str:
    """Recompute part, chapter, and volume status from children. Returns the volume status."""
    volume = (
        session.query(OutlineNode)
        .filter(OutlineNode.project_id == project.id, OutlineNode.level == "volume")
        .one_or_none()
    )
    chapters = session.query(OutlineNode).filter(OutlineNode.project_id == project.id, OutlineNode.level == "chapter").all()
    if not chapters:
        if volume:
            volume.completion_status = "PLANNED"
        return "PLANNED"
    for chapter in chapters:
        parts = _children(session, chapter.id, "part")
        if not parts:
            chapter.completion_status = "PLANNED"
            continue
        for part in parts:
            scenes = _children(session, part.id, "scene")
            beats = []
            for scene in scenes:
                beats.extend(_children(session, scene.id, "beat"))
            beats_done = bool(beats) and all(beat.completion_status in TERMINAL_OK for beat in beats)
            scenes_done = bool(scenes) and all(scene.completion_status in TERMINAL_OK for scene in scenes)
            if part_is_complete(part, scenes, beats, ratio=ratio):
                part.completion_status = "COMPLETED"
                part.status = "approved"
            elif scenes_done and beats_done and part.completion_status != "NEEDS_REVIEW":
                part.completion_status = "NEEDS_REVIEW"
            elif part.completion_status == "COMPLETED":
                part.completion_status = "GENERATING"
        chapter.actual_words = sum(part.actual_words or 0 for part in parts)
        if parts and all(part.completion_status in TERMINAL_OK for part in parts):
            chapter.completion_status = "COMPLETED"
            chapter.status = "approved"
        elif any(part.completion_status == "NEEDS_REVIEW" for part in parts):
            chapter.completion_status = "NEEDS_REVIEW"
        elif chapter.completion_status == "COMPLETED":
            chapter.completion_status = "GENERATING"
    done = all(chapter.completion_status in TERMINAL_OK for chapter in chapters)
    kinds = {chapter.payload.get("kind") for chapter in chapters}
    required = {"prologue", "chapter", "epilogue"}
    if volume:
        volume.actual_words = sum(chapter.actual_words or 0 for chapter in chapters)
        from app.knowledge.coverage import coverage_report

        dataset_ready = coverage_report(session)["full_text_volumes"] >= 16 or bool((project.config or {}).get("dataset_override"))
        if done and required <= kinds and not dataset_ready:
            volume.completion_status = "NEEDS_EXPANSION"
            volume.continuity = {**(volume.continuity or {}), "dataset": "Volumes 1–16 are not ingested as full text."}
        elif done and required <= kinds and dataset_ready:
            volume.completion_status = "COMPLETED"
            project.workflow_state = "VOLUME_COMPLETED"
        else:
            if volume.completion_status == "COMPLETED":
                volume.completion_status = "GENERATING"
            if project.workflow_state == "VOLUME_COMPLETED":
                project.workflow_state = "CHAPTER_PLANNED"
        return volume.completion_status
    return "COMPLETED" if done else "GENERATING"
