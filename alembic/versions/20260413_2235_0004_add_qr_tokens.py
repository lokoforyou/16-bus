"""add qr tokens

Revision ID: 20260413_2235_0004
Revises: 20260413_2215_0003
Create Date: 2026-04-13 22:35:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260413_2235_0004"
down_revision: str | None = "20260413_2215_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "qr_tokens",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("booking_id", sa.String(length=64), nullable=False),
        sa.Column("state", sa.String(length=32), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("scanned_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["booking_id"], ["bookings.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("booking_id"),
    )
    op.create_index(op.f("ix_qr_tokens_booking_id"), "qr_tokens", ["booking_id"])
    op.create_index(op.f("ix_qr_tokens_state"), "qr_tokens", ["state"])


def downgrade() -> None:
    op.drop_index(op.f("ix_qr_tokens_state"), table_name="qr_tokens")
    op.drop_index(op.f("ix_qr_tokens_booking_id"), table_name="qr_tokens")
    op.drop_table("qr_tokens")
