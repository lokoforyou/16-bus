from fastapi.testclient import TestClient
from app.domain.auth.models import UserRole
from app.core.security import hash_password
from app.domain.organizations.models import OrganizationORM, OrganizationType

def get_admin_token(client: TestClient):
    from app.core.database import get_session_factory
    from app.domain.auth.models import UserORM
    
    session = get_session_factory()()
    try:
        org = OrganizationORM(id="org-1", name="Test Org", type=OrganizationType.TAXI_ASSOCIATION)
        session.add(org)
        user = UserORM(
            full_name="Admin",
            phone="27111111111",
            password_hash=hash_password("password123"),
            role=UserRole.ORG_ADMIN,
            organization_id="org-1"
        )
        session.add(user)
        session.commit()
    finally:
        session.close()
    
    response = client.post(
        "/api/v1/auth/login",
        json={"phone": "27111111111", "password": "password123"}
    )
    return response.json()["access_token"], "org-1"


def test_create_vehicle(client: TestClient):
    token, org_id = get_admin_token(client)
    
    response = client.post(
        "/api/v1/vehicles",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "organization_id": org_id,
            "plate_number": "JHB-001",
            "capacity": 16
        }
    )
    assert response.status_code == 200
    assert response.json()["plate_number"] == "JHB-001"


def test_start_shift(client: TestClient):
    from app.core.database import get_session_factory
    from app.domain.vehicles.models import VehicleORM
    from app.domain.drivers.models import DriverORM
    from app.domain.auth.models import UserORM
    
    token, org_id = get_admin_token(client)
    
    session = get_session_factory()()
    try:
        # Create a real driver user
        user = UserORM(full_name="D1", phone="27222222222", password_hash=hash_password("password123"), role=UserRole.DRIVER, organization_id=org_id)
        session.add(user)
        session.commit()
        
        driver = DriverORM(organization_id=org_id, user_id=user.id, full_name="D1", phone="27222222222", licence_number="L1")
        vehicle = VehicleORM(organization_id=org_id, plate_number="V1", capacity=16)
        session.add(driver)
        session.add(vehicle)
        session.commit()
        driver_id = driver.id
        vehicle_id = vehicle.id
    finally:
        session.close()
    
    # Login as Driver
    login_response = client.post(
        "/api/v1/auth/login",
        json={"phone": "27222222222", "password": "password123"}
    )
    driver_token = login_response.json()["access_token"]
    
    # Start Shift
    response = client.post(
        "/api/v1/driver/shifts/start",
        headers={"Authorization": f"Bearer {driver_token}"},
        json={"driver_id": driver_id, "vehicle_id": vehicle_id}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "active"


def test_driver_cannot_end_another_driver_shift(client: TestClient):
    from app.core.database import get_session_factory
    from app.domain.vehicles.models import VehicleORM
    from app.domain.drivers.models import DriverORM
    from app.domain.auth.models import UserORM

    token, org_id = get_admin_token(client)

    session = get_session_factory()()
    try:
        driver1_user = UserORM(full_name="D One", phone="27333333333", password_hash=hash_password("password123"), role=UserRole.DRIVER, organization_id=org_id)
        driver2_user = UserORM(full_name="D Two", phone="27444444444", password_hash=hash_password("password123"), role=UserRole.DRIVER, organization_id=org_id)
        session.add_all([driver1_user, driver2_user])
        session.commit()

        driver1 = DriverORM(organization_id=org_id, user_id=driver1_user.id, full_name="D One", phone="27333333333", licence_number="L11")
        driver2 = DriverORM(organization_id=org_id, user_id=driver2_user.id, full_name="D Two", phone="27444444444", licence_number="L22")
        vehicle = VehicleORM(organization_id=org_id, plate_number="V2", capacity=16)
        session.add_all([driver1, driver2, vehicle])
        session.commit()

        shift_response = client.post(
            "/api/v1/driver/shifts/start",
            headers={"Authorization": f"Bearer {_login_driver(client, '27333333333')}"},
            json={"driver_id": driver1.id, "vehicle_id": vehicle.id},
        )
        shift_id = shift_response.json()["id"]

        end_response = client.post(
            f"/api/v1/driver/shifts/{shift_id}/end",
            headers={"Authorization": f"Bearer {_login_driver(client, '27444444444')}"},
        )
        assert end_response.status_code == 403
    finally:
        session.close()


def _login_driver(client: TestClient, phone: str) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"phone": phone, "password": "password123"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]
