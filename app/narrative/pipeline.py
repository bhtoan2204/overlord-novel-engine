"""Scene pipeline, checkpoints, and recovery."""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import WorkflowError
from app.core.text import word_count
from app.core.workflow import (
    GENERATION_READY,
    INTERRUPTED_SCENE_STATES,
    WorkflowState,
    can_transition,
)
from app.db.models import CanonReview, Job, OutlineNode, Project, SceneDraft, Snapshot, StateDiff, ValidationReport
from app.inference.base import ChatBackend
from app.knowledge.schemas import SceneSpec
from app.narrative.planner import build_deterministic_tree, replace_outline
from app.narrative.preferences import preference_instructions
from app.narrative.validators import blocking, disagreement, run_heuristics
from app.narrative.world import apply_diff, initial_state, validate_diff
from app.narrative.writer import write_scene
from app.retrieval.context import build_context_pack
from app.retrieval.hybrid import VectorIndex, hybrid_search


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _set_state(project: Project, target: WorkflowState) -> None:
    current = WorkflowState(project.workflow_state)
    if not can_transition(current, target):
        raise WorkflowError(f"Cannot move from {current.value} to {target.value}.")
    project.workflow_state = target.value
    project.updated_at = _now()


def checkpoint_path(settings: Settings, project_id: str) -> Path:
    path = settings.data_dir / "checkpoints" / f"{project_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def save_checkpoint(settings: Settings, job: Job, project: Project, payload: dict) -> None:
    job.checkpoint = payload
    job.updated_at = _now()
    body = {"job_id": job.id, "project_id": project.id, "state": project.workflow_state, "checkpoint": payload}
    checkpoint_path(settings, project.id).write_text(json.dumps(body, ensure_ascii=False, indent=2), encoding="utf-8")


def recover_interrupted(session: Session) -> int:
    """Move crashed scene jobs back to PAUSED. Approved scenes stay approved."""
    jobs = session.query(Job).filter(Job.state.in_([state.value for state in INTERRUPTED_SCENE_STATES])).all()
    for job in jobs:
        job.state = WorkflowState.PAUSED.value
        job.error = "Process stopped. Restored the last checkpoint; approved scenes were kept."
        job.updated_at = _now()
        project = session.get(Project, job.project_id)
        if project and project.workflow_state in {state.value for state in INTERRUPTED_SCENE_STATES}:
            project.resume_state = project.workflow_state
            project.workflow_state = WorkflowState.PAUSED.value
            project.updated_at = _now()
    return len(jobs)


class GenerationControl:
    def __init__(self, session: Session, job: Job | None):
        self.session = session
        self.job = job

    def poll(self) -> None:
        if self.job is None:
            return
        self.session.refresh(self.job)
        if self.job.state == WorkflowState.CANCELLED.value:
            raise WorkflowError("Generation was cancelled.")
        if self.job.state == WorkflowState.PAUSED.value:
            raise WorkflowError("Generation is paused.")


def create_project(session: Session, title: str, disclaimer: str) -> Project:
    project = Project(
        id=str(uuid.uuid4()),
        title=title,
        disclaimer=disclaimer,
        workflow_state=WorkflowState.NOT_STARTED.value,
        config={"language": "vi", "unofficial": True},
    )
    session.add(project)
    return project


