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
        SELECT 'org-16-bus', '16 Bus Taxi Association', 'taxi_association', 'verified', 1
        WHERE NOT EXISTS (SELECT 1 FROM organizations WHERE id = 'org-16-bus')
        """
    )
    op.execute(
        """
        INSERT INTO users (id, full_name, phone, password_hash, role, organization_id, is_active)
        SELECT 'user-driver-001', 'Driver 001', '27000001001', 'seeded-password', 'driver', 'org-16-bus', 1
        WHERE NOT EXISTS (SELECT 1 FROM users WHERE id = 'user-driver-001')
        """
    )
    op.execute(
        """
        INSERT INTO users (id, full_name, phone, password_hash, role, organization_id, is_active)
        SELECT 'user-driver-002', 'Driver 002', '27000001002', 'seeded-password', 'driver', 'org-16-bus', 1
        WHERE NOT EXISTS (SELECT 1 FROM users WHERE id = 'user-driver-002')
        """
    )
    op.execute(
        """
        INSERT INTO vehicles (id, organization_id, plate_number, capacity, permit_number, compliance_status, is_active)
        SELECT 'vehicle-001', 'org-16-bus', 'SEED-001', 16, NULL, 'verified', 1
        WHERE NOT EXISTS (SELECT 1 FROM vehicles WHERE id = 'vehicle-001')
        """
    )
    op.execute(
        """
        INSERT INTO vehicles (id, organization_id, plate_number, capacity, permit_number, compliance_status, is_active)
        SELECT 'vehicle-002', 'org-16-bus', 'SEED-002', 16, NULL, 'verified', 1
        WHERE NOT EXISTS (SELECT 1 FROM vehicles WHERE id = 'vehicle-002')
        """
    )
    op.execute(
        """
        INSERT INTO drivers (id, organization_id, user_id, full_name, phone, licence_number, pdp_verified, is_active)
        SELECT 'driver-001', 'org-16-bus', 'user-driver-001', 'Driver 001', '27111111001', 'LIC-001', 1, 1
        WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE id = 'driver-001')
        """
    )
    op.execute(
        """
        INSERT INTO drivers (id, organization_id, user_id, full_name, phone, licence_number, pdp_verified, is_active)
        SELECT 'driver-002', 'org-16-bus', 'user-driver-002', 'Driver 002', '27111111002', 'LIC-002', 1, 1
        WHERE NOT EXISTS (SELECT 1 FROM drivers WHERE id = 'driver-002')
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
