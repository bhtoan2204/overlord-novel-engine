"""HTML pages and the small JSON API used by the dashboard."""

from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.core.disclaimer import DISCLAIMER
from app.core.errors import EngineError, WorkflowError
from app.core.workflow import WorkflowState
from app.db.base import session_scope
from app.db.models import (
    CatalogEntry,
    Character,
    Event,
    Faction,
    Feedback,
    Job,
    Location,
    OutlineNode,
    Plotline,
    Project,
    SceneDraft,
    Source,
    ValidationReport,
    WorldRule,
)
from app.inference.resources import cpu_snapshot, probe_gpu
from app.narrative.export import render_markdown, write_epub, write_markdown, write_pdf
from app.narrative.pipeline import (
    approve_outline,
    create_outline,
    create_project,
    generate_scene,
    rollback_state,
    verify_canon,
)
from app.narrative.preferences import AXES
from app.services.library import discover_and_store, import_file

router = APIRouter()


def db(request: Request):
    return session_scope(request.app.state.session_factory)


def current_project(session: Session) -> Project:
    project = session.query(Project).order_by(Project.created_at.desc()).first()
    if project is None:
        project = create_project(session, "Overlord — Tập 17 (fanfiction không chính thức)", DISCLAIMER)
        session.flush()
    return project


def render(request: Request, name: str, **context):
    context["request"] = request
    context["disclaimer"] = DISCLAIMER
    return request.app.state.templates.TemplateResponse(request, name, context)


def _redirect(path: str, message: str = "", error: str = "") -> RedirectResponse:
    glue = "&" if "?" in path else "?"
    if message:
        path = f"{path}{glue}message={quote(message)}"
    elif error:
        path = f"{path}{glue}error={quote(error)}"
    return RedirectResponse(path, status_code=303)


@router.get("/")
def dashboard(request: Request):
    with db(request) as session:
        project = current_project(session)
        sources = session.query(Source).count()
        characters = session.query(Character).count()
        scenes = session.query(OutlineNode).filter(OutlineNode.project_id == project.id, OutlineNode.level == "scene").count()
        approved = session.query(OutlineNode).filter(OutlineNode.project_id == project.id, OutlineNode.level == "scene", OutlineNode.status == "approved").count()
        jobs = session.query(Job).order_by(Job.updated_at.desc()).limit(8).all()
        gpu = probe_gpu()
        cpu = cpu_snapshot()
        return render(
            request,
            "dashboard.html",
            project=project,
            sources=sources,
            characters=characters,
            scenes=scenes,
            approved=approved,
            jobs=jobs,
            gpu=gpu,
            cpu=cpu,
            message=request.query_params.get("message", ""),
            error=request.query_params.get("error", ""),
        )


@router.get("/library")
def library(request: Request):
    with db(request) as session:
        sources = session.query(Source).order_by(Source.ingestion_timestamp.desc()).all()
        return render(request, "library.html", sources=sources, message=request.query_params.get("message", ""), error=request.query_params.get("error", ""))


@router.post("/library/upload")
async def upload_source(
    request: Request,
    file: UploadFile = File(...),
    title: str = Form(...),
    source_type: str = Form("user_notes"),
    canon_level: str = Form("USER_INTERPRETATION"),
    license_status: str = Form(...),
    timeline: str = Form("main"),
    language: str = Form("vi"),
    training_allowed: bool = Form(False),
):
    settings = request.app.state.settings
    destination = settings.data_dir / "incoming" / Path(file.filename or "upload.txt").name
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(await file.read())
    try:
        with db(request) as session:
            project = current_project(session)
            source, created = import_file(
                session,
                settings,
                request.app.state.embedder,
                request.app.state.index,
                destination,
                title=title,
                source_type=source_type,
                canon_level=canon_level,
                license_status=license_status,
                language=language,
                timeline=timeline,
                training_allowed=training_allowed,
                backend=request.app.state.backend if destination.suffix.lower() != ".json" else None,
                project=project,
            )
        note = "imported" if created else "already-imported"
        return _redirect("/library", f"{note}:{source.id}")
    except EngineError as exc:
        return _redirect("/library", error=str(exc))