def create_outline(session: Session, project: Project, settings: Settings, backend: ChatBackend | None = None) -> dict:
    if project.workflow_state in {
        WorkflowState.OUTLINE_APPROVED.value,
        WorkflowState.SCENE_GENERATING.value,
        WorkflowState.VOLUME_COMPLETED.value,
    }:
        raise WorkflowError("The outline is already approved or generation has started.")
    if settings.planner_mode == "llm":
        if backend is None:
            raise WorkflowError("LLM planning needs an inference backend.")
        from app.inference.base import GenerationSettings
        from app.inference.structured import generate_model
        from app.knowledge.schemas import LlmOutline

        tree_model = generate_model(
            backend,
            [
                {"role": "system", "content": "TASK: plan. Lập dàn ý fanfiction không chính thức. Trả JSON."},
                {"role": "user", "content": json.dumps({"premise": project.title}, ensure_ascii=False)},
            ],
            GenerationSettings(settings.temperature_plan, settings.seed, 2000, "plan"),
            LlmOutline,
            settings.max_json_attempts,
        )
        tree = _tree_from_llm(tree_model.model_dump(), settings.scene_target_words)
    else:
        tree = build_deterministic_tree(session, settings.volume_target_words)
    replace_outline(session, project, tree)
    if project.workflow_state == WorkflowState.NOT_STARTED.value:
        _set_state(project, WorkflowState.SOURCES_PREPARED)
        _set_state(project, WorkflowState.KNOWLEDGE_EXTRACTED)
        _set_state(project, WorkflowState.CANON_VERIFIED)
    elif project.workflow_state == WorkflowState.SOURCES_PREPARED.value:
        _set_state(project, WorkflowState.KNOWLEDGE_EXTRACTED)
        _set_state(project, WorkflowState.CANON_VERIFIED)
    elif project.workflow_state == WorkflowState.KNOWLEDGE_EXTRACTED.value:
        _set_state(project, WorkflowState.CANON_VERIFIED)
    if project.workflow_state == WorkflowState.CANON_VERIFIED.value:
        _set_state(project, WorkflowState.OUTLINE_CREATED)
    elif project.workflow_state != WorkflowState.OUTLINE_CREATED.value:
        project.workflow_state = WorkflowState.OUTLINE_CREATED.value
    return tree


def _tree_from_llm(payload: dict, words: int) -> dict:
    chapters = []
    for chapter in payload["chapters"]:
        scenes = []
        for scene in chapter["scenes"]:
            scenes.append(
                {
                    "title": scene["title"],
                    "viewpoint": scene["viewpoint_character"],
                    "location": scene["location"],
                    "participants": scene.get("participating_characters") or [scene["viewpoint_character"]],
                    "tone": scene.get("emotional_tone") or "",
                    "objective": scene["summary"],
                    "outcome": scene.get("desired_outcome") or scene["summary"],
                    "events": scene.get("required_events") or [scene["summary"]],
                }
            )
        chapters.append(
            {
                "kind": "chapter",
                "title": chapter["title"],
                "summary": chapter["summary"],
                "requires": [],
                "uncertainties": payload.get("alternatives") or [],
                "caused_by": None,
                "scenes": scenes,
            }
        )
    return {
        "title": "Overlord — Tập 17 (fanfiction không chính thức)",
        "premise": payload["premise"],
        "disclaimer": "Fanfiction không chính thức.",
        "alternatives": payload.get("alternatives") or [],
        "target_words": words * max(1, sum(len(chapter["scenes"]) for chapter in chapters)),
        "words_per_scene": words,
        "arcs": [{"title": "Dàn ý mô hình", "chapters": chapters}],
    }


def approve_outline(session: Session, project: Project) -> None:
    if project.workflow_state != WorkflowState.OUTLINE_APPROVED.value:
        if project.workflow_state != WorkflowState.OUTLINE_CREATED.value:
            raise WorkflowError("Create an outline before approving it.")
        _set_state(project, WorkflowState.OUTLINE_APPROVED)
    for node in session.query(OutlineNode).filter(OutlineNode.project_id == project.id).all():
        node.approved = True
        if node.level == "scene" and node.status == "draft":
            node.status = "planned"


