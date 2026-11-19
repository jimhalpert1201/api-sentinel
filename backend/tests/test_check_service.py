from unittest.mock import AsyncMock, patch

import httpx
import pytest
from app.models.check_result import CheckResult
from app.models.monitor import Monitor
from app.models.user import User
from app.schemas.check_result import CheckExecutionResult, CheckResultResponse
from app.services.check_service import (
    execute_http_probe,
    record_check_result,
    run_monitor_check,
)


@pytest.fixture
def test_user(db_session):
    user = User(
        email="probe_user@example.com",
        username="probe_user",
        hashed_password="fake_hashed_password_123",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_monitor(db_session, test_user):
    monitor = Monitor(
        user_id=test_user.id,
        name="Target API",
        url="https://api.example.com/health",
        http_method="GET",
        interval_seconds=60,
        timeout_seconds=5,
        expected_status_code=200,
    )
    db_session.add(monitor)
    db_session.commit()
    db_session.refresh(monitor)
    return monitor


@pytest.mark.asyncio
async def test_execute_http_probe_success():
    """Verify probe returns successful result when target responds with expected status code."""
    mock_response = httpx.Response(
        status_code=200,
        request=httpx.Request("GET", "https://api.example.com/health"),
    )

    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_response

        result = await execute_http_probe(
            url="https://api.example.com/health",
            method="GET",
            headers={"Authorization": "Bearer test"},
            body=None,
            timeout_seconds=5,
            expected_status_code=200,
        )

        assert isinstance(result, CheckExecutionResult)
        assert result.is_successful is True
        assert result.status_code == 200
        assert result.error_message is None
        assert result.response_time_ms >= 0.0
        assert mock_request.call_count == 1


@pytest.mark.asyncio
async def test_execute_http_probe_status_mismatch():
    """Verify probe returns unsuccessful when status doesn't match expected status."""
    mock_response = httpx.Response(
        status_code=503,
        request=httpx.Request("GET", "https://api.example.com/health"),
    )

    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_response

        result = await execute_http_probe(
            url="https://api.example.com/health",
            method="GET",
            headers=None,
            body=None,
            timeout_seconds=5,
            expected_status_code=200,
        )

        assert result.is_successful is False
        assert result.status_code == 503
        assert result.error_message == "Status code 503 did not match expected 200"
        assert result.response_time_ms >= 0.0
        # Should retry once per NFR-021 if first attempt fails
        assert mock_request.call_count == 2


@pytest.mark.asyncio
async def test_execute_http_probe_retry_success():
    """Verify probe retries on first failure and succeeds if second attempt passes."""
    fail_response = httpx.Response(
        status_code=500,
        request=httpx.Request("GET", "https://api.example.com/health"),
    )
    success_response = httpx.Response(
        status_code=200,
        request=httpx.Request("GET", "https://api.example.com/health"),
    )

    with (
        patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_request,
        patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
    ):
        mock_request.side_effect = [fail_response, success_response]

        result = await execute_http_probe(
            url="https://api.example.com/health",
            method="GET",
            headers=None,
            body=None,
            timeout_seconds=5,
            expected_status_code=200,
        )

        assert result.is_successful is True
        assert result.status_code == 200
        assert mock_request.call_count == 2
        mock_sleep.assert_awaited_once_with(1.0)


@pytest.mark.asyncio
async def test_execute_http_probe_timeout_error():
    """Verify probe gracefully handles timeout error and captures error message."""
    with (
        patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_request,
        patch("asyncio.sleep", new_callable=AsyncMock),
    ):
        mock_request.side_effect = httpx.ConnectTimeout("Connection timed out after 5.0s")

        result = await execute_http_probe(
            url="https://api.example.com/health",
            method="GET",
            headers=None,
            body=None,
            timeout_seconds=5,
            expected_status_code=200,
        )

        assert result.is_successful is False
        assert result.status_code is None
        assert "timed out" in (result.error_message or "").lower()
        assert mock_request.call_count == 2


@pytest.mark.asyncio
async def test_execute_http_probe_connection_error():
    """Verify probe gracefully handles connection failure/DNS resolution failure."""
    with (
        patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_request,
        patch("asyncio.sleep", new_callable=AsyncMock),
    ):
        mock_request.side_effect = httpx.ConnectError("Failed to resolve host")

        result = await execute_http_probe(
            url="https://invalid-host-domain.test/health",
            method="GET",
            headers=None,
            body=None,
            timeout_seconds=5,
            expected_status_code=200,
        )

        assert result.is_successful is False
        assert result.status_code is None
        assert "Failed to resolve host" in (result.error_message or "")
        assert mock_request.call_count == 2


def test_record_check_result(db_session, test_monitor):
    """Verify record_check_result stores CheckResult row correctly in database."""
    execution = CheckExecutionResult(
        status_code=200,
        response_time_ms=124.55,
        is_successful=True,
        error_message=None,
    )

    record = record_check_result(
        db=db_session,
        monitor_id=test_monitor.id,
        result=execution,
    )

    assert isinstance(record, CheckResult)
    assert record.id is not None
    assert record.monitor_id == test_monitor.id
    assert record.status_code == 200
    assert record.response_time_ms == 124.55
    assert record.is_successful is True
    assert record.error_message is None
    assert record.checked_at is not None

    # Verify schema serialization works
    schema_dump = CheckResultResponse.model_validate(record)
    assert schema_dump.status_code == 200


@pytest.mark.asyncio
async def test_run_monitor_check(db_session, test_monitor):
    """Verify run_monitor_check executes probe and persists check result for a monitor."""
    mock_response = httpx.Response(
        status_code=200,
        request=httpx.Request("GET", test_monitor.url),
    )

    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_response

        check = await run_monitor_check(db=db_session, monitor=test_monitor)

        assert isinstance(check, CheckResult)
        assert check.monitor_id == test_monitor.id
        assert check.status_code == 200
        assert check.is_successful is True

        # Query database to confirm persisted
        stored = db_session.query(CheckResult).filter_by(id=check.id).first()
        assert stored is not None
        assert stored.monitor_id == test_monitor.id


@pytest.mark.asyncio
async def test_execute_http_probe_generic_exception():
    """Verify probe catches unexpected generic exceptions."""
    with (
        patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_request,
        patch("asyncio.sleep", new_callable=AsyncMock),
    ):
        mock_request.side_effect = RuntimeError("Unexpected socket error")

        result = await execute_http_probe(
            url="https://api.example.com/health",
            method="GET",
        )

        assert result.is_successful is False
        assert result.status_code is None
        assert "Unexpected socket error" in (result.error_message or "")