@router.post("/library/sample")
def load_sample(request: Request):
    path = request.app.state.settings.root / "data" / "seed" / "volume_16_study_notes.json"
    with db(request) as session:
        project = current_project(session)
        source, created = import_file(
            session,
            request.app.state.settings,
            request.app.state.embedder,
            request.app.state.index,
            path,
            title="Ghi chú nghiên cứu gốc sau tập 16",
            source_type="user_notes",
            canon_level="USER_INTERPRETATION",
            license_status="original-structured-notes",
            timeline="main",
            project=project,
        )
    return _redirect("/library", "sample-loaded" if created else "sample-already-present")


@router.get("/knowledge")
def knowledge(request: Request):
    with db(request) as session:
        return render(
            request,
            "knowledge.html",
            characters=session.query(Character).order_by(Character.name).all(),
            factions=session.query(Faction).order_by(Faction.name).all(),
            locations=session.query(Location).order_by(Location.name).all(),
            events=session.query(Event).order_by(Event.chronological_order).all(),
            plotlines=session.query(Plotline).order_by(Plotline.priority).all(),
            rules=session.query(WorldRule).all(),
        )


@router.get("/planner")
def planner(request: Request):
    with db(request) as session:
        project = current_project(session)
        nodes = session.query(OutlineNode).filter(OutlineNode.project_id == project.id).all()
        return render(request, "planner.html", project=project, nodes=nodes, message=request.query_params.get("message", ""), error=request.query_params.get("error", ""))


@router.post("/planner/create")
def planner_create(request: Request):
    try:
        with db(request) as session:
            project = current_project(session)
            create_outline(session, project, request.app.state.settings, request.app.state.backend)
        return _redirect("/planner", "outline-created")
    except (EngineError, ValueError, WorkflowError) as exc:
        return _redirect("/planner", error=str(exc))


@router.post("/planner/approve")
def planner_approve(request: Request):
    try:
        with db(request) as session:
            approve_outline(session, current_project(session))
        return _redirect("/planner", "outline-approved")
    except WorkflowError as exc:
        return _redirect("/planner", error=str(exc))


@router.post("/planner/node")
def planner_edit(request: Request, node_id: str = Form(...), summary: str = Form(...)):
    with db(request) as session:
        node = session.get(OutlineNode, node_id)
        if node and not node.approved:
            node.summary = summary
    return _redirect("/planner", "outline-updated")


@router.post("/planner/verify")
def planner_verify(request: Request):
    with db(request) as session:
        verify_canon(session, current_project(session))
    return _redirect("/planner", "canon-verified")


@router.get("/reader")
def reader(request: Request):
    query = request.query_params.get("q", "").strip()
    with db(request) as session:
        project = current_project(session)
        scenes = session.query(OutlineNode).filter(OutlineNode.project_id == project.id, OutlineNode.level == "scene").all()
        drafts = []
        for scene in scenes:
            draft = (
                session.query(SceneDraft)
                .filter(SceneDraft.node_id == scene.id, SceneDraft.selected.is_(True))
                .order_by(SceneDraft.iteration.desc())
                .first()
            )
            if draft and (not query or query.lower() in draft.prose.lower() or query.lower() in scene.title.lower()):
                drafts.append((scene, draft))
        return render(request, "reader.html", project=project, drafts=drafts, query=query)


@router.get("/reader/{scene_id}")
def reader_scene(request: Request, scene_id: str):
    with db(request) as session:
        scene = session.get(OutlineNode, scene_id)
        drafts = session.query(SceneDraft).filter(SceneDraft.node_id == scene_id).order_by(SceneDraft.iteration).all()
        reports = []
        if drafts:
            reports = session.query(ValidationReport).filter(ValidationReport.draft_id.in_([item.id for item in drafts])).all()
        return render(request, "scene.html", scene=scene, drafts=drafts, reports=reports)