def verify_canon(session: Session, project: Project) -> dict:
    from app.core.canon import beats
    from app.db.models import Assertion

    grouped: dict[tuple, list] = {}
    for row in session.query(Assertion).filter(Assertion.kind == "fact").all():
        grouped.setdefault((row.subject_name, row.predicate, row.timeline), []).append(row)
    conflicts = []
    adopted = []
    for key, rows in grouped.items():
        main_rows = [row for row in rows if row.timeline == "main"]
        alternate = [row for row in rows if row.timeline != "main"]
        winner = None
        for row in main_rows:
            if winner is None or beats(row.canon_level, winner.canon_level):
                if winner and row.value != winner.value:
                    conflicts.append(
                        {
                            "subject": key[0],
                            "predicate": key[1],
                            "kept": row.value,
                            "kept_level": row.canon_level,
                            "dropped": winner.value,
                            "dropped_level": winner.canon_level,
                        }
                    )
                winner = row
        if winner:
            adopted.append(
                {
                    "subject": winner.subject_name,
                    "predicate": winner.predicate,
                    "value": winner.value,
                    "canon_level": winner.canon_level,
                    "evidence": winner.evidence_source_id,
                }
            )
        if alternate:
            conflicts.append(
                {
                    "subject": key[0],
                    "predicate": key[1],
                    "note": "Alternate-universe assertions were excluded from the main timeline.",
                    "count": len(alternate),
                }
            )
    report = {"conflicts": conflicts, "adopted": adopted}
    session.add(CanonReview(id=str(uuid.uuid4()), project_id=project.id, report=report))
    existing = session.query(Snapshot).filter(Snapshot.project_id == project.id, Snapshot.version == 1).one_or_none()
    if existing is None:
        state = initial_state(session)
        session.add(Snapshot(id=str(uuid.uuid4()), project_id=project.id, version=1, node_id=None, state=state))
        project.snapshot_version = 1
    if project.workflow_state == WorkflowState.KNOWLEDGE_EXTRACTED.value:
        _set_state(project, WorkflowState.CANON_VERIFIED)
    elif project.workflow_state == WorkflowState.SOURCES_PREPARED.value:
        _set_state(project, WorkflowState.KNOWLEDGE_EXTRACTED)
        _set_state(project, WorkflowState.CANON_VERIFIED)
    return report


def latest_state(session: Session, project: Project) -> dict:
    row = (
        session.query(Snapshot)
        .filter(Snapshot.project_id == project.id, Snapshot.version == project.snapshot_version)
        .one_or_none()
    )
    if row is None:
        return initial_state(session)
    return row.state


def rollback_state(session: Session, project: Project, version: int) -> None:
    if version < 1 or version > project.snapshot_version:
        raise WorkflowError("That snapshot version does not exist.")
    session.query(Snapshot).filter(Snapshot.project_id == project.id, Snapshot.version > version).delete()
    project.snapshot_version = version
    project.updated_at = _now()


def _scene_nodes(session: Session, project_id: str) -> list[OutlineNode]:
    return (
        session.query(OutlineNode)
        .filter(OutlineNode.project_id == project_id, OutlineNode.level == "scene")
        .all()
    )


def next_scene(session: Session, project_id: str) -> OutlineNode | None:
    scenes = _scene_nodes(session, project_id)
    chapters = {
        row.id: row
        for row in session.query(OutlineNode).filter(OutlineNode.project_id == project_id, OutlineNode.level == "chapter")
    }
    arcs = {
        row.id: row
        for row in session.query(OutlineNode).filter(OutlineNode.project_id == project_id, OutlineNode.level == "arc")
    }

    def sort_key(scene: OutlineNode):
        chapter = chapters.get(scene.parent_id)
        arc = arcs.get(chapter.parent_id) if chapter else None
        return (arc.ordinal if arc else 0, chapter.ordinal if chapter else 0, scene.ordinal)

    for scene in sorted(scenes, key=sort_key):
        if scene.status != "approved":
            return scene
    return None


