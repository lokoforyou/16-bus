"""harden trip and telemetry foreign keys

Revision ID: 20260414_1200_0006
Revises: 20260414_0105_0005
Create Date: 2026-04-14 12:00:00
"""

from collections.abc import Sequence

from alembic import op


revision: str = "20260414_1200_0006"
down_revision: str | None = "20260414_0105_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO organizations (id, name, type, compliance_status, is_active)
        SELECT DISTINCT t.organization_id, t.organization_id, 'taxi_association', 'verified', 1
        FROM trips t
        WHERE t.organization_id IS NOT NULL
          AND NOT EXISTS (SELECT 1 FROM organizations o WHERE o.id = t.organization_id)
        """
    )

    op.execute(
        """
        INSERT INTO users (id, full_name, phone, password_hash, role, organization_id, is_active)
        SELECT DISTINCT
            'user-auto-' || t.driver_id,
            'Auto Driver ' || t.driver_id,
            'auto-' || t.driver_id,
            'seeded-password',
            'driver',
            t.organization_id,
            1
        FROM trips t
        WHERE t.driver_id IS NOT NULL
          AND NOT EXISTS (SELECT 1 FROM drivers d WHERE d.id = t.driver_id)
          AND NOT EXISTS (SELECT 1 FROM users u WHERE u.id = 'user-auto-' || t.driver_id)
        """
    )

    op.execute(
        """
        INSERT INTO vehicles (id, organization_id, plate_number, capacity, permit_number, compliance_status, is_active)
        SELECT DISTINCT
            t.vehicle_id,
            t.organization_id,
            'AUTO-' || t.vehicle_id,
            16,
            NULL,
            'verified',
            1
        FROM trips t
        WHERE t.vehicle_id IS NOT NULL
          AND NOT EXISTS (SELECT 1 FROM vehicles v WHERE v.id = t.vehicle_id)
        """
    )

    op.execute(
        """
        INSERT INTO drivers (id, organization_id, user_id, full_name, phone, licence_number, pdp_verified, is_active)
        SELECT DISTINCT
            t.driver_id,
            t.organization_id,
            'user-auto-' || t.driver_id,
            'Auto Driver ' || t.driver_id,
            'auto-driver-' || t.driver_id,
            'AUTO-' || t.driver_id,
            1,
            1
        FROM trips t
        WHERE t.driver_id IS NOT NULL
          AND NOT EXISTS (SELECT 1 FROM drivers d WHERE d.id = t.driver_id)
        """
    )

    with op.batch_alter_table("trips") as batch_op:
        batch_op.create_foreign_key("fk_trips_vehicle_id", "vehicles", ["vehicle_id"], ["id"])
        batch_op.create_foreign_key("fk_trips_driver_id", "drivers", ["driver_id"], ["id"])

    with op.batch_alter_table("vehicle_locations") as batch_op:
        batch_op.create_foreign_key("fk_vehicle_locations_vehicle_id", "vehicles", ["vehicle_id"], ["id"])


def downgrade() -> None:
    with op.batch_alter_table("vehicle_locations") as batch_op:
        batch_op.drop_constraint("fk_vehicle_locations_vehicle_id", type_="foreignkey")

    with op.batch_alter_table("trips") as batch_op:
        batch_op.drop_constraint("fk_trips_driver_id", type_="foreignkey")
        batch_op.drop_constraint("fk_trips_vehicle_id", type_="foreignkey")
