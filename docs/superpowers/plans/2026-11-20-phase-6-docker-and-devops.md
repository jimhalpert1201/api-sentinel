# Phase 6 Implementation Plan: Containerization, Docker Compose & CI/CD Hardening

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Package API Sentinel into production-ready Docker containers, orchestrate the full stack with single-command `docker-compose.yml`, harden the GitHub Actions CI pipeline with frontend build validation, and update platform documentation for release `v1.0.0`.

**Architecture:** 
- **Backend Service:** Dockerized FastAPI application based on `python:3.13-slim` running as non-root `sentinel` user (UID 1000). Automated entrypoint script verifies write permissions on `/app/data`, runs `alembic upgrade head`, optionally seeds accounts, and uses `exec uvicorn` for graceful PID 1 signal forwarding.
- **Frontend Service:** Multi-stage Docker build utilizing `node:20-alpine` for TypeScript/Vite compilation and `nginx:alpine` for static asset serving and reverse proxying `/api/` and `/health` traffic directly to the backend container (eliminating CORS).
- **Orchestration:** Root `docker-compose.yml` linking Frontend, Backend, and persistent volume storage with built-in health checks (`/health`) and `start_period: 15s`.
- **CI/CD:** Multi-job GitHub Actions workflow executing backend linting/pytest (96% coverage gate), frontend compilation (`tsc -b && vite build`), and a strict `ci-gate` aggregator.

**Tech Stack:** Docker, Docker Compose, Nginx, Python 3.13, FastAPI, Node.js 20, Vite, React, GitHub Actions.

