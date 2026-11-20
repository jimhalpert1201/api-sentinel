# 🛡️ API Sentinel

[![CI Pipeline](https://github.com/jimhalpert1201/api-sentinel/actions/workflows/ci.yml/badge.svg)](https://github.com/jimhalpert1201/api-sentinel/actions/workflows/ci.yml)
[![Version](https://img.shields.io/badge/version-v1.0.0-emerald.svg)](https://github.com/jimhalpert1201/api-sentinel/releases)
[![Python](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/react-18-61dafb.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/typescript-5.6-3178c6.svg)](https://www.typescriptlang.org/)
[![Tests](https://img.shields.io/badge/tests-130%20passed-success.svg)](https://docs.pytest.org/)
[![License](https://img.shields.io/badge/license-MIT-purple.svg)](LICENSE)

**API Sentinel** is an enterprise-grade, zero-cost full-stack API monitoring, telemetry, and incident observability platform. Monitor target endpoints, capture sub-millisecond latency percentiles, automate outage detection, dispatch webhook notifications, and triage incidents through an Emil Kowalski-inspired dark observability dashboard.

---

## 🌟 Key Capabilities

- **Automated Health Probes**: In-process asynchronous scheduler executing configurable HTTP probes (`interval`, `timeout`, `expected_status_code`, and custom methods).
- **Deep Latency Analytics**: Sliding time-window metrics (`24h`, `7d`, `30d`) computing average latency, `p50`, `p95`, `p99` percentiles, and continuous time-series chart data.
- **Incident Lifecycle Engine**: Automated incident generation after $N$ consecutive check failures, automated resolution upon recovery, audit timeline logging, and in-place operator acknowledgment.
- **Outbound Webhook Dispatcher**: Non-blocking async webhooks delivering structured JSON alert notifications to configured webhook URLs with automated retry on $5\text{xx}$ server errors.
- **Observability Web Dashboard**: Built with React 18, Vite, TypeScript, and Tailwind CSS. Features persistent dark sidebar AppShell (`#0e1526`), real-time Fleet Health Dot Matrix, guided 3-step monitor modal, and expandable diagnostic probe inspector.
- **Micro-Interaction Craft**: Emil Kowalski design engineering principles with [Sonner](https://sonner.emilkowal.ski/) toast notifications, tactile spring physics (`active:scale-[0.97]`), glass rim-lighting (`surface-card`), and stable tabular typography (`tabular-nums`).
- **Resilient Multi-Tenant Auth**: Single-in-flight token refresh mutex with subscriber queuing preventing token family reuse lockouts, password complexity validation, and HTTP 429 rate limit banners.
- **Production Packaging**: Multi-stage Docker containerization, non-root user execution (`sentinel`), Nginx SPA reverse proxy, and single-command Docker Compose orchestration.

---

## 🛠️ Tech Stack

| Layer | Technologies & Architecture |
|---|---|
| **Frontend UI** | React 18, TypeScript, Vite, Tailwind CSS, Recharts, Lucide Icons, Sonner |
| **Backend API** | Python 3.13, FastAPI, Pydantic v2, Uvicorn, Asyncio In-Process Scheduler |
| **ORM & Storage** | SQLAlchemy 2.0, Alembic Migrations, SQLite WAL mode / PostgreSQL Duality |
| **Security & Auth** | JWT Access & Refresh Token Rotation, BCrypt (cost $\ge 12$), RBAC (`admin`, `user`) |
| **Container & Ops** | Docker, Multi-Stage Builds, Nginx Reverse Proxy, Docker Compose |
| **Quality & CI/CD** | Pytest (130 tests, 96% coverage), Ruff (Linter & Formatter), GitHub Actions |

---

## 🚀 Quick Start Guide

You can run API Sentinel using any of the 3 supported modes:

### Mode 1: Docker Compose (Recommended for Production / Containers)

Launch the entire containerized fleet (FastAPI backend + Nginx frontend + persistent SQLite volume) with a single command:

```bash
# 1. Clone repository
git clone https://github.com/jimhalpert1201/api-sentinel.git
cd api-sentinel

# 2. Launch full stack
docker compose up --build -d
```

- **Web Dashboard**: [http://localhost:3000](http://localhost:3000)
- **API Server & Health**: [http://localhost:8000/health](http://localhost:8000/health)
- **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

### Mode 2: One-Click Windows Launcher (`run.bat`)

For Windows workstations with Python and Node.js installed:

```powershell
.\run.bat
```

*The launcher automatically applies Alembic migrations, installs frontend packages on first run, starts the Vite development server in the background, launches FastAPI with hot reload, and opens your browser to `http://localhost:5173`.*

---

### Mode 3: Manual Local Development

#### 1. Backend Server
```bash
cd backend
python -m venv venv
.\venv\Scripts\activate          # Windows
# source venv/bin/activate       # macOS / Linux

pip install -r requirements.txt
alembic upgrade head
python scripts/seed_users.py     # Initialize sample admin & user accounts
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

#### 2. Frontend Development Server
```bash
cd frontend
npm install
npm run dev
```

Visit the dashboard at [http://localhost:5173](http://localhost:5173).

---

## 🔑 Pre-Seeded Test Accounts

When `SEED_SAMPLE_USERS=true` is set (or after running `python backend/scripts/seed_users.py`), the following credentials are ready for testing:

| Role | Username | Email | Default Password | Permissions |
|---|---|---|---|---|
| **Admin** | `admin` | `admin@apisentinel.dev` | `AdminPassword123!` | System-wide observability, all monitors & users |
| **User** | `developer` | `developer@apisentinel.dev` | `UserPassword123!` | Standard tenant: CRUD own monitors & incidents |

---

## 📊 Features & Phase Traceability

- [x] **Phase 1: Core Foundation & Models** — SQLAlchemy 2.0 ORM models (`User`, `Monitor`, `CheckResult`, `Incident`), SQLite/PostgreSQL duality, Alembic schema migrations, and Monitor CRUD endpoints.
- [x] **Phase 2: Authentication & Multi-Tenancy** — JWT access/refresh token rotation, bcrypt password hashing, login rate limiting, and RBAC user permissions.
- [x] **Phase 3: Automated Health Checks & Incidents** — In-process async probe scheduler, manual check trigger, consecutive failure incident creation ($N=3$), auto-recovery, and timeline event audit logs.
- [x] **Phase 4: Analytics & Webhook Alerts** — Sliding window latency percentiles (`p50`, `p95`, `p99`, `avg`), contiguous time-series series data, and resilient outbound webhook alert dispatcher.
- [x] **Phase 5: React Web Dashboard & UI Polish** — Complete React 18 + Vite dashboard, dark observability AppShell, fleet health matrix, guided 3-step modal, diagnostic probe inspector, Sonner toasts, and tactile spring physics.
- [x] **Phase 6: Production Readiness & Containerization** — Multi-stage Dockerfiles, Nginx SPA reverse proxy, `docker-compose.yml` orchestration, and dual-stack GitHub Actions CI pipeline.

---

## 🧪 Testing & Quality Gates

Run backend unit and integration test suite:
```bash
cd backend
.\venv\Scripts\pytest --cov=app --cov-report=term-missing tests/
```
```text
======================= 130 passed in 45.66s =======================
Total Line Coverage: 96%
Ruff Linting: 0 errors
```

Run frontend typecheck and production build:
```bash
cd frontend
npm run build
```
```text
✓ 2250 modules transformed.
✓ built in 4.41s
Exit Code: 0
```

---

## 📂 Project Directory Structure

```text
api-sentinel/
├── backend/                      # FastAPI Python Application
│   ├── alembic/                  # Database migration versions
│   ├── app/
│   │   ├── api/v1/endpoints/     # REST routes (auth, users, monitors, incidents, metrics)
│   │   ├── auth/                 # JWT tokens, password hashing, dependencies
│   │   ├── core/                 # Config, database engine, rate limiter
│   │   ├── models/               # SQLAlchemy ORM entity models
│   │   ├── schemas/              # Pydantic v2 request/response contracts
│   │   └── services/             # Health checker, incident detector, metrics, webhooks
│   ├── scripts/                  # User seeding script (seed_users.py)
│   ├── tests/                    # 130 pytest test suites
│   ├── Dockerfile                # Python 3.13-slim container
│   └── entrypoint.sh             # Auto-migration & Uvicorn startup script
├── frontend/                     # React 18 + Vite Web Dashboard
│   ├── src/
│   │   ├── api/                  # Axios client with refresh mutex & endpoints
│   │   ├── components/           # AppShell, MonitorCard, Modal, Charts, Sonner
│   │   ├── context/              # AuthContext provider
│   │   ├── pages/                # Login, Register, Dashboard, Details, Incidents
│   │   └── types/                # TypeScript interfaces
│   ├── Dockerfile                # Multi-stage build (Node 20 -> Nginx)
│   └── nginx.conf                # SPA routing & /api/ reverse proxy
├── docs/                         # Requirements, architecture, plans & DevOps audits
│   ├── devops/                   # Pre-commit safety checklists & scope checkers
│   └── superpowers/plans/        # Phase implementation plans
├── .github/workflows/ci.yml      # Dual-job backend & frontend CI pipeline
├── docker-compose.yml            # Single-command production stack
└── run.bat                       # One-click Windows development launcher
```

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
