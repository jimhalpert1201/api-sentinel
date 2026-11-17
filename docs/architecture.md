# API Sentinel — Architecture

## 1. System Overview

API Sentinel follows a layered architecture with four main components:

1. **React Frontend** — Single-page application (dashboard)
2. **FastAPI Backend** — REST API server handling business logic
3. **Background Workers** — Celery workers executing scheduled health checks
4. **Data Stores** — PostgreSQL (primary) + Redis (queue & cache)

```
┌─────────────────┐         ┌──────────────────────────────────┐
│                  │  HTTP   │           FastAPI Backend         │
│  React Frontend  │◄───────►│                                  │
│  (TypeScript)    │  REST   │  ┌──────┐  ┌────────┐  ┌──────┐ │
│                  │         │  │ Auth │  │Services│  │ API  │ │
└─────────────────┘         │  └──────┘  └────────┘  └──────┘ │
                            └──────────┬──────────┬────────────┘
                                       │          │
                              ┌────────▼──┐  ┌────▼─────┐
                              │PostgreSQL │  │  Redis   │
                              │  (Data)   │  │ (Queue)  │
                              └───────────┘  └────┬─────┘
                                                  │
                                          ┌───────▼────────┐
                                          │ Celery Workers  │
                                          │ (Health Checks) │
                                          └────────────────┘
```

---

## 2. Backend Architecture

The backend follows a **layered architecture** pattern:

```
Request
  │
  ▼
┌─────────────────────┐
│  API Layer          │  Routes, request/response handling
│  (app/api/v1/)      │  Depends on: Schemas, Services
├─────────────────────┤
│  Schema Layer       │  Pydantic models for validation
│  (app/schemas/)     │  Pure data contracts
├─────────────────────┤
│  Service Layer      │  Business logic
│  (app/services/)    │  Depends on: Models, Schemas
├─────────────────────┤
│  Model Layer        │  SQLAlchemy ORM models
│  (app/models/)      │  Database table definitions
├─────────────────────┤
│  Core Layer         │  Config, database, dependencies
│  (app/core/)        │  Shared infrastructure
└─────────────────────┘
```

**Key principle:** Each layer only depends on the layers below it. API handlers never touch the database directly — they go through services.

---

## 3. API Route Map

All routes are prefixed with `/api/v1`.

### Authentication

| Method | Path | Description | Auth |
|---|---|---|---|
| POST | `/auth/register` | Create a new user | No |
| POST | `/auth/login` | Authenticate and get tokens | No |
| POST | `/auth/refresh` | Refresh an access token | Refresh token |
| POST | `/auth/logout` | Invalidate refresh token | Yes |

### Users

| Method | Path | Description | Auth |
|---|---|---|---|
| GET | `/users/me` | Get current user profile | Yes |
| PATCH | `/users/me` | Update current user profile | Yes |

### Monitors

| Method | Path | Description | Auth |
|---|---|---|---|
| GET | `/monitors` | List user's monitors | Yes |
| POST | `/monitors` | Create a new monitor | Yes |
| GET | `/monitors/{id}` | Get monitor details | Yes (owner) |
| PATCH | `/monitors/{id}` | Update a monitor | Yes (owner) |
| DELETE | `/monitors/{id}` | Delete a monitor | Yes (owner) |
| POST | `/monitors/{id}/check` | Trigger a manual health check | Yes (owner) |
| GET | `/monitors/{id}/checks` | Get check history | Yes (owner) |

### Incidents

| Method | Path | Description | Auth |
|---|---|---|---|
| GET | `/incidents` | List user's incidents | Yes |
| GET | `/incidents/{id}` | Get incident details | Yes (owner) |
| PATCH | `/incidents/{id}` | Update incident (acknowledge) | Yes (owner) |
| GET | `/incidents/{id}/events` | Get incident timeline | Yes (owner) |

### System

| Method | Path | Description | Auth |
|---|---|---|---|
| GET | `/health` | System health check | No |

---

## 4. Authentication Flow

```
┌────────┐                    ┌─────────┐                 ┌────────┐
│ Client │                    │ FastAPI │                 │   DB   │
└───┬────┘                    └────┬────┘                 └───┬────┘
    │  POST /auth/login            │                          │
    │  {email, password}           │                          │
    │─────────────────────────────►│  Verify credentials      │
    │                              │─────────────────────────►│
    │                              │◄─────────────────────────│
    │                              │  Hash matches?           │
    │  {access_token,              │                          │
    │   refresh_token}             │                          │
    │◄─────────────────────────────│                          │
    │                              │                          │
    │  GET /monitors               │                          │
    │  Authorization: Bearer <at>  │                          │
    │─────────────────────────────►│  Decode JWT              │
    │                              │  Extract user_id         │
    │                              │  Query monitors          │
    │  [monitors]                  │─────────────────────────►│
    │◄─────────────────────────────│◄─────────────────────────│
    │                              │                          │
    │  POST /auth/refresh          │                          │
    │  {refresh_token}             │                          │
    │─────────────────────────────►│  Validate + rotate       │
    │  {new_access_token,          │                          │
    │   new_refresh_token}         │                          │
    │◄─────────────────────────────│                          │
```

