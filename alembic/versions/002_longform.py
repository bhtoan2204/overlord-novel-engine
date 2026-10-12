"""Add part-level word tracking and committed prose chunks."""

from alembic import op

from app.db.init_db import ensure_longform_columns

revision = "002_longform"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from app.db.base import Base
    from app.db import models  # noqa: F401

    bind = op.get_bind()
    Base.metadata.create_all(bind)
    ensure_longform_columns(bind)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS prose_chunks")
    op.execute("DROP TABLE IF EXISTS preserved_drafts")
