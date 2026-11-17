# Phase 1: Database Models & Core Monitor CRUD Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish the working Python 3.13 backend environment, implement the core SQLAlchemy models with SQLite/PostgreSQL duality, and build the first test-driven CRUD API for API Monitors (`/api/v1/monitors`).

**Architecture:** Layered architecture adhering to Ponytail's minimalist constraints. FastAPI routes handle HTTP serialization and dispatch to pure service functions; SQLAlchemy 2.0 declarative models manage persistence; Pydantic v2 schemas enforce request/response validation.

**Tech Stack:** Python 3.13, FastAPI, SQLAlchemy 2.0, Pydantic v2, Pytest, HTTPX.

**Spec:** [docs/requirements.md](docs/requirements.md), [docs/database.md](docs/database.md), [docs/architecture.md](docs/architecture.md).

## Global Constraints
- Minimalist engineering (Ponytail): zero unnecessary dependencies, no premature abstractions.
- Database agnostic for local development: SQLite for zero-setup local dev (`sqlite:///./sentinel.db`), PostgreSQL-ready.
- API Route Prefix: `/api/v1/`.
- Strict typing on all Python functions.
- 100% test pass rate via Pytest before completion.

## Review Focus
1. **Invalid URL Input**: Reject non-HTTP/HTTPS URLs at schema validation before touching DB.
2. **Negative/Zero Intervals**: Reject interval <= 0 and timeout <= 0.
3. **Database Null Constraints**: Ensure foreign keys and non-nullable fields fail gracefully rather than crashing server with unhandled 500.
4. **Cascade Deletes**: Deleting a monitor must cascade delete its check results and incidents.
5. **Session Leakage**: Database sessions must properly close on every request via FastAPI dependency injection.

---

### Task 1: Environment Setup & Core Dependencies

**Files:**
- Create: `backend/venv` (directory via `python -m venv`)
- Modify: `backend/requirements.txt`
- Modify: `backend/.env.example`
- Create: `backend/.env`
- Test: `backend/tests/test_health.py`

**Steps:**
- [x] Refine `backend/requirements.txt` to ensure clean compatibility with Python 3.13.
- [x] Create Python virtual environment: `python -m venv backend/venv`.
- [x] Install dependencies into the virtual environment using `backend/venv/Scripts/pip install -r backend/requirements.txt`.
- [x] Create `backend/.env` with local SQLite default: `DATABASE_URL=sqlite:///./sentinel.db`.
- [x] Write a test in `backend/tests/test_health.py` validating `GET /health`.
- [x] Run test using `pytest` to confirm virtual environment and FastAPI app run cleanly.
- [x] Commit changes.

---

### Task 2: SQLAlchemy Models

**Files:**
- Create: `backend/app/models/user.py`
- Create: `backend/app/models/monitor.py`
- Create: `backend/app/models/check_result.py`
- Create: `backend/app/models/incident.py`
- Modify: `backend/app/models/__init__.py`
- Test: `backend/tests/test_models.py`

**Steps:**
- [x] Write tests in `backend/tests/test_models.py` verifying model creation, defaults, and foreign key cascades.
- [x] Run `pytest backend/tests/test_models.py` to confirm failure (Red).
- [x] Implement `backend/app/models/user.py` (id, email, username, hashed_password, is_active, role, timestamps).
- [x] Implement `backend/app/models/monitor.py` (id, user_id, name, url, http_method, interval_seconds, timeout_seconds, expected_status_code, headers, body, is_active, timestamps).
- [x] Implement `backend/app/models/check_result.py` and `backend/app/models/incident.py`.
- [x] Register all models in `backend/app/models/__init__.py`.
- [x] Run `pytest backend/tests/test_models.py` and confirm all tests pass (Green).
- [x] Commit changes.

---

### Task 3: Pydantic Schemas

**Files:**
- Create: `backend/app/schemas/monitor.py`
- Create: `backend/app/schemas/common.py`
- Test: `backend/tests/test_schemas.py`

**Steps:**
- [x] Write schema validation tests in `backend/tests/test_schemas.py` testing invalid URLs, interval bounds, and serialization.
- [x] Run `pytest backend/tests/test_schemas.py` to confirm failure (Red).
- [x] Implement `backend/app/schemas/monitor.py`:
  - `MonitorBase`: URL, name, method, interval, timeout, expected status code.
  - `MonitorCreate`: Required fields with Pydantic `HttpUrl` or custom URL validator.
  - `MonitorUpdate`: Optional fields.
  - `MonitorResponse`: Full serialization schema with `from_attributes = True`.
- [x] Run `pytest backend/tests/test_schemas.py` to confirm tests pass (Green).
- [x] Commit changes.

---

### Task 4: Monitor CRUD Service & API Endpoints

**Files:**
- Create: `backend/app/services/monitor_service.py`
- Create: `backend/app/api/v1/endpoints/monitors.py`
- Create: `backend/app/api/v1/router.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_api_monitors.py`

**Steps:**
- [x] Write integration tests in `backend/tests/test_api_monitors.py` covering:
  - `POST /api/v1/monitors` (Create monitor)
  - `GET /api/v1/monitors` (List monitors)
  - `GET /api/v1/monitors/{id}` (Get single monitor)
  - `PATCH /api/v1/monitors/{id}` (Update monitor)
  - `DELETE /api/v1/monitors/{id}` (Delete monitor)
  - `404 Not Found` for non-existent IDs.
- [x] Run `pytest backend/tests/test_api_monitors.py` to confirm failure (Red).
- [x] Implement `backend/app/services/monitor_service.py` with standalone helper functions (Ponytail style).
- [x] Implement `backend/app/api/v1/endpoints/monitors.py`.
- [x] Aggregate endpoints in `backend/app/api/v1/router.py` and mount in `backend/app/main.py`.
- [x] Run `pytest` to confirm all integration tests pass (Green).
- [x] Commit changes.

---

### Task 5: Quality Gate & Code Review Checkpoint

**Files:**
- All modified backend files

**Steps:**
- [x] Run full Pytest test suite across all tests.
- [x] Check code formatting and static safety.
- [x] Review changes using CodeRabbit and SonarQube rules.
- [x] Final commit for Phase 1 Milestone.
