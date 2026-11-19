import uuid
from datetime import UTC, datetime, timedelta

import pytest
from app.auth.jwt import create_access_token
from app.models.check_result import CheckResult
from app.models.monitor import Monitor
from app.models.user import User
from fastapi.testclient import TestClient


@pytest.fixture
def owner_user(db_session):
    user = User(email="owner@example.com", username="owner_user", hashed_password="pw")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def other_user(db_session):
    user = User(email="other_m@example.com", username="other_m_user", hashed_password="pw")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_monitor(db_session, owner_user):
    monitor = Monitor(
        user_id=owner_user.id,
        name="Production Metrics API",
        url="https://api.example.com",
        interval_seconds=60,
    )
    db_session.add(monitor)
    db_session.commit()
    db_session.refresh(monitor)
    return monitor


def test_get_monitor_metrics_default_24h(client: TestClient, db_session, test_monitor, owner_user):
    """Verify GET /api/v1/monitors/{id}/metrics defaults to 24h window and returns 200."""
    now = datetime.now(UTC)
    check = CheckResult(
        monitor_id=test_monitor.id,
        status_code=200,
        response_time_ms=75.0,
        is_successful=True,
        checked_at=now - timedelta(hours=1),
    )
    db_session.add(check)
    db_session.commit()

    token = create_access_token(user_id=owner_user.id)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get(f"/api/v1/monitors/{test_monitor.id}/metrics", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert data["monitor_id"] == str(test_monitor.id)
    assert data["window"] == "24h"
    assert data["summary"]["total_checks"] == 1
    assert data["summary"]["successful_checks"] == 1
    assert data["summary"]["uptime_percentage"] == 100.0
    assert data["summary"]["avg_response_time_ms"] == 75.0
    assert len(data["series"]) == 24


def test_get_monitor_metrics_7d_and_30d(client: TestClient, test_monitor, owner_user):
    """Verify query parameter window=7d and window=30d return corresponding bucket counts."""
    token = create_access_token(user_id=owner_user.id)
    headers = {"Authorization": f"Bearer {token}"}

    # Test 7d
    res_7d = client.get(
        f"/api/v1/monitors/{test_monitor.id}/metrics",
        params={"window": "7d"},
        headers=headers,
    )
    assert res_7d.status_code == 200
    assert res_7d.json()["window"] == "7d"
    assert len(res_7d.json()["series"]) == 7

    # Test 30d
    res_30d = client.get(
        f"/api/v1/monitors/{test_monitor.id}/metrics",
        params={"window": "30d"},
        headers=headers,
    )
    assert res_30d.status_code == 200
    assert res_30d.json()["window"] == "30d"
    assert len(res_30d.json()["series"]) == 30


def test_get_monitor_metrics_invalid_window_422(client: TestClient, test_monitor, owner_user):
    """Verify invalid window parameter returns 422 Unprocessable Entity."""
    token = create_access_token(user_id=owner_user.id)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get(
        f"/api/v1/monitors/{test_monitor.id}/metrics",
        params={"window": "invalid_window"},
        headers=headers,
    )
    assert response.status_code == 422


def test_get_monitor_metrics_tenant_isolation(client: TestClient, test_monitor, other_user):
    """Verify user cannot view metrics for another user's monitor (returns 404)."""
    token = create_access_token(user_id=other_user.id)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get(f"/api/v1/monitors/{test_monitor.id}/metrics", headers=headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "Monitor not found"


def test_get_monitor_metrics_not_found(client: TestClient, owner_user):
    """Verify unknown monitor ID returns 404."""
    token = create_access_token(user_id=owner_user.id)
    headers = {"Authorization": f"Bearer {token}"}

    random_id = uuid.uuid4()
    response = client.get(f"/api/v1/monitors/{random_id}/metrics", headers=headers)
    assert response.status_code == 404


def test_get_monitor_metrics_unauthenticated(client: TestClient, test_monitor):
    """Verify unauthenticated request returns 401."""
    response = client.get(f"/api/v1/monitors/{test_monitor.id}/metrics")
    assert response.status_code == 401