**Spec:** [`docs/requirements.md`](file:///c:/Users/User/Documents/Jim/api-sentinel/docs/requirements.md) (NFR-040, NFR-041, NFR-042, NFR-043) and [`docs/architecture.md`](file:///c:/Users/User/Documents/Jim/api-sentinel/docs/architecture.md).

## Global Constraints

- **NFR-040:** All services containerized with Docker.
- **NFR-041:** Full environment launchable with `docker compose up`.
- **NFR-042:** CI pipeline runs tests on every push (backend + frontend).
- **NFR-043:** No paid infrastructure required for development (pure open source).
- Non-root container security: Backend runs as unprivileged user `sentinel` (UID 1000) with write permissions to `/app/data`.
- Local workflow compatibility: Native Windows batch launcher (`run.bat`) must remain untouched and fully operational.
- Frontend routing & ingress: Nginx must support SPA client-side routing via `try_files $uri $uri/ /index.html;` and forward `/health` to backend.

## Review Focus

1. **SQLite volume directory permissions in container:** Non-root user `sentinel` must have write permissions to `/app/data` to create and write `sentinel.db` and `-wal` / `-shm` locks.
2. **Nginx SPA fallback & Reverse Proxy:** Direct navigation or browser refresh on `/monitors/:id` or `/incidents` must not return 404; `/api/` and `/health` must proxy to backend without URL strip errors.
3. **Container Healthcheck Ordering:** Backend health check must use `start_period: 15s` so migrations finish before healthcheck retries fail; frontend waits for `condition: service_healthy`.
4. **PID 1 Signal Handling:** `entrypoint.sh` must use `exec uvicorn` so Docker stop signals (`SIGTERM`) reach Uvicorn and FastAPI lifespan handlers cleanly.
5. **CI Matrix Completeness:** GitHub Actions must validate both Python 3.13 backend and Node.js 20 frontend builds with working directories and dependency caching properly scoped.

---

## Tasks

### Task 1: Backend Dockerization & Automated Migration Entrypoint

**Files:**
- Create: `backend/Dockerfile`
- Create: `backend/entrypoint.sh`
- Create: `backend/.dockerignore`
- Modify: `backend/.env.example`

- [ ] **Step 1.1**: Create `backend/.dockerignore` to ignore `venv/`, `__pycache__/`, `.pytest_cache/`, `*.db`, and test artifacts.
- [ ] **Step 1.2**: Create `backend/entrypoint.sh`:
  - Verify write access to `/app/data`.
  - Run `alembic upgrade head`.
  - Optionally run `python scripts/seed_users.py` if `SEED_SAMPLE_USERS=true`.
  - Use `exec uvicorn app.main:app --host 0.0.0.0 --port 8000` for PID 1 signal forwarding.
- [ ] **Step 1.3**: Create `backend/Dockerfile`:
  - Base: `python:3.13-slim`.
  - Install runtime dependencies: `curl`.
  - Create non-root user `sentinel` (UID 1000), directory `/app/data` with 775 permissions.
  - Install dependencies from `requirements.txt`.
  - Copy app code, sanitize CRLF on `entrypoint.sh` via `sed -i 's/\r$//'`, and set executable bits.
  - `USER sentinel`, `EXPOSE 8000`, `ENTRYPOINT ["/app/entrypoint.sh"]`.
- [ ] **Step 1.4**: Update `backend/.env.example` with container defaults (`DATABASE_URL=sqlite:////app/data/sentinel.db`).
- [ ] **Step 1.5**: Verify line endings and execute commit for Task 1.

---

### Task 2: Frontend Multi-Stage Dockerization & Nginx Reverse Proxy

**Files:**
- Create: `frontend/nginx.conf`
- Create: `frontend/Dockerfile`
- Create: `frontend/.dockerignore`

- [ ] **Step 2.1**: Create `frontend/.dockerignore` ignoring `node_modules/`, `dist/`, `.git/`, and npm logs.
- [ ] **Step 2.2**: Create `frontend/nginx.conf`:
  - Gzip compression and security headers.
  - Immutable asset caching for `/assets/`.
  - Reverse proxy for `/api/` to `http://backend:8000`.
  - Reverse proxy for `/health` to `http://backend:8000/health`.
  - SPA routing: `location / { try_files $uri $uri/ /index.html; add_header Cache-Control "no-cache"; }`.
- [ ] **Step 2.3**: Create `frontend/Dockerfile`:
  - Stage 1: `node:20-alpine` runs `npm ci` and `npm run build`.
  - Stage 2: `nginx:alpine` copies `dist/` and `nginx.conf`.
  - Expose port 80.
- [ ] **Step 2.4**: Verify frontend build succeeds locally (`npm run build`).
- [ ] **Step 2.5**: Commit Task 2.

---

### Task 3: Production Docker Compose Orchestration

**Files:**
- Create: `docker-compose.yml`
- Create: `.env.docker.example`
- Modify: `.gitignore`

- [ ] **Step 3.1**: Create `docker-compose.yml`:
  - Service `backend`:
    - `build: ./backend`
    - Ports: `"8000:8000"`
    - Environment variables (`DATABASE_URL=sqlite:////app/data/sentinel.db`, `SEED_SAMPLE_USERS=true`, etc.).
    - Volume: `sentinel_data:/app/data`.
    - Healthcheck with `start_period: 15s`.
  - Service `frontend`:
    - `build: ./frontend`
    - Ports: `"3000:80"`
    - Depends on `backend` with `condition: service_healthy`.
  - Named Volume: `sentinel_data`.
- [ ] **Step 3.2**: Create `.env.docker.example` and ensure `.env.docker` is in `.gitignore`.
- [ ] **Step 3.3**: Commit Task 3.

---

### Task 4: GitHub Actions CI Pipeline Hardening

**Files:**
- Modify: `.github/workflows/ci.yml`

- [ ] **Step 4.1**: Upgrade `.github/workflows/ci.yml` to dual-job pipeline:
  - Job `backend-ci`: Python 3.13, Ruff lint, Ruff format, Pytest coverage ($\ge 90\%$), Alembic check.
  - Job `frontend-ci`: Node 20, scoped cache dependency `frontend/package-lock.json`, working-directory `frontend`, `npm ci`, `tsc -b`, `npm run build`.
  - Job `ci-gate`: Downstream aggregator with `if: always()` and strict exit failure if either job fails.
- [ ] **Step 4.2**: Verify YAML schema and commit Task 4.

---

### Task 5: Documentation & Release Overhaul (`README.md`)

**Files:**
- Modify: `README.md`

- [ ] **Step 5.1**: Overhaul `README.md`:
  - Add production status badges.
  - Complete features checklist (100% completed across all 5 phases).
  - Multi-mode Getting Started guide (One-click batch, Docker Compose, Manual dev).
  - Document pre-seeded RBAC credentials and Sonner observability architecture.
- [ ] **Step 5.2**: Commit Task 5.

---

### Task 6: Verification, Scope Checker & Pull Request Description

**Files:**
- Create: `docs/devops/scope-checker-phase-6.md`
- Create: `docs/devops/pr-phase-6-docker-and-devops.md`

- [ ] **Step 6.1**: Run full backend test suite (`pytest tests/`) to confirm 130/130 passing tests.
- [ ] **Step 6.2**: Run full frontend production build (`npm run build`) to confirm clean bundle output.
- [ ] **Step 6.3**: Author `docs/devops/scope-checker-phase-6.md` (Traceability matrix for NFR-040, NFR-041, NFR-042, NFR-043, scope creep and omission audit).
- [ ] **Step 6.4**: Author `docs/devops/pr-phase-6-docker-and-devops.md` (Pre-commit safety verification & complete PR template).
- [ ] **Step 6.5**: Commit Task 6 and push branch `feature/phase-6-docker-devops` to `origin`.
