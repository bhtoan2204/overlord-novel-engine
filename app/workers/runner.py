"""One background generation thread. A second start request is rejected."""

import threading

from sqlalchemy.orm import Session

from app.core.errors import WorkflowError
from app.core.workflow import WorkflowState
from app.db.models import Job, Project
from app.narrative.pipeline import generate_scene


class GenerationRunner:
    def __init__(self, session_factory, settings, backend, embedder, index) -> None:
        self.session_factory = session_factory
        self.settings = settings
        self.backend = backend
        self.embedder = embedder
        self.index = index
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

    def running(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    def start(self, project_id: str, limit_scenes: int = 1) -> str:
        with self._lock:
            if self.running():
                raise WorkflowError("A generation job is already running.")
            session = self.session_factory()
            try:
                project = session.get(Project, project_id)
                if project is None:
                    raise WorkflowError("Unknown project.")
                job = Job(
                    id=__import__("uuid").uuid4().__str__(),
                    project_id=project_id,
                    kind="generate_scenes",
                    state=WorkflowState.CHAPTER_PLANNED.value,
                    payload={"limit_scenes": limit_scenes},
                    checkpoint={},
                    max_attempts=3,
                )
                session.add(job)
                session.commit()
                job_id = job.id
            finally:
                session.close()
            self._thread = threading.Thread(target=self._run, args=(job_id, limit_scenes), daemon=True)
            self._thread.start()
            return job_id

    def _run(self, job_id: str, limit_scenes: int) -> None:
        session: Session = self.session_factory()
        try:
            job = session.get(Job, job_id)
            project = session.get(Project, job.project_id)
            produced = 0
            while produced < limit_scenes:
                session.refresh(job)
                if job.state in {WorkflowState.PAUSED.value, WorkflowState.CANCELLED.value}:
                    break
                result = generate_scene(session, project, self.settings, self.backend, self.embedder, self.index, job)
                session.commit()
                produced += 1
                if result.get("done") or result.get("status") == "human_review":
                    break
                if self.settings.cooldown_seconds:
                    import time

                    time.sleep(self.settings.cooldown_seconds)
            else:
                if job.state not in {WorkflowState.FAILED.value, WorkflowState.PAUSED.value, WorkflowState.CANCELLED.value}:
                    job.state = project.workflow_state
            session.commit()
        except Exception as exc:
            session.rollback()
            job = session.get(Job, job_id)
            if job is not None:
                job.state = WorkflowState.FAILED.value
                job.error = str(exc)
                session.commit()
        finally:
            session.close()

    def set_state(self, job_id: str, state: str) -> None:
        session = self.session_factory()
        try:
            job = session.get(Job, job_id)
            if job is None:
                raise WorkflowError("Unknown job.")
            job.state = state
            project = session.get(Project, job.project_id)
            if state == WorkflowState.PAUSED.value and project is not None:
                project.resume_state = project.workflow_state
                project.workflow_state = WorkflowState.PAUSED.value
            if state == WorkflowState.CANCELLED.value and project is not None:
                project.workflow_state = WorkflowState.CANCELLED.value
            session.commit()
        finally:
            session.close()
