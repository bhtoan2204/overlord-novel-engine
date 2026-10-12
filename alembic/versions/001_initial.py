"""Initial schema. Later revisions should alter tables rather than recreate them."""

from alembic import op

from app.db.init_db import FTS_SQL

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    from app.db.base import Base
    from app.db import models  # noqa: F401

    bind = op.get_bind()
    Base.metadata.create_all(bind)
    op.execute(FTS_SQL)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS segment_fts")
    bind = op.get_bind()
    from app.db.base import Base
    from app.db import models  # noqa: F401

    Base.metadata.drop_all(bind)
