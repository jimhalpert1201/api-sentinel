import uuid

import pytest
from app.auth.dependencies import get_current_user
from app.main import app
from app.models.user import User
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


@pytest.fixture
def test_user(db_session: Session) -> User:
    """Fixture providing a primary test user."""
    user = User(
        email="tester@example.com",
        username="tester",
        hashed_password="hashed_pw_test",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def other_user(db_session: Session) -> User:
    """Fixture providing a second user for ownership isolation tests."""
    user = User(
        email="other@example.com",
        username="otheruser",
        hashed_password="hashed_pw_other",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_client(client: TestClient, test_user: User) -> TestClient:
    """TestClient authenticated as test_user."""
    app.dependency_overrides[get_current_user] = lambda: test_user
    return client


def test_create_monitor(auth_client: TestClient):
    """Verify POST /api/v1/monitors creates a monitor."""
    payload = {
        "name": "Auth Service Health",
        "url": "https://auth.example.com/healthz",
        "http_method": "GET",
        "interval_seconds": 30,
        "timeout_seconds": 10,
        "expected_status_code": 200,
        "headers": {"X-Custom": "Test"},
    }
    response = auth_client.post("/api/v1/monitors", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == payload["name"]
    assert data["url"] == payload["url"]
    assert data["interval_seconds"] == 30
    assert "id" in data
    assert "user_id" in data


def test_create_monitor_validation_errors(auth_client: TestClient):
    """Verify POST /api/v1/monitors validates input fields."""
    # Invalid URL
    res = auth_client.post(
        "/api/v1/monitors",
        json={"name": "Bad URL", "url": "ftp://bad.com"},
    )
    assert res.status_code == 422

    # Negative interval
    res = auth_client.post(
        "/api/v1/monitors",
        json={"name": "Bad Interval", "url": "https://example.com", "interval_seconds": -5},
    )
    assert res.status_code == 422


def test_list_monitors(auth_client: TestClient):
    """Verify GET /api/v1/monitors returns all monitors for current user."""
    # Create two monitors
    auth_client.post(
        "/api/v1/monitors",
        json={"name": "Monitor 1", "url": "https://m1.example.com"},
    )
    auth_client.post(
        "/api/v1/monitors",
        json={"name": "Monitor 2", "url": "https://m2.example.com"},
    )

    response = auth_client.get("/api/v1/monitors")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    names = [m["name"] for m in data]
    assert "Monitor 1" in names
    assert "Monitor 2" in names


def test_get_monitor_by_id(auth_client: TestClient):
    """Verify GET /api/v1/monitors/{id} returns monitor details."""
    created = auth_client.post(
        "/api/v1/monitors",
        json={"name": "Single Monitor", "url": "https://single.example.com"},
    ).json()

    monitor_id = created["id"]
    response = auth_client.get(f"/api/v1/monitors/{monitor_id}")
    assert response.status_code == 200
    assert response.json()["id"] == monitor_id


def test_get_monitor_not_found(auth_client: TestClient):
    """Verify GET /api/v1/monitors/{id} returns 404 for unknown ID."""
    random_id = str(uuid.uuid4())
    response = auth_client.get(f"/api/v1/monitors/{random_id}")
    assert response.status_code == 404


def test_get_current_user_dependency(db_session: Session):
    """Verify get_current_user resolves active user from valid JWT."""
    from app.auth.jwt import create_access_token

    user = User(
        email="dep_test@example.com",
        username="deptest",
        hashed_password="hashed_pw",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token(user.id)
    resolved = get_current_user(token=token, db=db_session)
    assert resolved.id == user.id
    assert resolved.email == "dep_test@example.com"


def test_update_monitor(auth_client: TestClient):
    """Verify PATCH /api/v1/monitors/{id} partially updates a monitor."""
    created = auth_client.post(
        "/api/v1/monitors",
        json={
            "name": "Initial Name",
            "url": "https://init.example.com/api",
            "interval_seconds": 60,
        },
    ).json()
    monitor_id = created["id"]

    patch_res = auth_client.patch(
        f"/api/v1/monitors/{monitor_id}",
        json={
            "name": "Updated Name",
            "url": "https://updated.example.com/api",
            "interval_seconds": 120,
        },
    )
    assert patch_res.status_code == 200
    updated = patch_res.json()
    assert updated["name"] == "Updated Name"
    assert updated["interval_seconds"] == 120
    assert updated["url"] == "https://updated.example.com/api"


def test_update_monitor_null_fields_rejected(auth_client: TestClient):
    """Verify PATCH /api/v1/monitors/{id} rejects explicit null for non-nullable fields."""
    created = auth_client.post(
        "/api/v1/monitors",
        json={"name": "Valid Name", "url": "https://valid.example.com/api"},
    ).json()
    monitor_id = created["id"]

    # Reject null name
    res1 = auth_client.patch(f"/api/v1/monitors/{monitor_id}", json={"name": None})
    assert res1.status_code in (400, 422)
    assert res1.status_code != 500

    # Reject null url
    res2 = auth_client.patch(f"/api/v1/monitors/{monitor_id}", json={"url": None})
    assert res2.status_code in (400, 422)
    assert res2.status_code != 500


def test_update_monitor_not_found(auth_client: TestClient):
    """Verify PATCH /api/v1/monitors/{id} returns 404 for unknown ID."""
    random_id = str(uuid.uuid4())
    response = auth_client.patch(f"/api/v1/monitors/{random_id}", json={"name": "New"})
    assert response.status_code == 404


def test_delete_monitor(auth_client: TestClient):
    """Verify DELETE /api/v1/monitors/{id} deletes the monitor."""
    created = auth_client.post(
        "/api/v1/monitors",
        json={"name": "To Delete", "url": "https://delete.example.com"},
    ).json()
    monitor_id = created["id"]

    del_res = auth_client.delete(f"/api/v1/monitors/{monitor_id}")
    assert del_res.status_code == 204

    # Verify 404 after deletion
    get_res = auth_client.get(f"/api/v1/monitors/{monitor_id}")
    assert get_res.status_code == 404


def test_delete_monitor_not_found(auth_client: TestClient):
    """Verify DELETE /api/v1/monitors/{id} returns 404 for unknown ID."""
    random_id = str(uuid.uuid4())
    response = auth_client.delete(f"/api/v1/monitors/{random_id}")
    assert response.status_code == 404


def test_monitors_unauthenticated_rejected(client: TestClient):
    """Verify accessing /api/v1/monitors without Bearer token returns 401."""
    response = client.get("/api/v1/monitors")
    assert response.status_code == 401


def test_monitor_user_isolation(auth_client: TestClient, other_user: User):
    """Verify a user cannot access or modify another user's monitor."""
    # test_user creates a monitor
    created = auth_client.post(
        "/api/v1/monitors",
        json={"name": "User 1 Monitor", "url": "https://u1.example.com"},
    ).json()
    monitor_id = created["id"]

    # Switch current user to other_user
    app.dependency_overrides[get_current_user] = lambda: other_user

    # other_user lists monitors (should be empty)
    list_res = auth_client.get("/api/v1/monitors")
    assert list_res.status_code == 200
    assert len(list_res.json()) == 0

    # other_user tries to get test_user's monitor
    get_res = auth_client.get(f"/api/v1/monitors/{monitor_id}")
    assert get_res.status_code == 404

    # other_user tries to patch test_user's monitor
    patch_res = auth_client.patch(f"/api/v1/monitors/{monitor_id}", json={"name": "Hacked"})
    assert patch_res.status_code == 404

    # other_user tries to delete test_user's monitor
    del_res = auth_client.delete(f"/api/v1/monitors/{monitor_id}")
    assert del_res.status_code == 404


def test_create_and_update_monitor_with_webhook_url(auth_client: TestClient):
    """Verify creating and updating a monitor with a valid webhook_url."""
    webhook = "https://hooks.example.com/alerts"
    payload = {
        "name": "Webhook Monitored API",
        "url": "https://api.example.com/health",
        "webhook_url": webhook,
    }
    create_res = auth_client.post("/api/v1/monitors", json=payload)
    assert create_res.status_code == 201
    created_data = create_res.json()
    assert created_data["webhook_url"] == webhook
    monitor_id = created_data["id"]

    # Verify GET retrieves the webhook_url
    get_res = auth_client.get(f"/api/v1/monitors/{monitor_id}")
    assert get_res.status_code == 200
    assert get_res.json()["webhook_url"] == webhook

    # Verify PATCH updates the webhook_url
    new_webhook = "https://hooks.example.com/new-alerts"
    patch_res = auth_client.patch(
        f"/api/v1/monitors/{monitor_id}", json={"webhook_url": new_webhook}
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["webhook_url"] == new_webhook


def test_create_monitor_invalid_webhook_url_rejected(auth_client: TestClient):
    """Verify invalid webhook_url returns 422 validation error."""
    payload = {
        "name": "Bad Webhook API",
        "url": "https://api.example.com/health",
        "webhook_url": "ftp://invalid-scheme.com",
    }
    response = auth_client.post("/api/v1/monitors", json=payload)
    assert response.status_code == 422
