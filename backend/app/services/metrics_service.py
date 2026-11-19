import statistics
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.models.check_result import CheckResult
from app.models.monitor import Monitor
from app.schemas.metrics import MetricSummary, MonitorMetricsResponse, TimeSeriesPoint


def get_monitor_metrics(
    db: Session,
    monitor: Monitor,
    window: str = "24h",
) -> MonitorMetricsResponse:
    """
    Calculate dynamic uptime percentage, response time percentiles, and contiguous
    chart series buckets for a given monitor over a sliding time window (24h, 7d, 30d).
    """
    now = datetime.now(UTC)

    # Determine time window cutoff and bucket structure
    if window == "7d":
        cutoff = now - timedelta(days=7)
        bucket_delta = timedelta(days=1)
        num_buckets = 7
    elif window == "30d":
        cutoff = now - timedelta(days=30)
        bucket_delta = timedelta(days=1)
        num_buckets = 30
    else:  # default "24h"
        window = "24h"
        cutoff = now - timedelta(hours=24)
        bucket_delta = timedelta(hours=1)
        num_buckets = 24

    # Query check results within the window
    raw_checks = (
        db.query(
            CheckResult.is_successful,
            CheckResult.response_time_ms,
            CheckResult.checked_at,
        )
        .filter(
            CheckResult.monitor_id == monitor.id,
            CheckResult.checked_at >= cutoff,
        )
        .order_by(CheckResult.checked_at.asc())
        .all()
    )

    # Normalize datetime to UTC for SQLite/Postgres consistency
    checks: list[tuple[bool, float, datetime]] = []
    for c in raw_checks:
        checked_at = c.checked_at
        if checked_at.tzinfo is None:
            checked_at = checked_at.replace(tzinfo=UTC)
        checks.append((c.is_successful, c.response_time_ms, checked_at))

    total_checks = len(checks)
    successful_checks = sum(1 for is_succ, _, _ in checks if is_succ)
    failed_checks = total_checks - successful_checks

    uptime_percentage = (
        round((successful_checks / total_checks) * 100.0, 2) if total_checks > 0 else 100.0
    )

    successful_latencies = [resp_ms for is_succ, resp_ms, _ in checks if is_succ]

    avg_latency: float | None = None
    p50_latency: float | None = None
    p95_latency: float | None = None
    p99_latency: float | None = None

    if len(successful_latencies) == 1:
        val = round(successful_latencies[0], 2)
        avg_latency = val
        p50_latency = val
        p95_latency = val
        p99_latency = val
    elif len(successful_latencies) >= 2:
        avg_latency = round(sum(successful_latencies) / len(successful_latencies), 2)
        quantiles = statistics.quantiles(successful_latencies, n=100, method="inclusive")
        p50_latency = round(quantiles[49], 2)
        p95_latency = round(quantiles[94], 2)
        p99_latency = round(quantiles[98], 2)

    summary = MetricSummary(
        total_checks=total_checks,
        successful_checks=successful_checks,
        failed_checks=failed_checks,
        uptime_percentage=uptime_percentage,
        avg_response_time_ms=avg_latency,
        p50_response_time_ms=p50_latency,
        p95_response_time_ms=p95_latency,
        p99_response_time_ms=p99_latency,
    )

    # Generate contiguous chronological buckets from cutoff to now
    series: list[TimeSeriesPoint] = []
    for i in range(num_buckets):
        b_start = cutoff + (i * bucket_delta)
        b_end = cutoff + ((i + 1) * bucket_delta)

        # In-bucket checks (inclusive of upper bound on the final bucket)
        if i == num_buckets - 1:
            b_checks = [c for c in checks if b_start <= c[2] <= b_end]
        else:
            b_checks = [c for c in checks if b_start <= c[2] < b_end]

        b_total = len(b_checks)
        if b_total == 0:
            series.append(
                TimeSeriesPoint(
                    bucket_start=b_start,
                    bucket_end=b_end,
                    total_checks=0,
                    uptime_percentage=None,
                    avg_response_time_ms=None,
                )
            )
        else:
            b_succ = sum(1 for is_succ, _, _ in b_checks if is_succ)
            b_uptime = round((b_succ / b_total) * 100.0, 2)
            b_succ_lats = [resp_ms for is_succ, resp_ms, _ in b_checks if is_succ]
            b_avg = round(sum(b_succ_lats) / len(b_succ_lats), 2) if b_succ_lats else None

            series.append(
                TimeSeriesPoint(
                    bucket_start=b_start,
                    bucket_end=b_end,
                    total_checks=b_total,
                    uptime_percentage=b_uptime,
                    avg_response_time_ms=b_avg,
                )
            )

    return MonitorMetricsResponse(
        monitor_id=monitor.id,
        window=window,
        summary=summary,
        series=series,
    )
