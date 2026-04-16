"""add audit logs, rank queue tickets, policies, and postgis extension

Revision ID: 20260416_0001_0007
Revises: 20260414_1200_0006
Create Date: 2026-04-16 00:01:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260416_0001_0007"
down_revision: str | None = "20260414_1200_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(length=128), nullable=False),
        sa.Column("action", sa.String(length=128), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.String(length=128), nullable=True),
        sa.Column("actor_id", sa.String(length=128), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audit_logs_action"), "audit_logs", ["action"], unique=False)
    op.create_index(op.f("ix_audit_logs_actor_id"), "audit_logs", ["actor_id"], unique=False)
    op.create_index(op.f("ix_audit_logs_entity_id"), "audit_logs", ["entity_id"], unique=False)
    op.create_index(op.f("ix_audit_logs_entity_type"), "audit_logs", ["entity_type"], unique=False)

    op.create_table(
        "policies",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("organization_id", sa.String(length=64), nullable=False),
        sa.Column("route_id", sa.String(length=64), nullable=True),
        sa.Column("wait_time_sla_minutes", sa.Integer(), nullable=False),
        sa.Column("pickup_grace_minutes", sa.Integer(), nullable=False),
        sa.Column("cancellation_grace_minutes", sa.Integer(), nullable=False),
        sa.Column("eta_breach_credit_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("no_show_fee_type", sa.String(length=32), nullable=False),
        sa.Column("no_show_fee_value", sa.Numeric(10, 2), nullable=False),
        sa.Column("pricing_rules_json", sa.JSON(), nullable=False),
        sa.Column("refund_rules_json", sa.JSON(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["route_id"], ["routes.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_policies_organization_id"), "policies", ["organization_id"], unique=False)
    op.create_index(op.f("ix_policies_route_id"), "policies", ["route_id"], unique=False)

    op.create_table(
        "rank_queue_tickets",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("rank_id", sa.String(length=64), nullable=False),
        sa.Column("trip_id", sa.String(length=64), nullable=False),
        sa.Column("queue_number", sa.Integer(), nullable=False),
        sa.Column("payment_status", sa.String(length=32), nullable=False),
        sa.Column("qr_token_id", sa.String(length=64), nullable=True),
        sa.Column("state", sa.String(length=32), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["trip_id"], ["trips.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_rank_queue_tickets_rank_id"), "rank_queue_tickets", ["rank_id"], unique=False)
    op.create_index(op.f("ix_rank_queue_tickets_state"), "rank_queue_tickets", ["state"], unique=False)
    op.create_index(op.f("ix_rank_queue_tickets_trip_id"), "rank_queue_tickets", ["trip_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_rank_queue_tickets_trip_id"), table_name="rank_queue_tickets")
    op.drop_index(op.f("ix_rank_queue_tickets_state"), table_name="rank_queue_tickets")
    op.drop_index(op.f("ix_rank_queue_tickets_rank_id"), table_name="rank_queue_tickets")
    op.drop_table("rank_queue_tickets")

    op.drop_index(op.f("ix_policies_route_id"), table_name="policies")
    op.drop_index(op.f("ix_policies_organization_id"), table_name="policies")
    op.drop_table("policies")

    op.drop_index(op.f("ix_audit_logs_entity_type"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_entity_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_actor_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_action"), table_name="audit_logs")
    op.drop_table("audit_logs")
