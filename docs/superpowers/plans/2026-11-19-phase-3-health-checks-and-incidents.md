# Phase 3: Health Check Engine, Background Worker & Incident Detection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the automated health check engine, manual check trigger, check result history, consecutive failure incident state machine, and background scheduler for API Sentinel.

**Architecture:** Layered asynchronous architecture adhering to Ponytail minimalist constraints. An asynchronous HTTP probe service powered by native `httpx.AsyncClient` executes probes with millisecond latency timing and retry logic; check results are persisted to `check_results` in dedicated sessions; an incident state machine evaluates consecutive check outcomes to automatically transition incidents between open and resolved states; and an in-process asynchronous scheduler runs background checks for active monitors inside FastAPI's lifespan without requiring heavyweight external broker infrastructure in development.

**Tech Stack:** Python 3.13, FastAPI, httpx (async client), SQLAlchemy 2.0, Pydantic v2, Pytest, Pytest-Asyncio.

**Spec:** [docs/requirements.md](docs/requirements.md), [docs/architecture.md](docs/architecture.md), [docs/database.md](docs/database.md).

## Global Constraints

- **Minimalist engineering (Ponytail):** Native `httpx.AsyncClient` with zero unneeded third-party wrappers.
- **Dual execution modes:** Works out-of-the-box with local SQLite (`sentinel.db`) in an async task loop while maintaining clean separation for Celery/Redis deployment in production.
- **Strict Multi-Tenant Isolation:** Users can only trigger checks, inspect check history, or view/acknowledge incidents for monitors they own. All `Incident` queries must join `Monitor` on `Incident.monitor_id == Monitor.id` filtered by `Monitor.user_id == current_user.id`.
- **Accurate Timing:** Latency measured using `time.perf_counter()` in milliseconds rounded to 2 decimal places.
- **Safe Network Probe Defaults:** Requests enforce timeout limits, disallow dangerous unconfigured internal redirects, and gracefully capture all network/DNS/timeout errors into `CheckResult.error_message`.
- **Schema Parity:** No unmigrated columns added to `Monitor` or `Incident`. All queries strictly respect `docs/database.md`.
- **100% Test Pass Rate & High Coverage:** Full pytest suite passes with $\ge 90\%$ test coverage before milestone completion.

## Review Focus

1. **Network Failure Resilience (NFR-021):** Probe execution retries once after 1s backoff on initial network/timeout failure before recording failure; unresolvable DNS, connection timeouts, or TCP resets are caught, logging `status_code=None`, `is_successful=False`, and the error in `CheckResult.error_message`.
2. **Consecutive Threshold & Flapping Guards:** Verify incident transitions strictly adhere to the $N=3$ threshold — 2 failures must NOT trigger an incident; 1 pass after 2 failures resets the consecutive failure counter. If an incident is already `open` or `acknowledged`, subsequent failed checks do not create duplicate incidents.
3. **Auto-Resolution Parity:** When a monitor with an open/acknowledged incident succeeds $N=3$ consecutive times, the incident is marked `resolved`, timestamped with `resolved_at`, and an `IncidentEvent` is generated.
4. **Data Isolation Across Tenants:** A user cannot view, trigger checks, or acknowledge incidents for another user's monitor (`404 Not Found`).
5. **Database Session & Concurrency Safety:** Asynchronous background worker tasks open and close scoped database sessions (`SessionLocal()`) per check execution to prevent SQLite database locks or leaked connections.

---

### Task 1: Check Execution Service & HTTP Probe Engine (with Single Retry)

**Files:**
- Create: `backend/app/schemas/check_result.py`
- Create: `backend/app/services/check_service.py`
- Modify: `backend/app/schemas/__init__.py`
- Test: `backend/tests/test_check_service.py`

