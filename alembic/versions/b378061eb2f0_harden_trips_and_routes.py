"""harden_trips_and_routes

Revision ID: b378061eb2f0
Revises: 95b0c3305cc9
Create Date: 2026-04-14 00:42:02.335935
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b378061eb2f0'
down_revision: str | None = '95b0c3305cc9'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("qr_tokens") as batch_op:
        batch_op.drop_index(op.f("ix_qr_tokens_booking_id"))
        batch_op.create_index(op.f("ix_qr_tokens_booking_id"), ["booking_id"], unique=True)


def downgrade() -> None:
    with op.batch_alter_table("qr_tokens") as batch_op:
        batch_op.drop_index(op.f("ix_qr_tokens_booking_id"))
        batch_op.create_index(op.f("ix_qr_tokens_booking_id"), ["booking_id"], unique=False)
        batch_op.create_unique_constraint(op.f("qr_tokens_booking_id_key"), ["booking_id"])
