"""FastAPI application factory."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.core.config import Settings, get_settings
from app.core.logging import configure_logging
from app.db.base import make_engine, make_session_factory, session_scope
from app.db.init_db import init_database
from app.inference.llama_cpp import select_backend
from app.narrative.pipeline import recover_interrupted
from app.retrieval.embeddings import build_embedder
from app.retrieval.hybrid import VectorIndex
from app.workers.runner import GenerationRunner

PACKAGE = Path(__file__).resolve().parent


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    for name in ("incoming", "processed", "knowledge", "generated", "checkpoints", "models"):
        (settings.data_dir / name).mkdir(parents=True, exist_ok=True)
    database_path = settings.sqlite_path()
    if database_path is not None:
        database_path.parent.mkdir(parents=True, exist_ok=True)
    engine = make_engine(settings)
    init_database(engine)
    factory = make_session_factory(engine)
    with session_scope(factory) as session:
        recover_interrupted(session)
    embedder = build_embedder(settings.embedding_backend, settings.embedding_model)
    index = VectorIndex(embedder.dim, settings.data_dir / "processed" / "segments.faiss")
    backend = select_backend(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        yield
        stop = getattr(app.state.backend, "stop", None)
        if callable(stop):
            stop()

    app = FastAPI(title="Overlord Novel Engine", lifespan=lifespan)
    app.state.settings = settings
    app.state.engine = engine
    app.state.session_factory = factory
    app.state.embedder = embedder
    app.state.index = index
    app.state.backend = backend
    app.state.runner = GenerationRunner(factory, settings, backend, embedder, index)
    app.state.templates = Jinja2Templates(directory=str(PACKAGE / "templates"))
    app.mount("/static", StaticFiles(directory=str(PACKAGE / "static")), name="static")

    from app.api.routes import router

    app.include_router(router)
    return app