---

## 5. Health Check Flow

```
┌───────────┐      ┌───────┐      ┌────────┐      ┌────────┐      ┌────┐
│ Scheduler │      │ Redis │      │ Worker │      │ Target │      │ DB │
└─────┬─────┘      └───┬───┘      └───┬────┘      └───┬────┘      └──┬─┘
      │ Enqueue check   │             │                │              │
      │ (every interval) │             │                │              │
      │────────────────►│             │                │              │
      │                 │  Dequeue    │                │              │
      │                 │────────────►│                │              │
      │                 │             │  HTTP request  │              │
      │                 │             │───────────────►│              │
      │                 │             │  Response      │              │
      │                 │             │◄───────────────│              │
      │                 │             │  Save result   │              │
      │                 │             │───────────────────────────────►│
      │                 │             │  Check incident│              │
      │                 │             │  threshold     │              │
      │                 │             │───────────────────────────────►│
```

---

## 6. Technology Decisions

| Decision | Choice | Rationale |
|---|---|---|
| API framework | FastAPI | Async, auto-docs, type safety, modern |
| ORM | SQLAlchemy 2.0 | Industry standard, Alembic integration |
| Migrations | Alembic | The standard migration tool for SQLAlchemy |
| Auth | JWT (python-jose) + bcrypt | Stateless, scalable |
| Validation | Pydantic v2 | Built into FastAPI, fast, well-typed |
| Config | pydantic-settings | Type-safe `.env` loading |
| Task queue | Celery + Redis | Battle-tested, great monitoring tools |
| Database | PostgreSQL | JSONB support, reliability, free |
| Cache/broker | Redis | Fast, doubles as Celery broker and cache |
| Frontend | React + TypeScript | Dominant combo, type safety |
| HTTP client | React Query (TanStack) | Server-state management, caching, retries |
| Logging | structlog | Structured JSON logs, async-friendly |
| Testing | Pytest + httpx | AsyncClient for testing FastAPI |
| Containerization | Docker + Compose | Universal, reproducible environments |
| CI/CD | GitHub Actions | Free for public repos, tight GitHub integration |

---

## 7. Project Layout

```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── auth.py        # Register, login, refresh, logout
│   │       │   ├── users.py       # User profile
│   │       │   ├── monitors.py    # Monitor CRUD + manual check
│   │       │   ├── incidents.py   # Incident list, detail, acknowledge
│   │       │   └── health.py      # System health endpoint
│   │       └── router.py         # Aggregates all endpoint routers
│   ├── auth/
│   │   ├── dependencies.py       # get_current_user, require_role
│   │   ├── jwt.py                # Token creation and verification
│   │   └── passwords.py          # Hash and verify passwords
│   ├── core/
│   │   ├── config.py             # Settings from environment
│   │   ├── database.py           # SQLAlchemy engine + session
│   │   └── dependencies.py       # Shared FastAPI dependencies
│   ├── models/
│   │   ├── user.py               # User model
│   │   ├── monitor.py            # Monitor model
│   │   ├── check_result.py       # CheckResult model
│   │   ├── incident.py           # Incident model
│   │   └── incident_event.py     # IncidentEvent model
│   ├── schemas/
│   │   ├── user.py               # User request/response schemas
│   │   ├── monitor.py            # Monitor schemas
│   │   ├── check_result.py       # CheckResult schemas
│   │   ├── incident.py           # Incident schemas
│   │   └── common.py             # Shared schemas (pagination, errors)
│   ├── services/
│   │   ├── user_service.py       # User business logic
│   │   ├── monitor_service.py    # Monitor CRUD logic
│   │   ├── check_service.py      # Health check execution
│   │   └── incident_service.py   # Incident detection and management
│   ├── workers/
│   │   ├── celery_app.py         # Celery configuration
│   │   └── tasks.py              # Celery tasks (run_health_check)
│   └── main.py                   # FastAPI application entry point
├── alembic/                      # Database migrations
├── tests/
│   ├── conftest.py               # Test fixtures
│   ├── test_auth.py
│   ├── test_monitors.py
│   └── test_incidents.py
├── alembic.ini
├── requirements.txt
└── .env.example
```
