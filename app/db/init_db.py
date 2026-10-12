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


OUTLINE_COLUMNS = {
    "target_words": "INTEGER DEFAULT 0",
    "actual_words": "INTEGER DEFAULT 0",
    "completion_status": "VARCHAR(40) DEFAULT 'PLANNED'",
    "checkpoint": "JSON",
    "revision_history": "JSON",
    "continuity": "JSON",
}


def ensure_longform_columns(connection) -> None:
    rows = connection.execute(text("PRAGMA table_info(outline_nodes)")).fetchall()
    present = {row[1] for row in rows}
    for name, ddl in OUTLINE_COLUMNS.items():
        if name not in present:
            connection.execute(text(f"ALTER TABLE outline_nodes ADD COLUMN {name} {ddl}"))


def init_database(engine: Engine) -> None:
    Base.metadata.create_all(engine)
    with engine.begin() as connection:
        connection.execute(text(FTS_SQL))
        ensure_longform_columns(connection)


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
