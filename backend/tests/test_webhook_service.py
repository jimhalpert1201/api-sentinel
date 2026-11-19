import asyncio
import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from app.models.check_result import CheckResult
from app.models.monitor import Monitor
from app.models.user import User
from app.schemas.webhook import WebhookPayload
from app.services.incident_service import evaluate_monitor_incidents
from app.services.webhook_service import (
    dispatch_incident_webhook_safely,
    send_incident_webhook,
)


@pytest.fixture
def sample_payload() -> WebhookPayload:
    return WebhookPayload(
        event="incident_created",
        incident_id=uuid.uuid4(),
        monitor_id=uuid.uuid4(),
        monitor_name="Production API",
        monitor_url="https://api.example.com/health",
        status="open",
        cause="downtime",
        started_at=datetime.now(UTC),
        resolved_at=None,
        description="Monitor failed 3 consecutive checks.",
    )


@pytest.mark.asyncio
async def test_send_incident_webhook_success(sample_payload):
    """Verify webhook sends successfully on 200 response."""
    mock_resp = httpx.Response(status_code=200, request=httpx.Request("POST", "https://hook.test"))
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp

        success = await send_incident_webhook("https://hook.test", sample_payload)
        assert success is True
        assert mock_post.call_count == 1


@pytest.mark.asyncio
async def test_send_incident_webhook_retry_on_500(sample_payload):
    """Verify webhook retries once after 2s backoff on 5xx server error."""
    mock_fail = httpx.Response(status_code=500, request=httpx.Request("POST", "https://hook.test"))
    mock_ok = httpx.Response(status_code=200, request=httpx.Request("POST", "https://hook.test"))

    with (
        patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post,
        patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
    ):
        mock_post.side_effect = [mock_fail, mock_ok]

        success = await send_incident_webhook("https://hook.test", sample_payload)
        assert success is True
        assert mock_post.call_count == 2
        mock_sleep.assert_awaited_once_with(2.0)


@pytest.mark.asyncio
async def test_send_incident_webhook_4xx_does_not_retry(sample_payload):
    """Verify client errors (4xx) are unrecoverable and NOT retried."""
    mock_400 = httpx.Response(status_code=400, request=httpx.Request("POST", "https://hook.test"))

    with (
        patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post,
        patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
    ):
        mock_post.return_value = mock_400

        success = await send_incident_webhook("https://hook.test", sample_payload)
        assert success is False
        assert mock_post.call_count == 1
        mock_sleep.assert_not_called()


@pytest.mark.asyncio
async def test_send_incident_webhook_timeout_error(sample_payload):
    """Verify timeout exception triggers retry and returns False on persistent failure."""
    with (
        patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post,
        patch("asyncio.sleep", new_callable=AsyncMock),
    ):
        mock_post.side_effect = httpx.ConnectTimeout("Connection timed out")

        success = await send_incident_webhook("https://hook.test", sample_payload)
        assert success is False
        assert mock_post.call_count == 2


@pytest.mark.asyncio
async def test_send_incident_webhook_generic_exception(sample_payload):
    """Verify unexpected exception does not crash and returns False."""
    with (
        patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post,
        patch("asyncio.sleep", new_callable=AsyncMock),
    ):
        mock_post.side_effect = RuntimeError("Socket write failed")

        success = await send_incident_webhook("https://hook.test", sample_payload)
        assert success is False
        assert mock_post.call_count == 2


def test_dispatch_incident_webhook_safely_no_url(sample_payload):
    """Verify dispatch does nothing when webhook_url is None or empty."""
    with patch("app.services.webhook_service.send_incident_webhook") as mock_send:
        dispatch_incident_webhook_safely(None, sample_payload)
        dispatch_incident_webhook_safely("", sample_payload)
        mock_send.assert_not_called()


@pytest.mark.asyncio
async def test_dispatch_incident_webhook_safely_in_event_loop(sample_payload):
    """Verify dispatch schedules task when running inside an event loop."""
    with patch(
        "app.services.webhook_service.send_incident_webhook", new_callable=AsyncMock
    ) as mock_send:
        dispatch_incident_webhook_safely("https://hook.test", sample_payload)
        # Yield to event loop to allow scheduled task to run
        await asyncio.sleep(0.01)
        mock_send.assert_called_once()


def test_dispatch_incident_webhook_safely_without_event_loop(sample_payload):
    """Verify dispatch gracefully passes without crashing when no event loop exists."""
    # When running synchronously in a standard test function without an event loop
    with patch("asyncio.get_running_loop", side_effect=RuntimeError("no running event loop")):
        # Should NOT raise RuntimeError
        dispatch_incident_webhook_safely("https://hook.test", sample_payload)


def test_incident_service_triggers_webhook_on_create_and_resolve(db_session):
    """Verify evaluate_monitor_incidents triggers webhooks when webhook_url is configured."""
    user = User(email="webhooker@example.com", username="webhooker", hashed_password="pw")
    db_session.add(user)
    db_session.commit()

    monitor = Monitor(
        user_id=user.id,
        name="Webhook Monitor",
        url="https://api.example.com",
        webhook_url="https://hooks.example.com/alerts",
        interval_seconds=60,
    )
    db_session.add(monitor)
    db_session.commit()

    # Create 3 failed checks
    for _ in range(3):
        check = CheckResult(
            monitor_id=monitor.id,
            status_code=500,
            response_time_ms=100.0,
            is_successful=False,
            checked_at=datetime.now(UTC),
        )
        db_session.add(check)
        db_session.commit()

    with patch("app.services.incident_service.dispatch_incident_webhook_safely") as mock_dispatch:
        # Trigger incident evaluation on 3rd failure
        incident = evaluate_monitor_incidents(
            db=db_session,
            monitor_id=monitor.id,
            latest_check=check,
            threshold=3,
            monitor=monitor,
        )
        assert incident is not None
        assert incident.status == "open"
        mock_dispatch.assert_called_once()
        payload = mock_dispatch.call_args[0][1]
        assert payload.event == "incident_created"
        assert payload.monitor_name == monitor.name
        assert payload.status == "open"

    # Now add 3 successful checks to trigger resolution
    for _ in range(3):
        succ_check = CheckResult(
            monitor_id=monitor.id,
            status_code=200,
            response_time_ms=50.0,
            is_successful=True,
            checked_at=datetime.now(UTC),
        )
        db_session.add(succ_check)
        db_session.commit()

    with patch("app.services.incident_service.dispatch_incident_webhook_safely") as mock_dispatch:
        resolved_incident = evaluate_monitor_incidents(
            db=db_session,
            monitor_id=monitor.id,
            latest_check=succ_check,
            threshold=3,
            monitor=monitor,
        )
        assert resolved_incident is not None
        assert resolved_incident.status == "resolved"
        mock_dispatch.assert_called_once()
        payload = mock_dispatch.call_args[0][1]
        assert payload.event == "incident_resolved"
        assert payload.status == "resolved"
