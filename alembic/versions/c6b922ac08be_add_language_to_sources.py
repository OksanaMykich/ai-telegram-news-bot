"""add language to sources

Revision ID: c6b922ac08be
Revises: 39fbab6f208d
Create Date: 2026-08-07 20:29:35.444573

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c6b922ac08be"
down_revision: Union[str, Sequence[str], None] = "39fbab6f208d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "sources",
        sa.Column("language", sa.String(length=10), nullable=False, server_default="en"),
    )
    op.alter_column("sources", "language", server_default=None)


def downgrade() -> None:
    op.drop_column("sources", "language")