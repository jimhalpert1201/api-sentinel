import pytest
from app.core.rate_limiter import auth_rate_limiter
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def reset_limiter_fixture():
    auth_rate_limiter.reset()
    yield
    auth_rate_limiter.reset()


def test_register_user_success(client: TestClient):
    """Verify POST /api/v1/auth/register registers new user and returns 201."""
    payload = {
        "email": "newuser@example.com",
        "username": "newuser",
        "password": "Password123!",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["username"] == "newuser"
    assert "id" in data
    assert "hashed_password" not in data


def test_register_duplicate_email(client: TestClient):
    """Verify POST /api/v1/auth/register rejects duplicate email with 409."""
    payload = {
        "email": "duplicate@example.com",
        "username": "user1",
        "password": "Password123!",
    }
    res1 = client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    payload2 = {
        "email": "duplicate@example.com",
        "username": "user2",
        "password": "Password123!",
    }
    res2 = client.post("/api/v1/auth/register", json=payload2)
    assert res2.status_code == 409
    assert "Email already registered" in res2.json()["detail"]


def test_register_duplicate_username(client: TestClient):
    """Verify POST /api/v1/auth/register rejects duplicate username with 409."""
    payload = {
        "email": "u1@example.com",
        "username": "sameuser",
        "password": "Password123!",
    }
    res1 = client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    payload2 = {
        "email": "u2@example.com",
        "username": "sameuser",
        "password": "Password123!",
    }
    res2 = client.post("/api/v1/auth/register", json=payload2)
    assert res2.status_code == 409
    assert "Username already taken" in res2.json()["detail"]


def test_login_json_success(client: TestClient):
    """Verify POST /api/v1/auth/login works with JSON payload."""
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "loginuser@example.com",
            "username": "loginuser",
            "password": "Password123!",
        },
    )

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "loginuser@example.com", "password": "Password123!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_oauth2_form_success(client: TestClient):
    """Verify POST /api/v1/auth/login works with OAuth2 form-data."""
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "formuser@example.com",
            "username": "formuser",
            "password": "Password123!",
        },
    )

    response = client.post(
        "/api/v1/auth/login",
        data={"username": "formuser@example.com", "password": "Password123!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_login_invalid_password(client: TestClient):
    """Verify POST /api/v1/auth/login rejects wrong password with 401."""
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "wrongpw@example.com",
            "username": "wrongpw",
            "password": "Password123!",
        },
    )

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "wrongpw@example.com", "password": "WrongPassword123!"},
    )
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


def test_refresh_token_rotation_success(client: TestClient):
    """Verify POST /api/v1/auth/refresh rotates tokens."""
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "refresher@example.com",
            "username": "refresher",
            "password": "Password123!",
        },
    )
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "refresher@example.com", "password": "Password123!"},
    )
    old_refresh_token = login_res.json()["refresh_token"]

    refresh_res = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": old_refresh_token},
    )
    assert refresh_res.status_code == 200
    new_data = refresh_res.json()
    assert "access_token" in new_data
    assert "refresh_token" in new_data
    assert new_data["refresh_token"] != old_refresh_token


def test_refresh_token_reuse_detected_and_revoked(client: TestClient):
    """Verify using an already rotated refresh token fails with 401 and revokes session."""
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "reuse@example.com",
            "username": "reuse",
            "password": "Password123!",
        },
    )
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "reuse@example.com", "password": "Password123!"},
    )
    original_refresh_token = login_res.json()["refresh_token"]

    # First refresh succeeds
    res1 = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": original_refresh_token},
    )
    assert res1.status_code == 200

    # Second refresh using old token must be rejected as reuse
    res2 = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": original_refresh_token},
    )
    assert res2.status_code == 401


def test_logout_revokes_token(client: TestClient):
    """Verify POST /api/v1/auth/logout revokes the refresh token."""
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "logout@example.com",
            "username": "logoutuser",
            "password": "Password123!",
        },
    )
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "logout@example.com", "password": "Password123!"},
    )
    refresh_token = login_res.json()["refresh_token"]

    logout_res = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh_token},
    )
    assert logout_res.status_code == 204

    # Using the logged-out refresh token should now fail
    ref_res = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert ref_res.status_code == 401


def test_auth_rate_limiting(client: TestClient):
    """Verify repeated failed attempts trigger 429."""
    auth_rate_limiter.reset()

    # Threshold is 5 attempts per 60s
    for _ in range(5):
        client.post(
            "/api/v1/auth/login",
            json={"email": "nonexistent@example.com", "password": "WrongPassword1!"},
        )

    # 6th attempt should be rate limited
    throttled_res = client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent@example.com", "password": "WrongPassword1!"},
    )
    assert throttled_res.status_code == 429
    assert "Too many requests" in throttled_res.json()["detail"]
    auth_rate_limiter.reset()
