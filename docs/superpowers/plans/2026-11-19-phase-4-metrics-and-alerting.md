# Phase 4 Implementation Plan: Metrics, Analytics & Alerting

- **Branch:** `feature/phase-4-metrics-alerting`
- **Target Release:** `v0.2.0` (Phase 4 Milestone)
- **Base Branch:** `develop` (Commit: `de74125`)
- **Author:** Antigravity Architect

---

## 1. Overview & Objectives

Phase 4 implements the **Metrics & Analytics Engine** and **Incident Alerting via Webhooks** for API Sentinel:
1. **Uptime & Latency Metrics Engine (FR-030, FR-031)**: Calculate overall uptime percentage (24h, 7d, 30d) and latency distribution percentiles (average, p50, p95, p99) dynamically on demand from recorded health checks.
2. **Chart Series Generation (FR-033)**: Generate chronologically contiguous bucketed time-series data points (hourly for 24h, daily for 7d/30d) for frontend charts.
3. **Outbound Incident Webhooks (FR-050, FR-051)**: Dispatch JSON webhook notifications to a monitor's configured `webhook_url` when an incident is created or auto-resolved, using non-blocking async dispatch with single retry resilience.
4. **Multi-Tenant Isolation (NFR-014)**: Guarantee strict access boundaries so users can only view metrics for monitors they own.

---

## 2. Architecture & Data Contracts

### 2.1 Database Migration: Monitor `webhook_url`
- Table: `monitors`
- Column: `webhook_url` (`VARCHAR(2048)`, nullable, default `None`)
- Managed via Alembic revision `add_webhook_url_to_monitors`.

### 2.2 Outbound Webhook Payload Contract
```json
{
  "event": "incident_created | incident_resolved",
  "incident_id": "uuid-string",
  "monitor_id": "uuid-string",
  "monitor_name": "Production API",
  "monitor_url": "https://api.example.com/health",
  "status": "open | resolved",
  "cause": "downtime",
  "started_at": "2026-11-19T10:00:00Z",
  "resolved_at": "2026-11-19T10:15:00Z | null",
  "description": "Monitor failed 3 consecutive checks."
}
```

### 2.3 Metrics Response Contract (`GET /api/v1/monitors/{id}/metrics?window=24h|7d|30d`)
```json
{
  "monitor_id": "uuid-string",
  "window": "24h",
  "summary": {
    "total_checks": 1440,
    "successful_checks": 1437,
    "failed_checks": 3,
    "uptime_percentage": 99.79,
    "avg_response_time_ms": 112.4,
    "p50_response_time_ms": 95.0,
    "p95_response_time_ms": 220.5,
    "p99_response_time_ms": 480.0
  },
  "series": [
    {
      "bucket_start": "2026-11-19T00:00:00Z",
      "bucket_end": "2026-11-19T01:00:00Z",
      "total_checks": 60,
      "uptime_percentage": 100.0,
      "avg_response_time_ms": 105.2
    }
  ]
}
```

---

## 3. Implementation Tasks (Strict TDD)

### Task 1: Database Migration & Schema/Service Update for Monitor `webhook_url`
- [ ] **Step 1.1**: Update `backend/app/models/monitor.py` to add `webhook_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)`.
- [ ] **Step 1.2**: Update `backend/app/schemas/monitor.py`:
  - `MonitorBase`: add `webhook_url: HttpUrl | None = None`
  - `MonitorUpdate`: add `webhook_url: HttpUrl | None = None`
  - `MonitorResponse`: add `webhook_url: str | None = None`
- [ ] **Step 1.2b**: Update `backend/app/services/monitor_service.py`:
  - In `create_monitor`: persist `webhook_url=str(data.webhook_url) if data.webhook_url else None`.
  - In `update_monitor`: if `key == "webhook_url"` and `value is not None`, set `str(value)`.
- [ ] **Step 1.3**: Generate Alembic migration:
  `cd backend && .\venv\Scripts\alembic revision --autogenerate -m "add_webhook_url_to_monitors"`.
- [ ] **Step 1.4**: Apply migration: `cd backend && .\venv\Scripts\alembic upgrade head`.
- [ ] **Step 1.5**: Write integration tests in `backend/tests/test_api_monitors.py` verifying monitor creation, update, and retrieval with `webhook_url`.
- [ ] **Step 1.6**: Run `pytest` and `alembic check` to verify clean migration.
- [ ] **Step 1.7**: Run `ruff check backend` and `ruff format backend`.
- [ ] **Step 1.8**: Commit Task 1.

### Task 2: Outbound Webhook Dispatcher Service & Incident Hook
- [ ] **Step 2.1**: Write unit tests in `backend/tests/test_webhook_service.py`:
  - Webhook dispatch success (200 OK).
  - Webhook retry on 5xx failure with 2s backoff, succeeding on attempt 2.
  - Webhook client error (4xx) is not retried.
  - Webhook failure logging on persistent timeout/connect error (does not raise or break caller).
  - No-op when monitor has no `webhook_url`.
- [ ] **Step 2.2**: Implement `backend/app/schemas/webhook.py`:
  ```python
  class WebhookPayload(BaseModel):
      event: str  # "incident_created" | "incident_resolved"
      incident_id: uuid.UUID
      monitor_id: uuid.UUID
      monitor_name: str
      monitor_url: str
      status: str
      cause: str
      started_at: datetime
      resolved_at: datetime | None = None
      description: str | None = None
  ```
