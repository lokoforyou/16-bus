from fastapi.testclient import TestClient
from app.domain.auth.models import UserRole
from app.core.security import hash_password


def test_login_success(client: TestClient):
    from app.core.database import get_session_factory
    from app.domain.auth.models import UserORM
    
    session = get_session_factory()()
    try:
        user = UserORM(
            full_name="Test User",
            phone="27999999999",
            password_hash=hash_password("password123"),
            role=UserRole.PASSENGER
        )
        session.add(user)
        session.commit()
    finally:
        session.close()
    
    response = client.post(
        "/api/v1/auth/login",
        json={"phone": "27999999999", "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_failure(client: TestClient):
    response = client.post(
        "/api/v1/auth/login",
        json={"phone": "27999999999", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert response.json()["code"] == "AUTHENTICATION_ERROR"


def test_get_me(client: TestClient):
    from app.core.database import get_session_factory
    from app.domain.auth.models import UserORM
    
    session = get_session_factory()()
    try:
        user = UserORM(
            full_name="Me User",
            phone="27888888888",
            password_hash=hash_password("password123"),
            role=UserRole.PASSENGER
        )
        session.add(user)
        session.commit()
    finally:
        session.close()
    
    login_response = client.post(
        "/api/v1/auth/login",
        json={"phone": "27888888888", "password": "password123"}
    )
    token = login_response.json()["access_token"]
    
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Me User"
    assert data["phone"] == "27888888888"
