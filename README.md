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

## Features (Planned)

- [x] Project scaffolding
- [ ] User registration & authentication (JWT + refresh tokens)
- [ ] API monitor management (CRUD)
- [ ] Automated health checks with configurable intervals
- [ ] Response time & uptime tracking
- [ ] Incident detection & management
- [ ] Monitoring dashboard (React)
- [ ] Role-based access control
- [ ] Anomaly detection
- [ ] Webhook notifications

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
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

🟡 **Phase 1 — Software Engineering Fundamentals**

## License

[MIT](LICENSE)
