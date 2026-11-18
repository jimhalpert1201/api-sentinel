import pytest
from app.core.rate_limiter import auth_rate_limiter
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def reset_rate_limiter_fixture():
    auth_rate_limiter.reset()
    yield
    auth_rate_limiter.reset()


def register_and_login(client: TestClient, email: str, username: str, password: str) -> str:
    """Helper to register and login a user, returning access token."""
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "username": username, "password": password},
    )
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    return login_res.json()["access_token"]


def test_get_current_user_profile(client: TestClient):
    """Verify GET /api/v1/users/me returns authenticated user profile."""
    token = register_and_login(client, "me@example.com", "meuser", "Password123!")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "me@example.com"
    assert data["username"] == "meuser"
    assert "hashed_password" not in data


def test_get_profile_unauthorized(client: TestClient):
    """Verify GET /api/v1/users/me requires authorization."""
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401


def test_update_user_profile(client: TestClient):
    """Verify PATCH /api/v1/users/me updates profile fields."""
    token = register_and_login(client, "patch@example.com", "patchuser", "Password123!")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.patch(
        "/api/v1/users/me",
        headers=headers,
        json={"username": "updated_patchuser"},
    )
    assert response.status_code == 200
    assert response.json()["username"] == "updated_patchuser"


def test_update_user_duplicate_email(client: TestClient):
    """Verify PATCH /api/v1/users/me rejects duplicate email with 409."""
    register_and_login(client, "first@example.com", "firstuser", "Password123!")
    token2 = register_and_login(client, "second@example.com", "seconduser", "Password123!")

    headers2 = {"Authorization": f"Bearer {token2}"}
    response = client.patch(
        "/api/v1/users/me",
        headers=headers2,
        json={"email": "first@example.com"},
    )
    assert response.status_code == 409
    assert "Email already in use" in response.json()["detail"]


def test_change_password_success(client: TestClient):
    """Verify POST /api/v1/users/me/password changes password."""
    token = register_and_login(client, "pwchange@example.com", "pwuser", "OldPassword123!")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        "/api/v1/users/me/password",
        headers=headers,
        json={
            "current_password": "OldPassword123!",
            "new_password": "BrandNewPassword456@",
        },
    )
    assert response.status_code == 204

    # Old password fails
    login_old = client.post(
        "/api/v1/auth/login",
        json={"email": "pwchange@example.com", "password": "OldPassword123!"},
    )
    assert login_old.status_code == 401

    # New password succeeds
    login_new = client.post(
        "/api/v1/auth/login",
        json={"email": "pwchange@example.com", "password": "BrandNewPassword456@"},
    )
    assert login_new.status_code == 200


def test_change_password_wrong_current(client: TestClient):
    """Verify POST /api/v1/users/me/password fails with 400 when current password wrong."""
    token = register_and_login(client, "wrongcurrent@example.com", "wcuser", "CorrectPassword123!")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        "/api/v1/users/me/password",
        headers=headers,
        json={
            "current_password": "IncorrectPassword999!",
            "new_password": "BrandNewPassword456@",
        },
    )
    assert response.status_code == 400
    assert "Incorrect current password" in response.json()["detail"]
