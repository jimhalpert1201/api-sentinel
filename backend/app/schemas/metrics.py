import uuid
from datetime import datetime

from pydantic import BaseModel


class MetricSummary(BaseModel):
    """Aggregate uptime and latency statistics for a monitor over a given window."""

    total_checks: int
    successful_checks: int
    failed_checks: int
    uptime_percentage: float
    avg_response_time_ms: float | None = None
    p50_response_time_ms: float | None = None
    p95_response_time_ms: float | None = None
    p99_response_time_ms: float | None = None


class TimeSeriesPoint(BaseModel):
    """Chronological time-series bucket for chart rendering."""

    bucket_start: datetime
    bucket_end: datetime
    total_checks: int
    uptime_percentage: float | None = None
    avg_response_time_ms: float | None = None


class MonitorMetricsResponse(BaseModel):
    """Full metrics response containing aggregate summary and chart series."""

    monitor_id: uuid.UUID
    window: str
    summary: MetricSummary
    series: list[TimeSeriesPoint]
