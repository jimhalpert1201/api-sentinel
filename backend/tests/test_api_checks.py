import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import httpx
from app.auth.jwt import create_access_token
from app.models.check_result import CheckResult
from app.models.monitor import Monitor
from app.models.user import User


def test_manual_check_trigger_success(client, db_session):
    """Verify owner can trigger immediate manual health check."""
    user = User(email="checker@example.com", username="checker", hashed_password="pw")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    monitor = Monitor(
        user_id=user.id,
        name="API Test",
        url="https://api.test.com/ping",
        http_method="GET",
        interval_seconds=60,
        timeout_seconds=5,
        expected_status_code=200,
    )
    db_session.add(monitor)
    db_session.commit()
    db_session.refresh(monitor)

    token = create_access_token(user_id=user.id)
    headers = {"Authorization": f"Bearer {token}"}

    mock_resp = httpx.Response(status_code=200, request=httpx.Request("GET", monitor.url))
    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_resp

        response = client.post(f"/api/v1/monitors/{monitor.id}/check", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["monitor_id"] == str(monitor.id)
        assert data["status_code"] == 200
        assert data["is_successful"] is True
        assert data["response_time_ms"] >= 0.0


def test_manual_check_trigger_cross_user_isolation(client, db_session):
    """Verify user B cannot trigger manual check on user A's monitor (returns 404)."""
    user_a = User(email="user_a@example.com", username="user_a", hashed_password="pw")
    user_b = User(email="user_b@example.com", username="user_b", hashed_password="pw")
    db_session.add_all([user_a, user_b])
    db_session.commit()

    monitor_a = Monitor(
        user_id=user_a.id,
        name="User A API",
        url="https://api.test.com/a",
    )
    db_session.add(monitor_a)
    db_session.commit()

    token_b = create_access_token(user_id=user_b.id)
    headers_b = {"Authorization": f"Bearer {token_b}"}

    response = client.post(f"/api/v1/monitors/{monitor_a.id}/check", headers=headers_b)
    assert response.status_code == 404
    assert response.json()["detail"] == "Monitor not found"


def test_manual_check_trigger_unauthenticated(client):
    """Verify unauthenticated request to trigger check returns 401."""
    random_id = uuid.uuid4()
    response = client.post(f"/api/v1/monitors/{random_id}/check")
    assert response.status_code == 401


def test_get_monitor_checks_empty(client, db_session):
    """Verify checks endpoint returns empty paginated list when no checks recorded."""
    user = User(email="empty_chk@example.com", username="empty_chk", hashed_password="pw")
    db_session.add(user)
    db_session.commit()

    monitor = Monitor(user_id=user.id, name="Empty API", url="https://api.test.com")
    db_session.add(monitor)
    db_session.commit()

    token = create_access_token(user_id=user.id)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get(f"/api/v1/monitors/{monitor.id}/checks", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["page"] == 1
    assert data["page_size"] == 50


def test_get_monitor_checks_pagination(client, db_session):
    """Verify checks endpoint supports pagination with page and page_size."""
    user = User(email="page_user@example.com", username="page_user", hashed_password="pw")
    db_session.add(user)
    db_session.commit()

    monitor = Monitor(user_id=user.id, name="Paginated API", url="https://api.test.com")
    db_session.add(monitor)
    db_session.commit()

    # Add 15 check results
    now = datetime.now(UTC)
    for i in range(15):
        db_session.add(
            CheckResult(
                monitor_id=monitor.id,
                status_code=200,
                response_time_ms=10.0 + i,
                is_successful=True,
                checked_at=now - timedelta(minutes=i),
            )
        )
    db_session.commit()

    token = create_access_token(user_id=user.id)
    headers = {"Authorization": f"Bearer {token}"}

    # Query page 1, size 10
    response = client.get(
        f"/api/v1/monitors/{monitor.id}/checks?page=1&page_size=10",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 10
    assert data["total"] == 15
    assert data["page"] == 1
    assert data["page_size"] == 10

    # Query page 2, size 10
    response2 = client.get(
        f"/api/v1/monitors/{monitor.id}/checks?page=2&page_size=10",
        headers=headers,
    )
    assert response2.status_code == 200
    data2 = response2.json()
    assert len(data2["items"]) == 5
    assert data2["total"] == 15
    assert data2["page"] == 2


def test_get_monitor_checks_filter_status(client, db_session):
    """Verify filtering checks by is_successful boolean."""
    user = User(email="filt_status@example.com", username="filt_status", hashed_password="pw")
    db_session.add(user)
    db_session.commit()

    monitor = Monitor(user_id=user.id, name="Status Filter API", url="https://api.test.com")
    db_session.add(monitor)
    db_session.commit()

    now = datetime.now(UTC)
    # Add 3 successful and 2 failed
    for i in range(3):
        db_session.add(
            CheckResult(
                monitor_id=monitor.id,
                status_code=200,
                response_time_ms=50.0,
                is_successful=True,
                checked_at=now - timedelta(minutes=i),
            )
        )
    for i in range(2):
        db_session.add(
            CheckResult(
                monitor_id=monitor.id,
                status_code=500,
                response_time_ms=50.0,
                is_successful=False,
                checked_at=now - timedelta(minutes=i + 5),
            )
        )
    db_session.commit()

    token = create_access_token(user_id=user.id)
    headers = {"Authorization": f"Bearer {token}"}

    # Filter successful only
    resp_success = client.get(
        f"/api/v1/monitors/{monitor.id}/checks?is_successful=true",
        headers=headers,
    )
    assert resp_success.status_code == 200
    assert resp_success.json()["total"] == 3
    assert all(item["is_successful"] is True for item in resp_success.json()["items"])

    # Filter failed only
    resp_failed = client.get(
        f"/api/v1/monitors/{monitor.id}/checks?is_successful=false",
        headers=headers,
    )
    assert resp_failed.status_code == 200
    assert resp_failed.json()["total"] == 2
    assert all(item["is_successful"] is False for item in resp_failed.json()["items"])


def test_get_monitor_checks_filter_date_range(client, db_session):
    """Verify filtering checks by from_date and to_date."""
    user = User(email="date_user@example.com", username="date_user", hashed_password="pw")
    db_session.add(user)
    db_session.commit()

    monitor = Monitor(user_id=user.id, name="Date Filter API", url="https://api.test.com")
    db_session.add(monitor)
    db_session.commit()

    base_time = datetime(2026, 11, 15, 12, 0, 0, tzinfo=UTC)
    # Day 1: Nov 15, Day 2: Nov 16, Day 3: Nov 17
    for day in range(3):
        db_session.add(
            CheckResult(
                monitor_id=monitor.id,
                status_code=200,
                response_time_ms=25.0,
                is_successful=True,
                checked_at=base_time + timedelta(days=day),
            )
        )
    db_session.commit()

    token = create_access_token(user_id=user.id)
    headers = {"Authorization": f"Bearer {token}"}

    from_iso = (base_time + timedelta(days=1)).isoformat()
    to_iso = (base_time + timedelta(days=2)).isoformat()

    response = client.get(
        f"/api/v1/monitors/{monitor.id}/checks",
        params={"from_date": from_iso, "to_date": to_iso},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2


def test_get_monitor_checks_cross_user_isolation(client, db_session):
    """Verify user B cannot query check history of user A's monitor."""
    user_a = User(email="owner_a@example.com", username="owner_a", hashed_password="pw")
    user_b = User(email="owner_b@example.com", username="owner_b", hashed_password="pw")
    db_session.add_all([user_a, user_b])
    db_session.commit()

    monitor_a = Monitor(user_id=user_a.id, name="Owner A API", url="https://api.test.com")
    db_session.add(monitor_a)
    db_session.commit()

    token_b = create_access_token(user_id=user_b.id)
    headers_b = {"Authorization": f"Bearer {token_b}"}

    response = client.get(f"/api/v1/monitors/{monitor_a.id}/checks", headers=headers_b)
    assert response.status_code == 404
    assert response.json()["detail"] == "Monitor not found"
