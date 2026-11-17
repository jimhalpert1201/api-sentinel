# API Sentinel

**Full-stack API monitoring and observability platform.**

Monitor your APIs, track uptime and latency, detect failures, and manage incidents — all from a single dashboard.

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | React, TypeScript |
| **Backend** | Python, FastAPI, Pydantic |
| **Database** | PostgreSQL, SQLAlchemy, Alembic |
| **Background Jobs** | Redis, Celery |
| **DevOps** | Docker, Docker Compose, GitHub Actions |
| **Testing** | Pytest |

## Features

- [x] Project scaffolding & engineering guidelines
- [x] Core database models (User, Monitor, CheckResult, Incident) with SQLite/PostgreSQL duality
- [x] API monitor management (CRUD endpoints with user data isolation)
- [x] Alembic schema migrations (`backend/alembic/`)
- [ ] User registration & authentication (JWT + refresh tokens) — *In Progress (Phase 2)*
- [ ] Automated health checks with configurable intervals
- [ ] Response time & uptime tracking
- [ ] Incident detection & management
- [ ] Monitoring dashboard (React)
- [ ] Role-based access control
- [ ] Anomaly detection
- [ ] Webhook notifications

## Getting Started

### Prerequisites

- Python 3.13+
- PostgreSQL 15+ (optional for local dev; SQLite is enabled by default)
- Redis 7+
- Node.js 18+ (for frontend)

### Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/macOS
pip install -r requirements.txt
cp .env.example .env         # Edit with your database credentials
alembic upgrade head         # Run database migrations
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.
API docs at `http://localhost:8000/docs`.

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The dashboard will be available at `http://localhost:5173`.

## Project Structure

```
api-sentinel/
├── backend/              # FastAPI application
│   ├── app/
│   │   ├── api/v1/       # API route handlers
│   │   ├── auth/         # Authentication logic
│   │   ├── core/         # Config, database, dependencies
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # Business logic
│   │   ├── workers/      # Background tasks
│   │   └── main.py       # Application entry point
│   ├── tests/            # Test suite
│   └── alembic/          # Database migrations
├── frontend/             # React + TypeScript dashboard
├── infrastructure/       # Docker configs
├── docs/                 # Project documentation
└── .github/workflows/    # CI/CD pipelines
```

## Documentation

- [Requirements](docs/requirements.md)
- [Architecture](docs/architecture.md)
- [Database Design](docs/database.md)

## Current Status

- 🟢 **Phase 1 Complete:** Software Engineering Fundamentals, Database Models, Alembic Migrations, and Monitor CRUD (27/27 tests passing, 99% coverage).
- 🟡 **Phase 2 In Progress:** JWT Authentication & User Management.

## License

[MIT](LICENSE)
