import asyncio
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from app.core.config import settings
from app.models.check_result import CheckResult
from app.models.monitor import Monitor
from app.models.user import User
from app.workers.scheduler import (
    AsyncMonitorScheduler,
    get_monitors_due_for_check,
    run_scheduler_tick,
)

from tests.conftest import TestingSessionLocal


@pytest.fixture
def scheduler_user(db_session):
    user = User(email="sched@example.com", username="sched_user", hashed_password="pw")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_get_monitors_due_never_checked(db_session, scheduler_user):
    """Verify monitor with no prior check results is due immediately."""
    monitor = Monitor(
        user_id=scheduler_user.id,
        name="Fresh Monitor",
        url="https://api.example.com",
        interval_seconds=60,
        is_active=True,
    )
    db_session.add(monitor)
    db_session.commit()

    now = datetime.now(UTC)
    due = get_monitors_due_for_check(db_session, now)
    assert any(m.id == monitor.id for m in due)


def test_get_monitors_due_elapsed_interval(db_session, scheduler_user):
    """Verify monitor is due if interval_seconds has passed since last check."""
    monitor = Monitor(
        user_id=scheduler_user.id,
        name="Interval Monitor",
        url="https://api.example.com",
        interval_seconds=60,
        is_active=True,
    )
    db_session.add(monitor)
    db_session.commit()

    # Check was 65 seconds ago
    past_check = CheckResult(
        monitor_id=monitor.id,
        status_code=200,
        response_time_ms=50.0,
        is_successful=True,
        checked_at=datetime.now(UTC) - timedelta(seconds=65),
    )
    db_session.add(past_check)
    db_session.commit()

    now = datetime.now(UTC)
    due = get_monitors_due_for_check(db_session, now)
    assert any(m.id == monitor.id for m in due)


def test_get_monitors_due_not_elapsed(db_session, scheduler_user):
    """Verify monitor is NOT due if interval_seconds has NOT passed."""
    monitor = Monitor(
        user_id=scheduler_user.id,
        name="Recent Monitor",
        url="https://api.example.com",
        interval_seconds=60,
        is_active=True,
    )
    db_session.add(monitor)
    db_session.commit()

    # Check was 10 seconds ago
    recent_check = CheckResult(
        monitor_id=monitor.id,
        status_code=200,
        response_time_ms=50.0,
        is_successful=True,
        checked_at=datetime.now(UTC) - timedelta(seconds=10),
    )
    db_session.add(recent_check)
    db_session.commit()

    now = datetime.now(UTC)
    due = get_monitors_due_for_check(db_session, now)
    assert not any(m.id == monitor.id for m in due)


def test_get_monitors_due_ignores_inactive(db_session, scheduler_user):
    """Verify inactive monitors (is_active=False) are never selected."""
    monitor = Monitor(
        user_id=scheduler_user.id,
        name="Paused Monitor",
        url="https://api.example.com",
        interval_seconds=60,
        is_active=False,
    )
    db_session.add(monitor)
    db_session.commit()

    now = datetime.now(UTC)
    due = get_monitors_due_for_check(db_session, now)
    assert not any(m.id == monitor.id for m in due)


@pytest.mark.asyncio
async def test_run_scheduler_tick(db_session, scheduler_user):
    """Verify scheduler tick executes checks for due monitors and records results."""
    monitor = Monitor(
        user_id=scheduler_user.id,
        name="Tick Monitor",
        url="https://api.example.com/tick",
        interval_seconds=60,
        is_active=True,
    )
    db_session.add(monitor)
    db_session.commit()

    mock_resp = httpx.Response(status_code=200, request=httpx.Request("GET", monitor.url))
    with patch("httpx.AsyncClient.request", new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_resp

        executed_count = await run_scheduler_tick(session_factory=TestingSessionLocal)
        assert executed_count >= 1

        # Check result was written in database
        latest = (
            db_session.query(CheckResult)
            .filter_by(monitor_id=monitor.id)
            .order_by(CheckResult.checked_at.desc())
            .first()
        )
        assert latest is not None
        assert latest.status_code == 200
        assert latest.is_successful is True


@pytest.mark.asyncio
async def test_async_monitor_scheduler_start_stop():
    """Verify AsyncMonitorScheduler starts background loop and stops cleanly."""
    scheduler = AsyncMonitorScheduler(interval_seconds=1)
    assert scheduler.is_running is False

    with patch.object(scheduler, "_tick", new_callable=AsyncMock) as mock_tick:
        scheduler.start()
        assert scheduler.is_running is True

        await asyncio.sleep(0.05)
        await scheduler.stop()
        assert scheduler.is_running is False
        assert mock_tick.call_count >= 1


def test_scheduler_settings():
    """Verify scheduler configuration settings exist."""
    assert hasattr(settings, "scheduler_enabled")
    assert hasattr(settings, "scheduler_interval_seconds")


@pytest.mark.asyncio
async def test_app_lifespan_starts_and_stops_scheduler():
    """Verify FastAPI lifespan manages AsyncMonitorScheduler lifecycle."""
    from app.main import app, lifespan

    with (
        patch("app.main.settings.scheduler_enabled", True),
        patch("app.main.AsyncMonitorScheduler") as mock_scheduler_cls,
    ):
        mock_instance = MagicMock()
        mock_instance.stop = AsyncMock()
        mock_scheduler_cls.return_value = mock_instance

        async with lifespan(app):
            mock_scheduler_cls.assert_called_once()
            mock_instance.start.assert_called_once()

        mock_instance.stop.assert_awaited_once()


@pytest.mark.asyncio
async def test_app_lifespan_disabled_scheduler():
    """Verify FastAPI lifespan skips scheduler when disabled."""
    from app.main import app, lifespan

    with (
        patch("app.main.settings.scheduler_enabled", False),
        patch("app.main.AsyncMonitorScheduler") as mock_scheduler_cls,
    ):
        async with lifespan(app):
            mock_scheduler_cls.assert_not_called()
