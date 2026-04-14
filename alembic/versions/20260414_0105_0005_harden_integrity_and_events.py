"""harden integrity and add domain events

Revision ID: 20260414_0105_0005
Revises: 1273ba2cc8fb
Create Date: 2026-04-14 01:05:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260414_0105_0005"
down_revision: str | None = "1273ba2cc8fb"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "domain_events",
        sa.Column("id", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("emitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_domain_events_name"), "domain_events", ["name"], unique=False)

    with op.batch_alter_table("route_stops") as batch_op:
        batch_op.create_unique_constraint(
            "uq_route_stops_variant_sequence", ["route_variant_id", "sequence_number"]
        )
        batch_op.create_unique_constraint(
            "uq_route_stops_variant_stop", ["route_variant_id", "stop_id"]
        )

    with op.batch_alter_table("users") as batch_op:
        batch_op.create_foreign_key("fk_users_organization_id", "organizations", ["organization_id"], ["id"])

    with op.batch_alter_table("drivers") as batch_op:
        batch_op.create_foreign_key("fk_drivers_organization_id", "organizations", ["organization_id"], ["id"])
        batch_op.create_foreign_key("fk_drivers_user_id", "users", ["user_id"], ["id"])

    with op.batch_alter_table("vehicles") as batch_op:
        batch_op.create_foreign_key("fk_vehicles_organization_id", "organizations", ["organization_id"], ["id"])

    with op.batch_alter_table("driver_shifts") as batch_op:
        batch_op.create_foreign_key("fk_driver_shifts_driver_id", "drivers", ["driver_id"], ["id"])
        batch_op.create_foreign_key("fk_driver_shifts_vehicle_id", "vehicles", ["vehicle_id"], ["id"])
        batch_op.create_foreign_key("fk_driver_shifts_organization_id", "organizations", ["organization_id"], ["id"])

    with op.batch_alter_table("routes") as batch_op:
        batch_op.create_foreign_key("fk_routes_organization_id", "organizations", ["organization_id"], ["id"])

    with op.batch_alter_table("trips") as batch_op:
        batch_op.create_foreign_key("fk_trips_organization_id", "organizations", ["organization_id"], ["id"])


def downgrade() -> None:

    with op.batch_alter_table("trips") as batch_op:
        batch_op.drop_constraint("fk_trips_organization_id", type_="foreignkey")

    with op.batch_alter_table("routes") as batch_op:
        batch_op.drop_constraint("fk_routes_organization_id", type_="foreignkey")

    with op.batch_alter_table("driver_shifts") as batch_op:
        batch_op.drop_constraint("fk_driver_shifts_organization_id", type_="foreignkey")
        batch_op.drop_constraint("fk_driver_shifts_vehicle_id", type_="foreignkey")
        batch_op.drop_constraint("fk_driver_shifts_driver_id", type_="foreignkey")

    with op.batch_alter_table("vehicles") as batch_op:
        batch_op.drop_constraint("fk_vehicles_organization_id", type_="foreignkey")

    with op.batch_alter_table("drivers") as batch_op:
        batch_op.drop_constraint("fk_drivers_user_id", type_="foreignkey")
        batch_op.drop_constraint("fk_drivers_organization_id", type_="foreignkey")

    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_constraint("fk_users_organization_id", type_="foreignkey")

    with op.batch_alter_table("route_stops") as batch_op:
        batch_op.drop_constraint("uq_route_stops_variant_stop", type_="unique")
        batch_op.drop_constraint("uq_route_stops_variant_sequence", type_="unique")

    op.drop_index(op.f("ix_domain_events_name"), table_name="domain_events")
    op.drop_table("domain_events")