@router.get("/generate")
def generate_page(request: Request):
    with db(request) as session:
        project = current_project(session)
        jobs = session.query(Job).filter(Job.project_id == project.id).order_by(Job.updated_at.desc()).limit(10).all()
        return render(
            request,
            "generate.html",
            project=project,
            jobs=jobs,
            running=request.app.state.runner.running(),
            message=request.query_params.get("message", ""),
            error=request.query_params.get("error", ""),
        )


@router.post("/generate/step")
def generate_step(request: Request):
    """Generate the next scene in the request thread. Used by the UI and tests."""
    try:
        with db(request) as session:
            project = current_project(session)
            result = generate_scene(
                session,
                project,
                request.app.state.settings,
                request.app.state.backend,
                request.app.state.embedder,
                request.app.state.index,
            )
        return _redirect("/generate", "scene-" + result.get("status", "done"))
    except (EngineError, WorkflowError) as exc:
        return _redirect("/generate", error=str(exc))


@router.post("/generate/start")
def generate_start(request: Request, limit_scenes: int = Form(1)):
    try:
        with db(request) as session:
            project = current_project(session)
            project_id = project.id
        job_id = request.app.state.runner.start(project_id, limit_scenes=max(1, min(limit_scenes, 3)))
        return _redirect("/generate", f"job-{job_id}")
    except WorkflowError as exc:
        return _redirect("/generate", error=str(exc))


@router.post("/generate/control")
def generate_control(request: Request, job_id: str = Form(...), action: str = Form(...)):
    state = {"pause": WorkflowState.PAUSED.value, "resume": WorkflowState.CHAPTER_PLANNED.value, "cancel": WorkflowState.CANCELLED.value}[action]
    try:
        request.app.state.runner.set_state(job_id, state)
    except WorkflowError as exc:
        return _redirect("/generate", error=str(exc))
    return _redirect("/generate", action)


@router.post("/generate/retry")
def generate_retry(request: Request):
    with db(request) as session:
        project = current_project(session)
        if project.workflow_state == WorkflowState.FAILED.value:
            project.workflow_state = WorkflowState.OUTLINE_APPROVED.value
            project.resume_state = None
    return _redirect("/generate", "retry-armed")


@router.get("/settings")
def settings_page(request: Request):
    return render(request, "settings.html", settings=request.app.state.settings, message=request.query_params.get("message", ""))


@router.post("/settings")
def settings_save(
    request: Request,
    context_tokens: int = Form(...),
    vram_budget_mb: int = Form(...),
    vram_reserve_mb: int = Form(...),
    cpu_limit_percent: int = Form(...),
    temperature_write: float = Form(...),
    scene_target_words: int = Form(...),
    cooldown_seconds: float = Form(...),
    active_model: str = Form(...),
    planner_mode: str = Form(...),
    inference_backend: str = Form(...),
):
    updated = request.app.state.settings.model_copy(
        update={
            "context_tokens": context_tokens,
            "vram_budget_mb": vram_budget_mb,
            "vram_reserve_mb": vram_reserve_mb,
            "cpu_limit_percent": cpu_limit_percent,
            "temperature_write": temperature_write,
            "scene_target_words": scene_target_words,
            "cooldown_seconds": cooldown_seconds,
            "active_model": active_model,
            "planner_mode": planner_mode,
            "inference_backend": inference_backend,
        }
    )
    request.app.state.settings = updated
    request.app.state.runner.settings = updated
    path = updated.data_dir / "runtime_settings.json"
    path.write_text(updated.model_dump_json(), encoding="utf-8")
    return _redirect("/settings", "saved")


