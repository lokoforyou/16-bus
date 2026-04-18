"""make rank queue ticket trip nullable

Revision ID: 20260417_0008
Revises: 20260416_0001_0007
Create Date: 2026-04-17 00:08:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260417_0008"
down_revision = "20260416_0001_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("rank_queue_tickets", "trip_id", existing_type=sa.String(length=64), nullable=True)


def downgrade() -> None:
    op.alter_column("rank_queue_tickets", "trip_id", existing_type=sa.String(length=64), nullable=False)
