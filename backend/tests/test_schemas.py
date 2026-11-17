import uuid
from datetime import UTC, datetime

import pytest
from app.schemas.monitor import (
    MonitorCreate,
    MonitorResponse,
    MonitorUpdate,
)
from pydantic import ValidationError


def test_monitor_create_valid():
    """Verify MonitorCreate schema parses valid input."""
    data = {
        "name": "User Service",
        "url": "https://api.example.com/health",
        "http_method": "GET",
        "interval_seconds": 60,
        "timeout_seconds": 15,
        "expected_status_code": 200,
        "headers": {"Authorization": "Bearer token"},
        "is_active": True,
    }
    schema = MonitorCreate(**data)
    assert schema.name == "User Service"
    assert str(schema.url) == "https://api.example.com/health"
    assert schema.http_method == "GET"
    assert schema.interval_seconds == 60
    assert schema.timeout_seconds == 15
    assert schema.expected_status_code == 200


def test_monitor_create_invalid_url():
    """Verify MonitorCreate rejects non-HTTP/HTTPS URLs."""
    invalid_urls = [
        "not-a-url",
        "ftp://files.example.com/resource",
        "javascript:alert(1)",
        "",
    ]
    for url in invalid_urls:
        with pytest.raises(ValidationError):
            MonitorCreate(
                name="Test",
                url=url,
            )


def test_monitor_create_invalid_intervals():
    """Verify MonitorCreate rejects non-positive interval and timeout."""
    with pytest.raises(ValidationError):
        MonitorCreate(name="Test", url="https://example.com", interval_seconds=0)

    with pytest.raises(ValidationError):
        MonitorCreate(name="Test", url="https://example.com", interval_seconds=-10)

    with pytest.raises(ValidationError):
        MonitorCreate(name="Test", url="https://example.com", timeout_seconds=0)

    with pytest.raises(ValidationError):
        MonitorCreate(name="Test", url="https://example.com", timeout_seconds=-5)


def test_monitor_create_invalid_method():
    """Verify MonitorCreate normalizes or validates HTTP method."""
    with pytest.raises(ValidationError):
        MonitorCreate(name="Test", url="https://example.com", http_method="INVALID_METHOD")


def test_monitor_update_partial():
    """Verify MonitorUpdate allows partial updates."""
    update = MonitorUpdate(name="New Name", interval_seconds=120)
    data = update.model_dump(exclude_unset=True)
    assert data == {"name": "New Name", "interval_seconds": 120}
    assert "url" not in data


def test_monitor_response_from_attributes():
    """Verify MonitorResponse serializes ORM-like objects."""
    target_id = uuid.uuid4()
    target_user_id = uuid.uuid4()
    now = datetime.now(UTC)

    class MockORM:
        def __init__(self):
            self.id = target_id
            self.user_id = target_user_id
            self.name = "Payment Gateway"
            self.url = "https://pay.example.com/health"
            self.http_method = "POST"
            self.interval_seconds = 30
            self.timeout_seconds = 10
            self.expected_status_code = 200
            self.headers = {"Content-Type": "application/json"}
            self.body = {"ping": "pong"}
            self.is_active = True
            self.created_at = now
            self.updated_at = now

    res = MonitorResponse.model_validate(MockORM())
    assert res.id == target_id
    assert res.user_id == target_user_id
    assert res.name == "Payment Gateway"
    assert res.url == "https://pay.example.com/health"
    assert res.http_method == "POST"
    assert res.headers == {"Content-Type": "application/json"}