- [ ] **Step 2.3**: Implement `backend/app/services/webhook_service.py`:
  - `async def send_incident_webhook(webhook_url: str, payload: WebhookPayload) -> bool`:
    - `httpx.AsyncClient` with `timeout=5.0`.
    - If status >= 500 or timeout/connect error: sleep 2.0s and retry once. If 4xx, do not retry.
    - Catch all exceptions, log structured warning, and return `False`. Never raise to caller.
  - `def dispatch_incident_webhook_safely(webhook_url: str | None, payload: WebhookPayload) -> None`:
    - If `not webhook_url`: return immediately.
    - Inspect `asyncio.get_running_loop()`. If active, `loop.create_task(send_incident_webhook(...))`. If `RuntimeError`, gracefully pass (protecting sync tests).
- [ ] **Step 2.4**: Connect webhook trigger into `backend/app/services/incident_service.py`:
  - Update `evaluate_monitor_incidents` signature:
    `def evaluate_monitor_incidents(db: Session, monitor_id: uuid.UUID, latest_check: CheckResult, threshold: int = 3, monitor: Monitor | None = None) -> Incident | None:`
  - If `monitor is None`: query `db.query(Monitor).filter_by(id=monitor_id).first()`.
  - On incident creation (`open`): call `dispatch_incident_webhook_safely` with `event="incident_created"`.
  - On incident auto-resolution (`resolved`): call `dispatch_incident_webhook_safely` with `event="incident_resolved"`.
- [ ] **Step 2.5**: Run pytest to verify all webhook service and incident tests pass (GREEN).
- [ ] **Step 2.6**: Run `ruff check backend` and `ruff format backend`.
- [ ] **Step 2.7**: Commit Task 2.

### Task 3: Metrics & Analytics Calculation Service
- [ ] **Step 3.1**: Write failing unit tests in `backend/tests/test_metrics_service.py`:
  - Monitor with 0 checks returns 100.0% uptime and None for all latency fields.
  - Monitor with 1 check returns round(val, 2) for avg, p50, p95, p99 without crashing.
  - Monitor with all failed checks returns 0.0% uptime and None for latencies.
  - Monitor with mixed results calculates accurate percentiles (`p50`, `p95`, `p99`) and uptime.
  - Generates contiguous chronological series of buckets (1-hour bins for 24h, 1-day bins for 7d/30d); empty buckets yield `total_checks=0, uptime_percentage=None, avg_response_time_ms=None`.
- [ ] **Step 3.2**: Implement `backend/app/schemas/metrics.py`:
  ```python
  class MetricSummary(BaseModel):
      total_checks: int
      successful_checks: int
      failed_checks: int
      uptime_percentage: float
      avg_response_time_ms: float | None = None
      p50_response_time_ms: float | None = None
      p95_response_time_ms: float | None = None
      p99_response_time_ms: float | None = None

  class TimeSeriesPoint(BaseModel):
      bucket_start: datetime
      bucket_end: datetime
      total_checks: int
      uptime_percentage: float | None = None
      avg_response_time_ms: float | None = None

  class MonitorMetricsResponse(BaseModel):
      monitor_id: uuid.UUID
      window: str
      summary: MetricSummary
      series: list[TimeSeriesPoint]
  ```
- [ ] **Step 3.3**: Implement `backend/app/services/metrics_service.py`:
  - `get_monitor_metrics(db: Session, monitor: Monitor, window: str = "24h") -> MonitorMetricsResponse`.
  - Dynamic querying of `check_results` filtered by `checked_at >= cutoff`.
  - Normalize timezone to UTC for SQLite/Postgres compatibility.
  - Percentile calculation guards:
    - If 0 successful: `None` for avg/p50/p95/p99.
    - If 1 successful: `round(val, 2)` for avg/p50/p95/p99.
    - If >= 2 successful: `statistics.quantiles(latencies, n=100, method="inclusive")`.
  - Generate contiguous series of buckets from `cutoff` to `now`.
- [ ] **Step 3.4**: Run pytest to verify all metrics calculations pass (GREEN).
- [ ] **Step 3.5**: Run `ruff check backend` and `ruff format backend`.
- [ ] **Step 3.6**: Commit Task 3.

### Task 4: Metrics API Endpoint & Multi-Tenant Authorization
- [ ] **Step 4.1**: Write failing integration tests in `backend/tests/test_api_metrics.py`:
  - `GET /api/v1/monitors/{id}/metrics` defaults to `24h` and returns 200 with summary and series.
  - Validates `window` parameter (accepts `24h`, `7d`, `30d`; rejects invalid window with 422).
  - Multi-tenant security: returns 404 when requesting metrics for another user's monitor.
  - Unauthenticated request returns 401.
- [ ] **Step 4.2**: Implement `GET /api/v1/monitors/{id}/metrics` in `backend/app/api/v1/endpoints/monitors.py`:
  - Endpoint signature:
    ```python
    @router.get("/{id}/metrics", response_model=MonitorMetricsResponse, summary="Get monitor uptime and latency metrics")
    def get_monitor_metrics(
        id: uuid.UUID,
        window: Literal["24h", "7d", "30d"] = Query(default="24h"),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
        monitor = monitor_service.get_monitor(db=db, monitor_id=id, user_id=current_user.id)
        if not monitor:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Monitor not found")
        return metrics_service.get_monitor_metrics(db=db, monitor=monitor, window=window)
    ```
- [ ] **Step 4.3**: Run pytest to verify endpoint tests pass (GREEN).
- [ ] **Step 4.4**: Run `ruff check backend` and `ruff format backend`.
- [ ] **Step 4.5**: Commit Task 4.

### Task 5: Quality Gate & Senior Code Review
- [ ] **Step 5.1**: Run full pytest suite with coverage >= 90%.
- [ ] **Step 5.2**: Run Ruff check and format.
- [ ] **Step 5.3**: Run Alembic migration check.
- [ ] **Step 5.4**: Senior Code Reviewer subagent adversarial audit.
- [ ] **Step 5.5**: Report to user and await explicit confirmation before merging into `develop`.
