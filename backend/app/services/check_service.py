import asyncio
import time
import uuid
from datetime import UTC, datetime
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.check_result import CheckResult
from app.models.monitor import Monitor
from app.schemas.check_result import CheckExecutionResult
from app.services.incident_service import evaluate_monitor_incidents


async def _perform_single_probe(
    url: str,
    method: str,
    headers: dict[str, Any] | None,
    body: dict[str, Any] | None,
    timeout_seconds: int,
    expected_status_code: int,
) -> CheckExecutionResult:
    """Execute a single HTTP request probe and measure latency."""
    start_time = time.perf_counter()
    status_code: int | None = None
    error_message: str | None = None
    is_successful: bool = False

    try:
        async with httpx.AsyncClient(
            timeout=float(timeout_seconds),
            follow_redirects=True,
        ) as client:
            response = await client.request(
                method=method.upper(),
                url=url,
                headers=headers,
                json=body if body is not None else None,
            )
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            status_code = response.status_code

            if status_code == expected_status_code:
                is_successful = True
            else:
                is_successful = False
                error_message = (
                    f"Status code {status_code} did not match expected {expected_status_code}"
                )

            return CheckExecutionResult(
                status_code=status_code,
                response_time_ms=elapsed_ms,
                is_successful=is_successful,
                error_message=error_message,
            )

    except httpx.TimeoutException as exc:
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return CheckExecutionResult(
            status_code=None,
            response_time_ms=elapsed_ms,
            is_successful=False,
            error_message=f"Request timed out: {exc}",
        )
    except httpx.ConnectError as exc:
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return CheckExecutionResult(
            status_code=None,
            response_time_ms=elapsed_ms,
            is_successful=False,
            error_message=f"Connection failed: {exc}",
        )
    except Exception as exc:
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return CheckExecutionResult(
            status_code=None,
            response_time_ms=elapsed_ms,
            is_successful=False,
            error_message=f"HTTP probe error: {exc}",
        )


async def execute_http_probe(
    url: str,
    method: str,
    headers: dict[str, Any] | None = None,
    body: dict[str, Any] | None = None,
    timeout_seconds: int = 30,
    expected_status_code: int = 200,
) -> CheckExecutionResult:
    """
    Execute HTTP health probe against target URL.
    Per NFR-021: If initial check fails, retry once after 1s backoff before recording failure.
    """
    result = await _perform_single_probe(
        url=url,
        method=method,
        headers=headers,
        body=body,
        timeout_seconds=timeout_seconds,
        expected_status_code=expected_status_code,
    )

    if not result.is_successful:
        await asyncio.sleep(1.0)
        retry_result = await _perform_single_probe(
            url=url,
            method=method,
            headers=headers,
            body=body,
            timeout_seconds=timeout_seconds,
            expected_status_code=expected_status_code,
        )
        return retry_result

    return result


def record_check_result(
    db: Session,
    monitor_id: uuid.UUID,
    result: CheckExecutionResult,
) -> CheckResult:
    """Persist check execution outcome into check_results table."""
    check_record = CheckResult(
        monitor_id=monitor_id,
        status_code=result.status_code,
        response_time_ms=result.response_time_ms,
        is_successful=result.is_successful,
        error_message=result.error_message,
        checked_at=datetime.now(UTC),
    )
    db.add(check_record)
    db.commit()
    db.refresh(check_record)
    return check_record


async def run_monitor_check(db: Session, monitor: Monitor) -> CheckResult:
    """
    Perform an end-to-end health check for a configured monitor and save result.
    """
    execution_result = await execute_http_probe(
        url=monitor.url,
        method=monitor.http_method,
        headers=monitor.headers,
        body=monitor.body,
        timeout_seconds=monitor.timeout_seconds,
        expected_status_code=monitor.expected_status_code,
    )

    check_record = record_check_result(
        db=db,
        monitor_id=monitor.id,
        result=execution_result,
    )

    evaluate_monitor_incidents(
        db=db,
        monitor_id=monitor.id,
        latest_check=check_record,
        threshold=settings.incident_threshold_failures,
    )

    return check_record
