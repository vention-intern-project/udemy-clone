"""add server_default to published_at

Revision ID: ec13af1d6f2e
Revises: 01ca1f9a7356
Create Date: 2026-07-02 13:25:10.143819

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ec13af1d6f2e"
down_revision: str | Sequence[str] | None = "01ca1f9a7356"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "courses",
        "published_at",
        server_default=sa.func.now(),
    )


def downgrade() -> None:
    op.alter_column(
        "courses",
        "published_at",
        server_default=None,
    )
