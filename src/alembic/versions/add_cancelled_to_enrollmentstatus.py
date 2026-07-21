"""add cancelled to enrollmentstatus

Revision ID: b1a2c3d4e5f6
Revises: e736e44c4843
Create Date: 2026-07-20 00:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b1a2c3d4e5f6"
down_revision: str | Sequence[str] | None = "e736e44c4843"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE enrollmentstatus ADD VALUE IF NOT EXISTS 'CANCELLED'")


def downgrade() -> None:
    # PostgreSQL doesn't support removing enum values directly.
    # A full enum recreation would be needed, which is out of scope here.
    pass