**Interfaces:**
- `CheckExecutionResult(status_code: int | None, response_time_ms: float, is_successful: bool, error_message: str | None)`
- `CheckResultResponse` Pydantic v2 schema matching `backend/app/models/check_result.py`.
- `execute_http_probe(url: str, method: str, headers: dict | None, body: dict | None, timeout_seconds: int, expected_status_code: int) -> CheckExecutionResult`:
  - Executes probe via `httpx.AsyncClient`.
  - Captures `httpx.ConnectTimeout`, `httpx.ReadTimeout`, `httpx.ConnectError` (DNS failure), `httpx.RemoteProtocolError`.
  - If initial attempt fails, retries once after 1s backoff per NFR-021 before concluding failure.
  - Returns `CheckExecutionResult`.
- `record_check_result(db: Session, monitor_id: uuid.UUID, result: CheckExecutionResult) -> CheckResult`
- `run_monitor_check(db: Session, monitor: Monitor) -> CheckResult`

**Steps:**
- [ ] Step 1.1: Write failing unit tests in `backend/tests/test_check_service.py` mocking `httpx.AsyncClient` for:
  - 200 OK matching expected status.
  - Status mismatch (e.g. 503 vs expected 200).
  - Timeout and retry behavior (initial fail $\to$ retry success; initial fail $\to$ retry fail).
  - Network/DNS error recording `status_code=None`, `is_successful=False`, non-empty `error_message`.
- [ ] Step 1.2: Run pytest to confirm failure (RED).
- [ ] Step 1.3: Create `backend/app/schemas/check_result.py` with `CheckResultResponse` and `CheckExecutionResult`.
- [ ] Step 1.4: Implement `backend/app/services/check_service.py` with `execute_http_probe`, `record_check_result`, and `run_monitor_check`.
- [ ] Step 1.5: Register `CheckResultResponse` in `backend/app/schemas/__init__.py`.
- [ ] Step 1.6: Run pytest to verify all check service tests pass (GREEN).
- [ ] Step 1.7: Run `ruff check backend` and format.
- [ ] Step 1.8: Commit Task 1: `feat(checks): implement async HTTP probe engine with retry and result recorder`.

---

### Task 2: Manual Check Trigger & Filtered Check History Endpoints (FR-032)

**Files:**
- Modify: `backend/app/api/v1/endpoints/monitors.py`
- Test: `backend/tests/test_api_checks.py`

**Interfaces:**
- `POST /api/v1/monitors/{id}/check`: Triggers immediate health check for owned monitor, returns `CheckResultResponse`. Unauthorized user receives `404 Not Found`.
- `GET /api/v1/monitors/{id}/checks`: Returns paginated `PaginatedResponse[CheckResultResponse]` with query parameters:
  - `is_successful: bool | None = None`
  - `from_date: datetime | None = None`
  - `to_date: datetime | None = None`
  - `page: int = 1`, `page_size: int = 50`

