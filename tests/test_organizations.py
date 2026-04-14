from fastapi.testclient import TestClient
from app.domain.auth.models import UserRole
from app.core.security import hash_password


def get_auth_token(client: TestClient, role: UserRole, phone: str):
    from app.core.database import get_session_factory
    from app.domain.auth.models import UserORM
    
    session = get_session_factory()()
    try:
        user = UserORM(
            full_name=f"Admin {role}",
            phone=phone,
            password_hash=hash_password("password123"),
            role=role
        )
        session.add(user)
        session.commit()
    finally:
        session.close()
    
    response = client.post(
        "/api/v1/auth/login",
        json={"phone": phone, "password": "password123"}
    )
    return response.json()["access_token"]


def test_create_organization_super_admin(client: TestClient):
    token = get_auth_token(client, UserRole.SUPER_ADMIN, "27777777777")
    
    response = client.post(
        "/api/v1/organizations",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "New Association",
            "type": "taxi_association"
        }
    )
    assert response.status_code == 200
    assert response.json()["name"] == "New Association"


def test_create_organization_forbidden(client: TestClient):
    token = get_auth_token(client, UserRole.PASSENGER, "27666666666")
    
    response = client.post(
        "/api/v1/organizations",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Forbidden Association",
            "type": "taxi_association"
        }
    )
    assert response.status_code == 403
    assert response.json()["code"] == "PERMISSION_DENIED"


def test_list_organizations(client: TestClient):
    response = client.get("/api/v1/organizations")
    assert response.status_code == 200
    assert "items" in response.json()