@router.get("/feedback")
def feedback_page(request: Request):
    with db(request) as session:
        project = current_project(session)
        scenes = session.query(OutlineNode).filter(OutlineNode.project_id == project.id, OutlineNode.level == "scene", OutlineNode.status == "approved").all()
        rows = session.query(Feedback).filter(Feedback.project_id == project.id).all()
        return render(request, "feedback.html", project=project, scenes=scenes, rows=rows, axes=AXES)


@router.post("/feedback")
def feedback_save(request: Request, node_id: str = Form(...), comment: str = Form(""), plot_quality: int = Form(...), character_accuracy: int = Form(...), dialogue: int = Form(...), emotional_impact: int = Form(...), worldbuilding: int = Form(...), suspense: int = Form(...), overall: int = Form(...)):
    ratings = {
        "plot_quality": plot_quality,
        "character_accuracy": character_accuracy,
        "dialogue": dialogue,
        "emotional_impact": emotional_impact,
        "worldbuilding": worldbuilding,
        "suspense": suspense,
        "overall": overall,
    }
    with db(request) as session:
        project = current_project(session)
        session.add(Feedback(id=__import__("uuid").uuid4().hex, project_id=project.id, node_id=node_id, ratings=ratings, comment=comment))
    return _redirect("/feedback", "saved")


@router.get("/export")
def export_page(request: Request):
    return render(request, "export.html", message=request.query_params.get("message", ""), error=request.query_params.get("error", ""))


@router.post("/export/{fmt}")
def export_book(request: Request, fmt: str):
    settings = request.app.state.settings
    try:
        with db(request) as session:
            project = current_project(session)
            target = settings.data_dir / "generated" / f"{project.id}.{fmt if fmt != 'markdown' else 'md'}"
            if fmt == "markdown":
                write_markdown(session, project, target)
            elif fmt == "epub":
                write_epub(session, project, target)
            elif fmt == "pdf":
                write_pdf(session, project, target, settings.font_path)
            else:
                raise EngineError("Supported exports: markdown, epub, pdf.")
            payload = target.read_bytes()
            filename = target.name
        return FileResponse(target, filename=filename)
    except EngineError as exc:
        return _redirect("/export", error=str(exc))


@router.get("/discover")
def discover_page(request: Request):
    with db(request) as session:
        entries = session.query(CatalogEntry).order_by(CatalogEntry.discovered_at.desc()).limit(100).all()
        return render(request, "discover.html", entries=entries, message=request.query_params.get("message", ""), error=request.query_params.get("error", ""))


@router.post("/discover")
def discover_post(request: Request, url: str = Form(...)):
    try:
        with db(request) as session:
            status, count = discover_and_store(session, url, request.app.state.settings)
        return _redirect("/discover", f"{status}-{count}")
    except EngineError as exc:
        return _redirect("/discover", error=str(exc))


@router.post("/api/state/rollback")
def api_rollback(request: Request, version: int = Form(...)):
    with db(request) as session:
        rollback_state(session, current_project(session), version)
    return _redirect("/generate", f"rolled-back-{version}")


@router.get("/api/health")
def health(request: Request):
    backend = request.app.state.backend.health()
    gpu = probe_gpu()
    return {"ok": True, "backend": backend, "gpu": gpu.__dict__, "cpu": cpu_snapshot()}


@router.get("/api/outline")
def api_outline(request: Request):
    with db(request) as session:
        project = current_project(session)
        nodes = session.query(OutlineNode).filter(OutlineNode.project_id == project.id).all()
        return {
            "project": project.workflow_state,
            "nodes": [
                {"id": node.id, "level": node.level, "title": node.title, "summary": node.summary, "parent_id": node.parent_id, "payload": node.payload}
                for node in nodes
            ],
        }


@router.get("/api/markdown")
def api_markdown(request: Request):
    with db(request) as session:
        return {"markdown": render_markdown(session, current_project(session))}