**Steps:**
- [ ] Step 2.1: Write failing API integration tests in `backend/tests/test_api_checks.py` testing:
  - Manual trigger on owned monitor.
  - History filtering by `is_successful=True/False`.
  - History filtering by `from_date` and `to_date`.
  - Pagination mechanics (`page`, `page_size`, `total`).
  - Cross-user 404 isolation (User B cannot check or view User A's monitor).
  - Unauthenticated 401 rejection.
- [ ] Step 2.2: Run pytest to confirm failure (RED).
- [ ] Step 2.3: Implement `POST /api/v1/monitors/{id}/check` in `backend/app/api/v1/endpoints/monitors.py`.
- [ ] Step 2.4: Implement `GET /api/v1/monitors/{id}/checks` with filter query parameters in `backend/app/api/v1/endpoints/monitors.py`.
- [ ] Step 2.5: Run pytest to verify API check endpoints pass (GREEN).
- [ ] Step 2.6: Run `ruff check backend` and format.
- [ ] Step 2.7: Commit Task 2: `feat(api): add manual check trigger and filtered historical checks endpoints`.

---

### Task 3: Incident Detection State Machine (Flapping & Auto-Resolve Guards)

**Files:**
- Create: `backend/app/schemas/incident.py`
- Create: `backend/app/services/incident_service.py`
- Modify: `backend/app/services/check_service.py` (call incident evaluation after check)
- Modify: `backend/app/schemas/__init__.py`
- Test: `backend/tests/test_incident_service.py`

**Interfaces:**
- `IncidentResponse`, `IncidentEventResponse`, and `IncidentUpdate` schemas.
- `evaluate_monitor_incidents(db: Session, monitor_id: uuid.UUID, latest_check: CheckResult, threshold: int = 3) -> Incident | None`:
  - Queries recent check results ordered by `checked_at.desc()` up to threshold count.
  - Checks if an active incident exists (`status IN ('open', 'acknowledged')`).
  - Creation: If $N$ consecutive checks are failed and NO active incident exists $\to$ create `Incident(status="open", cause="consecutive_failures")` and `IncidentEvent(event_type="incident_created")`.
  - Idempotency: If $N$ consecutive checks are failed but an active incident already exists $\to$ NO duplicate incident created.
  - Auto-Resolution: If active incident exists and latest $N$ consecutive checks are successful $\to$ transition active incident to `status="resolved"`, set `resolved_at=now()`, and record `IncidentEvent(event_type="incident_resolved")`.
  - Flapping reset: Any successful check resets failure counter; any failed check resets recovery counter.

**Steps:**
- [ ] Step 3.1: Write failing unit tests in `backend/tests/test_incident_service.py` verifying:
  - 1-2 failures do not open an incident.
  - 3 consecutive failures open an incident with `incident_created` event.
  - 4th consecutive failure does not create duplicate incident.
  - 1 pass after 2 fails resets failure counter.
  - 2 passes do not resolve open incident.
  - 3 consecutive passes auto-resolve open incident with `incident_resolved` event.
- [ ] Step 3.2: Run pytest to confirm failure (RED).
- [ ] Step 3.3: Implement `backend/app/schemas/incident.py`.
- [ ] Step 3.4: Implement `backend/app/services/incident_service.py`.
- [ ] Step 3.5: Hook `evaluate_monitor_incidents` into `check_service.py:run_monitor_check`.
- [ ] Step 3.6: Run pytest to confirm incident service tests pass (GREEN).
- [ ] Step 3.7: Run `ruff check backend` and format.
- [ ] Step 3.8: Commit Task 3: `feat(incidents): implement consecutive failure incident state machine and auto-resolution`.

---

### Task 4: Incident Management API Endpoints & Multi-Tenant Join

**Files:**
- Create: `backend/app/api/v1/endpoints/incidents.py`
- Modify: `backend/app/api/v1/router.py` (mount `/incidents`)
- Test: `backend/tests/test_api_incidents.py`

**Interfaces:**
- `GET /api/v1/incidents`: List user's incidents with optional query filter `status` (`open`, `acknowledged`, `resolved`).
  - Query: `db.query(Incident).join(Monitor, Incident.monitor_id == Monitor.id).filter(Monitor.user_id == current_user.id)`
- `GET /api/v1/incidents/{id}`: Detailed incident view.
- `GET /api/v1/incidents/{id}/events`: Retrieve incident timeline events (`list[IncidentEventResponse]`).
- `PATCH /api/v1/incidents/{id}` & `PATCH /api/v1/incidents/{id}/acknowledge`: Mark an open incident as `acknowledged`, recording `acknowledged_at=now()` and creating an `IncidentEvent(event_type="incident_acknowledged")`.

**Steps:**
- [ ] Step 4.1: Write failing integration tests in `backend/tests/test_api_incidents.py` for:
  - Listing user incidents with status filter.
  - Retrieving single incident details.
  - Retrieving incident timeline events via `GET /api/v1/incidents/{id}/events`.
  - Acknowledging incident via `PATCH /api/v1/incidents/{id}` and `PATCH /api/v1/incidents/{id}/acknowledge`.
  - Cross-user multi-tenant isolation: User B receives `404 Not Found` for User A's incident.
- [ ] Step 4.2: Run pytest to confirm failure (RED).
- [ ] Step 4.3: Implement `backend/app/api/v1/endpoints/incidents.py` with multi-tenant joins.
- [ ] Step 4.4: Mount router in `backend/app/api/v1/router.py`.
- [ ] Step 4.5: Run pytest to verify all incident endpoints pass (GREEN).
- [ ] Step 4.6: Run `ruff check backend` and format.
- [ ] Step 4.7: Commit Task 4: `feat(api): implement incident listing, timeline events, and acknowledgment endpoints`.

---

### Task 5: Background Scheduler Engine & Lifespan Integration

**Files:**
- Create: `backend/app/workers/scheduler.py`
- Modify: `backend/app/core/config.py` (add `scheduler_enabled: bool = True`, `scheduler_interval_seconds: int = 10`)
- Modify: `backend/app/main.py` (FastAPI `@asynccontextmanager` lifespan integration)
- Test: `backend/tests/test_scheduler.py`

**Interfaces:**
- Correlated subquery in `get_monitors_due_for_check(db: Session, now: datetime) -> list[Monitor]`:
  ```python
  latest_check_subq = (
      db.query(CheckResult.checked_at)
      .filter(CheckResult.monitor_id == Monitor.id)
      .order_by(CheckResult.checked_at.desc())
      .limit(1)
      .correlate(Monitor)
      .scalar_subquery()
  )
  ```
  Selects active monitors where `last_checked IS NULL` OR `now - last_checked >= interval_seconds`.
- `AsyncMonitorScheduler`:
  - `start()`: Launches background `asyncio` task loop running `run_scheduler_tick`.
  - `stop()`: Cleanly cancels task and waits for pending checks.
  - Concurrency safety: Uses `asyncio.Semaphore(10)` and opens an isolated `SessionLocal()` per check to prevent SQLite connection locks.
- `main.py` lifespan:
  - Starts `AsyncMonitorScheduler` on startup if `settings.scheduler_enabled`.
  - Cleanly shuts down on application termination.

**Steps:**
- [ ] Step 5.1: Write failing tests in `backend/tests/test_scheduler.py` testing:
  - Due monitor selection with correlated subquery.
  - Exclusion of inactive monitors (`is_active=False`).
  - Interval adherence (monitors checked recently are omitted).
  - Lifespan startup/shutdown lifecycle.
- [ ] Step 5.2: Run pytest to confirm failure (RED).
- [ ] Step 5.3: Implement `backend/app/workers/scheduler.py`.
- [ ] Step 5.4: Add settings in `backend/app/core/config.py`.
- [ ] Step 5.5: Wire lifespan context manager in `backend/app/main.py`.
- [ ] Step 5.6: Run pytest to verify scheduler tests pass (GREEN).
- [ ] Step 5.7: Run `ruff check backend` and format.
- [ ] Step 5.8: Commit Task 5: `feat(workers): implement monitor background scheduler with FastAPI lifespan integration`.

---

### Task 6: Quality Gate, Coverage Audit & Senior Code Review

**Steps:**
- [ ] Step 6.1: Run full pytest suite with coverage:
  ```bash
  backend\venv\Scripts\pytest --cov=backend/app --cov-report=term-missing backend/tests
  ```
  Ensure 100% pass rate and $\ge 90\%$ line coverage.
- [ ] Step 6.2: Run Ruff lint and format checks:
  ```bash
  backend\venv\Scripts\ruff check backend
  backend\venv\Scripts\ruff format --check backend
  ```
- [ ] Step 6.3: Run Alembic migration drift check:
  ```bash
  cd backend && .\venv\Scripts\alembic check
  ```
- [ ] Step 6.4: Dispatch Senior Code Reviewer subagent for Phase 3 audit.
- [ ] Step 6.5: Commit Task 6 and prepare release merge into `develop`.
