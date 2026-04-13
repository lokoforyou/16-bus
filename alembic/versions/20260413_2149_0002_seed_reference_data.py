"""seed reference data

Revision ID: 20260413_2149_0002
Revises: 20260413_2148_0001
Create Date: 2026-04-13 21:49:00
"""

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta

from alembic import op
import sqlalchemy as sa


revision: str = "20260413_2149_0002"
down_revision: str | None = "20260413_2148_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


routes_table = sa.table(
    "routes",
    sa.column("id", sa.String),
    sa.column("organization_id", sa.String),
    sa.column("code", sa.String),
    sa.column("name", sa.String),
    sa.column("direction", sa.String),
    sa.column("active", sa.Boolean),
)

stops_table = sa.table(
    "stops",
    sa.column("id", sa.String),
    sa.column("name", sa.String),
    sa.column("type", sa.String),
    sa.column("lat", sa.Float),
    sa.column("lon", sa.Float),
    sa.column("cash_allowed", sa.Boolean),
    sa.column("active", sa.Boolean),
)

variants_table = sa.table(
    "route_variants",
    sa.column("id", sa.String),
    sa.column("route_id", sa.String),
    sa.column("name", sa.String),
    sa.column("active", sa.Boolean),
)

route_stops_table = sa.table(
    "route_stops",
    sa.column("id", sa.String),
    sa.column("route_variant_id", sa.String),
    sa.column("stop_id", sa.String),
    sa.column("sequence_number", sa.Integer),
    sa.column("dwell_time_seconds", sa.Integer),
)

trips_table = sa.table(
    "trips",
    sa.column("id", sa.String),
    sa.column("route_id", sa.String),
    sa.column("route_variant_id", sa.String),
    sa.column("organization_id", sa.String),
    sa.column("vehicle_id", sa.String),
    sa.column("driver_id", sa.String),
    sa.column("trip_type", sa.String),
    sa.column("planned_start_time", sa.DateTime(timezone=True)),
    sa.column("state", sa.String),
    sa.column("seats_total", sa.Integer),
    sa.column("seats_free", sa.Integer),
    sa.column("current_stop_id", sa.String),
)


def upgrade() -> None:
    now = datetime.now(UTC)
    op.bulk_insert(
        routes_table,
        [
            {
                "id": "route-16-soweto-jhb",
                "organization_id": "org-16-bus",
                "code": "16B-JHB",
                "name": "Soweto to Johannesburg CBD",
                "direction": "inbound",
                "active": True,
            }
        ],
    )
    op.bulk_insert(
        variants_table,
        [
            {
                "id": "variant-16-soweto-jhb-main",
                "route_id": "route-16-soweto-jhb",
                "name": "Main Corridor",
                "active": True,
            }
        ],
    )
    op.bulk_insert(
        stops_table,
        [
            {
                "id": "stop-bara-rank",
                "name": "Bara Rank",
                "type": "rank",
                "lat": -26.2594,
                "lon": 27.9426,
                "cash_allowed": True,
                "active": True,
            },
            {
                "id": "stop-diepkloof",
                "name": "Diepkloof Interchange",
                "type": "stop",
                "lat": -26.2452,
                "lon": 27.9380,
                "cash_allowed": False,
                "active": True,
            },
            {
                "id": "stop-town",
                "name": "Johannesburg CBD",
                "type": "rank",
                "lat": -26.2041,
                "lon": 28.0473,
                "cash_allowed": True,
                "active": True,
            },
        ],
    )
    op.bulk_insert(
        route_stops_table,
        [
            {
                "id": "rs-1",
                "route_variant_id": "variant-16-soweto-jhb-main",
                "stop_id": "stop-bara-rank",
                "sequence_number": 1,
                "dwell_time_seconds": 180,
            },
            {
                "id": "rs-2",
                "route_variant_id": "variant-16-soweto-jhb-main",
                "stop_id": "stop-diepkloof",
                "sequence_number": 2,
                "dwell_time_seconds": 120,
            },
            {
                "id": "rs-3",
                "route_variant_id": "variant-16-soweto-jhb-main",
                "stop_id": "stop-town",
                "sequence_number": 3,
                "dwell_time_seconds": 240,
            },
        ],
    )
    op.bulk_insert(
        trips_table,
        [
            {
                "id": "trip-001",
                "route_id": "route-16-soweto-jhb",
                "route_variant_id": "variant-16-soweto-jhb-main",
                "organization_id": "org-16-bus",
                "vehicle_id": "vehicle-001",
                "driver_id": "driver-001",
                "trip_type": "rolling",
                "planned_start_time": now + timedelta(minutes=8),
                "state": "boarding",
                "seats_total": 16,
                "seats_free": 10,
                "current_stop_id": "stop-bara-rank",
            },
            {
                "id": "trip-002",
                "route_id": "route-16-soweto-jhb",
                "route_variant_id": "variant-16-soweto-jhb-main",
                "organization_id": "org-16-bus",
                "vehicle_id": "vehicle-002",
                "driver_id": "driver-002",
                "trip_type": "rolling",
                "planned_start_time": now + timedelta(minutes=18),
                "state": "planned",
                "seats_total": 16,
                "seats_free": 14,
                "current_stop_id": "stop-bara-rank",
            },
        ],
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            "DELETE FROM trips WHERE id IN ('trip-001', 'trip-002')"
        )
    )
    op.execute(
        sa.text(
            "DELETE FROM route_stops WHERE id IN ('rs-1', 'rs-2', 'rs-3')"
        )
    )
    op.execute(
        sa.text(
            "DELETE FROM route_variants WHERE id = 'variant-16-soweto-jhb-main'"
        )
    )
    op.execute(
        sa.text(
            "DELETE FROM stops WHERE id IN ('stop-bara-rank', 'stop-diepkloof', 'stop-town')"
        )
    )
    op.execute(sa.text("DELETE FROM routes WHERE id = 'route-16-soweto-jhb'"))
