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
    """Verify get_current_user auto-provisions dev user when DB is empty and reuses it."""
    user1 = get_current_user(db=db_session)
    assert user1 is not None
    assert user1.email == "dev@sentinel.local"

    user2 = get_current_user(db=db_session)
    assert user2.id == user1.id


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
