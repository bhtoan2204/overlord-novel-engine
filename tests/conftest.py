import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.factory import create_app


@pytest.fixture()
def settings(tmp_path: Path) -> Settings:
    return Settings(
        database_url=f"sqlite:///{tmp_path / 'test.db'}",
        data_dir=tmp_path / "data",
        inference_backend="mock",
        embedding_backend="hash",
        cooldown_seconds=0,
        planner_mode="deterministic",
        log_level="WARNING",
        training_enabled=False,
    )


@pytest.fixture()
def app(settings: Settings):
    return create_app(settings)


@pytest.fixture()
def client(app):
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def session(app):
    factory = app.state.session_factory
    db = factory()
    try:
        yield db
    finally:
        db.close()


def load_notes() -> dict:
    path = Path(__file__).resolve().parents[1] / "data" / "seed" / "volume_16_study_notes.json"
    return json.loads(path.read_text(encoding="utf-8"))
