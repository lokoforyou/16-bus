"""initial schema

Revision ID: 20260413_2148_0001
Revises:
Create Date: 2026-04-13 21:48:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260413_2148_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "routes",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("organization_id", sa.String(length=64), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("direction", sa.String(length=32), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index(op.f("ix_routes_organization_id"), "routes", ["organization_id"])

    op.create_table(
        "stops",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("lat", sa.Float(), nullable=False),
        sa.Column("lon", sa.Float(), nullable=False),
        sa.Column("cash_allowed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "route_variants",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("route_id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.ForeignKeyConstraint(["route_id"], ["routes.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_route_variants_route_id"), "route_variants", ["route_id"])

    op.create_table(
        "route_stops",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("route_variant_id", sa.String(length=64), nullable=False),
        sa.Column("stop_id", sa.String(length=64), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("dwell_time_seconds", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["route_variant_id"], ["route_variants.id"]),
        sa.ForeignKeyConstraint(["stop_id"], ["stops.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_route_stops_route_variant_id"),
        "route_stops",
        ["route_variant_id"],
    )
    op.create_index(op.f("ix_route_stops_stop_id"), "route_stops", ["stop_id"])

    op.create_table(
        "trips",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("route_id", sa.String(length=64), nullable=False),
        sa.Column("route_variant_id", sa.String(length=64), nullable=False),
        sa.Column("organization_id", sa.String(length=64), nullable=False),
        sa.Column("vehicle_id", sa.String(length=64), nullable=False),
        sa.Column("driver_id", sa.String(length=64), nullable=False),
        sa.Column("trip_type", sa.String(length=32), nullable=False),
        sa.Column("planned_start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("state", sa.String(length=32), nullable=False),
        sa.Column("seats_total", sa.Integer(), nullable=False),
        sa.Column("seats_free", sa.Integer(), nullable=False),
        sa.Column("current_stop_id", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["current_stop_id"], ["stops.id"]),
        sa.ForeignKeyConstraint(["route_id"], ["routes.id"]),
        sa.ForeignKeyConstraint(["route_variant_id"], ["route_variants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_trips_organization_id"), "trips", ["organization_id"])
    op.create_index(op.f("ix_trips_route_id"), "trips", ["route_id"])
    op.create_index(op.f("ix_trips_route_variant_id"), "trips", ["route_variant_id"])
    op.create_index(op.f("ix_trips_state"), "trips", ["state"])

    op.create_table(
        "bookings",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("trip_id", sa.String(length=64), nullable=False),
        sa.Column("passenger_id", sa.String(length=64), nullable=False),
        sa.Column("origin_stop_id", sa.String(length=64), nullable=False),
        sa.Column("destination_stop_id", sa.String(length=64), nullable=False),
        sa.Column("party_size", sa.Integer(), nullable=False),
        sa.Column("fare_amount", sa.Float(), nullable=False),
        sa.Column("hold_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payment_status", sa.String(length=32), nullable=False),
        sa.Column("booking_state", sa.String(length=32), nullable=False),
        sa.Column("forfeiture_fee_amount", sa.Float(), nullable=False, server_default="0"),
        sa.Column("booking_channel", sa.String(length=32), nullable=False),
        sa.Column("qr_token_id", sa.String(length=64), nullable=True),
        sa.ForeignKeyConstraint(["destination_stop_id"], ["stops.id"]),
        sa.ForeignKeyConstraint(["origin_stop_id"], ["stops.id"]),
        sa.ForeignKeyConstraint(["trip_id"], ["trips.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_bookings_booking_state"), "bookings", ["booking_state"])
    op.create_index(op.f("ix_bookings_passenger_id"), "bookings", ["passenger_id"])
    op.create_index(op.f("ix_bookings_trip_id"), "bookings", ["trip_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_bookings_trip_id"), table_name="bookings")
    op.drop_index(op.f("ix_bookings_passenger_id"), table_name="bookings")
    op.drop_index(op.f("ix_bookings_booking_state"), table_name="bookings")
    op.drop_table("bookings")

    op.drop_index(op.f("ix_trips_state"), table_name="trips")
    op.drop_index(op.f("ix_trips_route_variant_id"), table_name="trips")
    op.drop_index(op.f("ix_trips_route_id"), table_name="trips")
    op.drop_index(op.f("ix_trips_organization_id"), table_name="trips")
    op.drop_table("trips")

    op.drop_index(op.f("ix_route_stops_stop_id"), table_name="route_stops")
    op.drop_index(op.f("ix_route_stops_route_variant_id"), table_name="route_stops")
    op.drop_table("route_stops")

    op.drop_index(op.f("ix_route_variants_route_id"), table_name="route_variants")
    op.drop_table("route_variants")

    op.drop_table("stops")

    op.drop_index(op.f("ix_routes_organization_id"), table_name="routes")
    op.drop_table("routes")
