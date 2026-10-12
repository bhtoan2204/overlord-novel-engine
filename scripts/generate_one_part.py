"""Generate the first Volume 17 part with Qwen. Stops when that part completes or the job budget ends."""

import json
from pathlib import Path

from app.core.config import Settings
from app.core.text import word_count
from app.db.base import make_engine, make_session_factory
from app.db.init_db import init_database
from app.db.models import OutlineNode, Project
from app.inference.llama_cpp import LlamaCppBackend
from app.narrative.export import part_text
from app.narrative.longform import generate_next_chunk
from app.narrative.pipeline import approve_outline, create_outline

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "generated" / "volume17"


def main() -> None:
    settings = Settings(cooldown_seconds=1, context_tokens=4096, max_chunks_per_job=40)
    engine = make_engine(settings)
    init_database(engine)
    session = make_session_factory(engine)()
    project = session.query(Project).order_by(Project.created_at).first()
    if project is None:
        raise SystemExit("No project in the database. Import the study notes and create a project first.")
    project.workflow_state = "CANON_VERIFIED"
    project.config = {**(project.config or {}), "chunks_this_job": 0}
    create_outline(session, project, settings)
    approve_outline(session, project)
    session.commit()
    part = (
        session.query(OutlineNode)
        .filter(OutlineNode.project_id == project.id, OutlineNode.level == "part")
        .order_by(OutlineNode.ordinal)
        .first()
    )
    backend = LlamaCppBackend(settings)
    log = []
    try:
        for _ in range(settings.max_chunks_per_job):
            result = generate_next_chunk(session, project, settings, backend)
            session.commit()
            log.append(result)
            print(json.dumps(result, ensure_ascii=False), flush=True)
            session.refresh(part)
            if part.completion_status == "COMPLETED":
                break
            if result.get("status") in {"paused", "idle"} or part.completion_status == "NEEDS_REVIEW":
                break
    finally:
        backend.stop()
    session.refresh(part)
    prose = part_text(session, part.id)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "part-1.md").write_text(
        "Fanfiction không chính thức. Không phải chính sử.\n\n"
        + (f"**Chưa hoàn thành — {part.completion_status}.**\n\n" if part.completion_status != "COMPLETED" else "")
        + prose
        + "\n",
        encoding="utf-8",
    )
    payload = {
        "title": part.title,
        "completion_status": part.completion_status,
        "target_words": part.target_words,
        "actual_words": part.actual_words,
        "exported_words": word_count(prose),
        "requests": log,
    }
    (OUT / "part-1.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": part.completion_status, "words": part.actual_words, "target": part.target_words}, ensure_ascii=False))


if __name__ == "__main__":
    main()
