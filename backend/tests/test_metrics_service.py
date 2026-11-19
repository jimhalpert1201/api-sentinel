from datetime import UTC, datetime, timedelta

import pytest
from app.models.check_result import CheckResult
from app.models.monitor import Monitor
from app.models.user import User
from app.schemas.metrics import MonitorMetricsResponse, TimeSeriesPoint
from app.services.metrics_service import get_monitor_metrics


@pytest.fixture
def metric_monitor(db_session):
    user = User(email="metrics_user@example.com", username="muser", hashed_password="pw")
    db_session.add(user)
    db_session.commit()

    monitor = Monitor(
        user_id=user.id,
        name="Metrics API",
        url="https://api.example.com",
        interval_seconds=60,
    )
    db_session.add(monitor)
    db_session.commit()
    db_session.refresh(monitor)
    return monitor


def test_get_monitor_metrics_empty_checks(db_session, metric_monitor):
    """Verify monitor with no checks returns 100.0% uptime and None for all latencies."""
    metrics = get_monitor_metrics(db=db_session, monitor=metric_monitor, window="24h")
    assert isinstance(metrics, MonitorMetricsResponse)
    assert metrics.monitor_id == metric_monitor.id
    assert metrics.window == "24h"

    assert metrics.summary.total_checks == 0
    assert metrics.summary.successful_checks == 0
    assert metrics.summary.failed_checks == 0
    assert metrics.summary.uptime_percentage == 100.0
    assert metrics.summary.avg_response_time_ms is None
    assert metrics.summary.p50_response_time_ms is None
    assert metrics.summary.p95_response_time_ms is None
    assert metrics.summary.p99_response_time_ms is None

    # Series contains contiguous hourly buckets (24 buckets)
    assert len(metrics.series) == 24
    for point in metrics.series:
        assert isinstance(point, TimeSeriesPoint)
        assert point.total_checks == 0
        assert point.uptime_percentage is None
        assert point.avg_response_time_ms is None


def test_get_monitor_metrics_single_check(db_session, metric_monitor):
    """Verify monitor with 1 check computes percentiles without crash."""
    now = datetime.now(UTC)
    check = CheckResult(
        monitor_id=metric_monitor.id,
        status_code=200,
        response_time_ms=123.45,
        is_successful=True,
        checked_at=now - timedelta(minutes=10),
    )
    db_session.add(check)
    db_session.commit()

    metrics = get_monitor_metrics(db=db_session, monitor=metric_monitor, window="24h")
    assert metrics.summary.total_checks == 1
    assert metrics.summary.successful_checks == 1
    assert metrics.summary.failed_checks == 0
    assert metrics.summary.uptime_percentage == 100.0
    assert metrics.summary.avg_response_time_ms == 123.45
    assert metrics.summary.p50_response_time_ms == 123.45
    assert metrics.summary.p95_response_time_ms == 123.45
    assert metrics.summary.p99_response_time_ms == 123.45


def test_get_monitor_metrics_all_failed(db_session, metric_monitor):
    """Verify monitor with all failed checks returns 0.0% uptime and None for latencies."""
    now = datetime.now(UTC)
    for i in range(5):
        check = CheckResult(
            monitor_id=metric_monitor.id,
            status_code=500,
            response_time_ms=100.0,
            is_successful=False,
            checked_at=now - timedelta(minutes=i * 5),
        )
        db_session.add(check)
    db_session.commit()

    metrics = get_monitor_metrics(db=db_session, monitor=metric_monitor, window="24h")
    assert metrics.summary.total_checks == 5
    assert metrics.summary.successful_checks == 0
    assert metrics.summary.failed_checks == 5
    assert metrics.summary.uptime_percentage == 0.0
    assert metrics.summary.avg_response_time_ms is None
    assert metrics.summary.p50_response_time_ms is None
    assert metrics.summary.p95_response_time_ms is None
    assert metrics.summary.p99_response_time_ms is None


def test_get_monitor_metrics_mixed_percentiles(db_session, metric_monitor):
    """Verify percentiles and uptime percentage calculation with mixed results."""
    now = datetime.now(UTC)
    # Add 100 successful checks with ascending response times: 1.0 to 100.0
    for i in range(1, 101):
        check = CheckResult(
            monitor_id=metric_monitor.id,
            status_code=200,
            response_time_ms=float(i),
            is_successful=True,
            checked_at=now - timedelta(minutes=i),
        )
        db_session.add(check)

    # Add 25 failed checks
    for i in range(25):
        fail_check = CheckResult(
            monitor_id=metric_monitor.id,
            status_code=503,
            response_time_ms=0.0,
            is_successful=False,
            checked_at=now - timedelta(minutes=101 + i),
        )
        db_session.add(fail_check)
    db_session.commit()

    metrics = get_monitor_metrics(db=db_session, monitor=metric_monitor, window="24h")
    assert metrics.summary.total_checks == 125
    assert metrics.summary.successful_checks == 100
    assert metrics.summary.failed_checks == 25
    # Uptime % = (100 / 125) * 100 = 80.0%
    assert metrics.summary.uptime_percentage == 80.0

    # Average = 50.5
    assert metrics.summary.avg_response_time_ms == 50.5
    # Median / p50 ≈ 50.5
    assert 50.0 <= metrics.summary.p50_response_time_ms <= 51.0
    # p95 ≈ 95.0
    assert 94.0 <= metrics.summary.p95_response_time_ms <= 96.0
    # p99 ≈ 99.0
    assert 98.0 <= metrics.summary.p99_response_time_ms <= 100.0


def test_get_monitor_metrics_window_filtering(db_session, metric_monitor):
    """Verify checks older than the window cutoff are strictly excluded."""
    now = datetime.now(UTC)
    # Check within 24h
    recent = CheckResult(
        monitor_id=metric_monitor.id,
        status_code=200,
        response_time_ms=50.0,
        is_successful=True,
        checked_at=now - timedelta(hours=2),
    )
    # Check 2 days old (outside 24h, inside 7d)
    two_days_ago = CheckResult(
        monitor_id=metric_monitor.id,
        status_code=200,
        response_time_ms=100.0,
        is_successful=True,
        checked_at=now - timedelta(days=2),
    )
    # Check 10 days old (outside 7d, inside 30d)
    ten_days_ago = CheckResult(
        monitor_id=metric_monitor.id,
        status_code=200,
        response_time_ms=200.0,
        is_successful=True,
        checked_at=now - timedelta(days=10),
    )
    db_session.add_all([recent, two_days_ago, ten_days_ago])
    db_session.commit()

    m_24h = get_monitor_metrics(db=db_session, monitor=metric_monitor, window="24h")
    assert m_24h.summary.total_checks == 1
    assert len(m_24h.series) == 24

    m_7d = get_monitor_metrics(db=db_session, monitor=metric_monitor, window="7d")
    assert m_7d.summary.total_checks == 2
    assert len(m_7d.series) == 7

    m_30d = get_monitor_metrics(db=db_session, monitor=metric_monitor, window="30d")
    assert m_30d.summary.total_checks == 3
    assert len(m_30d.series) == 30
