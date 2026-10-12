"""Schema creation and full-text index. Alembic's initial revision calls the same helpers."""

from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.db.base import Base
from app.db import models  # noqa: F401

FTS_SQL = """
CREATE VIRTUAL TABLE IF NOT EXISTS segment_fts USING fts5(
    text,
    segment_id UNINDEXED,
    tokenize='unicode61'
)
"""


def init_database(engine: Engine) -> None:
    Base.metadata.create_all(engine)
    with engine.begin() as connection:
        connection.execute(text(FTS_SQL))


def rebuild_fts(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(text("DELETE FROM segment_fts"))
        connection.execute(
            text(
                """
                INSERT INTO segment_fts(text, segment_id)
                SELECT text, id FROM segments
                """
            )
        )
