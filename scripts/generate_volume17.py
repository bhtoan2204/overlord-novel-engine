"""Durable Volume 17 campaign. A slice is not the end of the book."""

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.core.config import Settings
from app.db.base import make_engine, make_session_factory
from app.db.init_db import init_database
from app.db.models import Job, Project
from app.inference.llama_cpp import LlamaCppBackend
from app.narrative.coordinator import run_campaign


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--until-complete", action="store_true")
    parser.add_argument("--target-words", type=int, default=350_000)
    parser.add_argument("--max-vram-mb", type=int, default=11000)
    parser.add_argument("--repair-reviews", action="store_true")
    parser.add_argument("--export-on-completion", action="store_true")
    args = parser.parse_args()
    out = ROOT / "data" / "generated" / "volume17"
    out.mkdir(parents=True, exist_ok=True)
    lock = out / "worker.lock"
    if lock.exists():
        pid = int(lock.read_text().strip() or "0")
        if pid and _pid_alive(pid):
            raise SystemExit(f"A campaign worker is already running as pid {pid}.")
    lock.write_text(str(os.getpid()), encoding="utf-8")
    settings = Settings(
        volume_target_words=args.target_words,
        vram_budget_mb=args.max_vram_mb,
        vram_reserve_mb=1000,
        cooldown_seconds=0,
        max_chunks_per_job=12,
        context_tokens=8192,
    )
    engine = make_engine(settings)
    init_database(engine)
    session = make_session_factory(engine)()
    project = session.query(Project).order_by(Project.created_at).first()
    if project is None:
        raise SystemExit("No project in the database.")
    job = session.query(Job).filter(Job.project_id == project.id, Job.kind == "volume_campaign").one_or_none()
    if job is None:
        job = Job(id=os.urandom(16).hex(), project_id=project.id, kind="volume_campaign", state="GENERATING", payload={}, checkpoint={})
        session.add(job)
    elif args.resume and job.state in {"PAUSED", "FAILED"}:
        job.state = "GENERATING"
        job.error = None
    session.commit()
    backend = LlamaCppBackend(settings)
    try:
        result = run_campaign(
            session,
            project,
            settings,
            backend,
            until_complete=args.until_complete,
            repair_reviews=args.repair_reviews,
            export_on_completion=args.export_on_completion,
            progress_path=out / "progress.json",
            export_dir=out,
        )
        print(result["status"], result["actual_accepted_words"], "/", result["volume_target_words"])
    finally:
        backend.stop()
        if lock.exists() and lock.read_text().strip() == str(os.getpid()):
            lock.unlink()


if __name__ == "__main__":
    main()