def _spec_for(session: Session, project: Project, node: OutlineNode, settings: Settings) -> SceneSpec:
    previous = ""
    state = latest_state(session, project)
    recent = state.get("recent_events") or []
    if recent:
        previous = str(recent[-1].get("summary") or recent[-1].get("title") or "")
    payload = node.payload or {}
    prohibited = list(payload.get("prohibited_contradictions") or [])
    return SceneSpec(
        scene_id=node.id,
        viewpoint_character=payload.get("viewpoint_character") or "Ainz Ooal Gown",
        location=payload.get("location") or "Đại Lăng Nazarick",
        timestamp=payload.get("timestamp") or "ngay sau Tập 16",
        scene_objective=payload.get("scene_objective") or node.summary,
        participating_characters=payload.get("participating_characters") or [],
        known_information=payload.get("known_information") or [],
        required_events=payload.get("required_events") or [],
        prohibited_contradictions=prohibited,
        target_word_count=int(payload.get("target_word_count") or settings.scene_target_words),
        previous_scene_summary=previous,
        emotional_tone=payload.get("emotional_tone") or "",
        desired_outcome=payload.get("desired_outcome") or "",
    )


def generate_scene(
    session: Session,
    project: Project,
    settings: Settings,
    backend: ChatBackend,
    embedder,
    index: VectorIndex,
    job: Job | None = None,
    force: bool = False,
) -> dict:
    if project.workflow_state not in {state.value for state in GENERATION_READY | {WorkflowState.OUTLINE_APPROVED}}:
        if project.workflow_state not in {
            WorkflowState.OUTLINE_APPROVED.value,
            WorkflowState.CHAPTER_PLANNED.value,
            WorkflowState.SCENE_APPROVED.value,
            WorkflowState.STATE_COMMITTED.value,
            WorkflowState.CHAPTER_COMPLETED.value,
            WorkflowState.PAUSED.value,
            WorkflowState.FAILED.value,
        }:
            raise WorkflowError("Approve the outline before generating scenes.")
    if project.workflow_state == WorkflowState.PAUSED.value:
        project.workflow_state = project.resume_state or WorkflowState.OUTLINE_APPROVED.value
    node = next_scene(session, project.id)
    if node is None:
        project.workflow_state = WorkflowState.VOLUME_COMPLETED.value
        project.updated_at = _now()
        return {"done": True}
    if node.status == "approved" and not force:
        return {"skipped": node.id}
    control = GenerationControl(session, job)
    control.poll()
    if job:
        job.attempts += 1
        if job.attempts > job.max_attempts:
            job.state = WorkflowState.FAILED.value
            raise WorkflowError("Retry limit reached for this scene.")
        job.state = WorkflowState.SCENE_GENERATING.value
    project.workflow_state = WorkflowState.SCENE_GENERATING.value
    spec = _spec_for(session, project, node, settings)
    context_limit = settings.context_tokens
    ensure_started = getattr(backend, "ensure_started", None)
    if ensure_started is not None:
        context_limit = ensure_started().context_tokens
    hits = hybrid_search(session, embedder, index, spec.scene_objective + " " + spec.location)
    pack = build_context_pack(
        session,
        viewpoint=spec.viewpoint_character,
        hits=hits,
        token_budget=min(settings.retrieval_token_budget, max(400, context_limit // 6)),
    )
    spec.prohibited_contradictions = list(dict.fromkeys(spec.prohibited_contradictions + pack.get("prohibited_knowledge", [])))
    spec.known_information = [section["text"] for section in pack["sections"][:8]]
    notes = preference_instructions(session, project.id)
    draft = write_scene(backend, spec, pack, settings, preference_notes=notes)
    save_checkpoint(settings, job, project, {"scene_id": node.id, "phase": "written"}) if job else None
    iteration = 1
    reports: list[dict] = []
    while True:
        control.poll()
        project.workflow_state = WorkflowState.SCENE_VALIDATING.value
        if job:
            job.state = WorkflowState.SCENE_VALIDATING.value
        reports = run_heuristics(session, spec, draft.prose)
        row = SceneDraft(
            id=str(uuid.uuid4()),
            project_id=project.id,
            node_id=node.id,
            iteration=iteration,
            prose=draft.prose,
            spec={**spec.model_dump(), "word_count": word_count(draft.prose)},
            selected=False,
        )
        session.add(row)
        session.flush()
        review = disagreement(reports)
        for report in reports:
            session.add(
                ValidationReport(
                    id=str(uuid.uuid4()),
                    draft_id=row.id,
                    validator=report["validator"],
                    scores=report["scores"],
                    issues=report["issues"],
                    recommendations=report["recommendations"],
                    human_review=review,
                )
            )
        problems = blocking(reports)
        if not problems and not review:
            row.selected = True
            node.status = "approved"
            project.workflow_state = WorkflowState.SCENE_APPROVED.value
            _commit_state(session, project, node, draft.state_diff)
            if job:
                job.state = WorkflowState.STATE_COMMITTED.value
                save_checkpoint(
                    settings,
                    job,
                    project,
                    {"scene_id": node.id, "phase": "committed", "approved_scene_id": node.id},
                )
            _refresh_chapter_status(session, project, node)
            return {"scene_id": node.id, "draft_id": row.id, "status": "approved", "iterations": iteration}
        if iteration >= settings.max_revision_iterations:
            row.selected = False
            node.status = "human_review"
            project.workflow_state = WorkflowState.FAILED.value
            if job:
                job.state = WorkflowState.FAILED.value
                job.error = "Validators still disagree or still report a continuity error."
            return {
                "scene_id": node.id,
                "draft_id": row.id,
                "status": "human_review",
                "iterations": iteration,
                "human_review": review,
                "issues": problems,
            }
        project.workflow_state = WorkflowState.SCENE_REVISING.value
        if job:
            job.state = WorkflowState.SCENE_REVISING.value
            save_checkpoint(settings, job, project, {"scene_id": node.id, "phase": "revising", "iteration": iteration})
        recommendations = []
        for report in reports:
            recommendations.extend(report["recommendations"])
        draft = write_scene(
            backend,
            spec,
            pack,
            settings,
            revise=True,
            previous_prose=draft.prose,
            recommendations=recommendations,
            preference_notes=notes,
        )
        iteration += 1


def _commit_state(session: Session, project: Project, node: OutlineNode, diff) -> None:
    reason = validate_diff(diff, latest_state(session, project))
    record = StateDiff(
        id=str(uuid.uuid4()),
        project_id=project.id,
        node_id=node.id,
        diff=diff.model_dump(),
        validated=reason is None,
        committed=reason is None,
        rejection_reason=reason,
    )
    session.add(record)
    if reason:
        raise WorkflowError(reason)
    updated = apply_diff(latest_state(session, project), diff, node.id)
    version = project.snapshot_version + 1
    session.add(Snapshot(id=str(uuid.uuid4()), project_id=project.id, version=version, node_id=node.id, state=updated))
    project.snapshot_version = version
    project.workflow_state = WorkflowState.STATE_COMMITTED.value


def _refresh_chapter_status(session: Session, project: Project, node: OutlineNode) -> None:
    siblings = session.query(OutlineNode).filter(OutlineNode.parent_id == node.parent_id, OutlineNode.level == "scene").all()
    if siblings and all(item.status == "approved" for item in siblings):
        chapter = session.get(OutlineNode, node.parent_id)
        if chapter:
            chapter.status = "approved"
        project.workflow_state = WorkflowState.CHAPTER_COMPLETED.value
    pending = next_scene(session, project.id)
    if pending is None and project.workflow_state != WorkflowState.VOLUME_COMPLETED.value:
        chapters = session.query(OutlineNode).filter(OutlineNode.project_id == project.id, OutlineNode.level == "chapter").all()
        if chapters and all(item.status == "approved" for item in chapters):
            project.workflow_state = WorkflowState.VOLUME_COMPLETED.value
        else:
            project.workflow_state = WorkflowState.CHAPTER_COMPLETED.value
    elif pending is not None and project.workflow_state == WorkflowState.CHAPTER_COMPLETED.value:
        project.workflow_state = WorkflowState.CHAPTER_PLANNED.value
