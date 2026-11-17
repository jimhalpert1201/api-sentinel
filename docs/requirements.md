# API Sentinel — Requirements

## 1. Overview

API Sentinel is a web-based platform that lets users register APIs for monitoring, automatically perform health checks, track uptime and latency, detect failures, and manage incidents through a dashboard.

---

## 2. Functional Requirements

### 2.1 User Management

| ID | Requirement | Priority |
|---|---|---|
| FR-001 | Users can register with email and password | Must |
| FR-002 | Users can log in and receive a JWT access token | Must |
| FR-003 | Access tokens expire; refresh tokens allow re-authentication without password | Must |
| FR-004 | Users can view and update their own profile | Should |
| FR-005 | Admin users can list and manage all users | Could |

### 2.2 API Monitor Management

| ID | Requirement | Priority |
|---|---|---|
| FR-010 | Users can add an API endpoint to monitor (name, URL, method, interval) | Must |
| FR-011 | Users can list their own monitors | Must |
| FR-012 | Users can view details of a single monitor | Must |
| FR-013 | Users can update monitor configuration | Must |
| FR-014 | Users can delete a monitor | Must |
| FR-015 | Users can pause/resume a monitor | Should |
| FR-016 | Users can configure custom headers and request body | Should |
| FR-017 | Users can set expected HTTP status code | Should |
| FR-018 | Each monitor belongs to the user who created it (ownership) | Must |

### 2.3 Health Checks

| ID | Requirement | Priority |
|---|---|---|
| FR-020 | The system performs automated HTTP requests to monitored endpoints at configured intervals | Must |
| FR-021 | Each check records: status code, response time, success/failure, timestamp | Must |
| FR-022 | Users can trigger a manual health check | Must |
| FR-023 | Checks respect the configured timeout threshold | Must |
| FR-024 | Failed checks record the error message | Must |

### 2.4 Uptime & Latency Tracking

| ID | Requirement | Priority |
|---|---|---|
| FR-030 | The system calculates uptime percentage per monitor | Must |
| FR-031 | The system tracks average, p50, p95, and p99 response times | Should |
| FR-032 | Users can view check history with filtering (date range, status) | Must |
| FR-033 | The dashboard displays uptime and latency charts | Should |

### 2.5 Incident Management

| ID | Requirement | Priority |
|---|---|---|
| FR-040 | An incident is created when a monitor fails N consecutive checks (configurable, default 3) | Must |
| FR-041 | An incident is auto-resolved when the monitor passes N consecutive checks (default 3) | Must |
| FR-042 | Users can view open and resolved incidents | Must |
| FR-043 | Users can manually acknowledge an incident | Should |
| FR-044 | Each incident has a timeline of events (created, acknowledged, resolved) | Should |
| FR-045 | High-latency anomalies trigger incidents | Could |
| FR-046 | Error-rate spikes trigger incidents | Could |

### 2.6 Notifications

| ID | Requirement | Priority |
|---|---|---|
| FR-050 | Webhook notifications when an incident is created | Should |
| FR-051 | Webhook notifications when an incident is resolved | Should |
| FR-052 | Email notifications (future phase) | Could |

### 2.7 Dashboard

| ID | Requirement | Priority |
|---|---|---|
| FR-060 | Web dashboard listing all monitors with current status | Must |
| FR-061 | Monitor detail page with uptime chart and check history | Must |
| FR-062 | Incident list page | Must |
| FR-063 | System health overview (how many monitors up/down) | Should |

---

## 3. Non-Functional Requirements

### 3.1 Performance

| ID | Requirement | Target |
|---|---|---|
| NFR-001 | API response time for CRUD operations | < 200ms (p95) |
| NFR-002 | Health check execution time per monitor | < configured timeout |
| NFR-003 | Support concurrent monitoring of 100+ endpoints | Minimum |
| NFR-004 | Dashboard page load time | < 2 seconds |

### 3.2 Security

| ID | Requirement |
|---|---|
| NFR-010 | Passwords hashed with bcrypt (cost factor ≥ 12) |
| NFR-011 | JWT access tokens expire in 15 minutes |
| NFR-012 | Refresh tokens expire in 7 days |
| NFR-013 | All API endpoints require authentication (except /auth and /health) |
| NFR-014 | Users can only access their own monitors and incidents |
| NFR-015 | Input validation on all endpoints (Pydantic) |
| NFR-016 | Rate limiting on authentication endpoints |
| NFR-017 | No secrets in source code — environment variables only |

### 3.3 Reliability

| ID | Requirement |
|---|---|
| NFR-020 | Background workers restart automatically on failure |
| NFR-021 | Failed checks are retried once before recording failure |
| NFR-022 | Database connections use connection pooling |

### 3.4 Maintainability

| ID | Requirement |
|---|---|
| NFR-030 | Database schema changes managed through Alembic migrations |
| NFR-031 | Structured JSON logging throughout the application |
| NFR-032 | Type hints on all Python functions |
| NFR-033 | API documentation auto-generated via OpenAPI (FastAPI default) |
| NFR-034 | Minimum 70% test coverage for backend |

### 3.5 Deployment

| ID | Requirement |
|---|---|
| NFR-040 | All services containerized with Docker |
| NFR-041 | Full environment launchable with `docker compose up` |
| NFR-042 | CI pipeline runs tests on every push |
| NFR-043 | No paid infrastructure required for development |

---

## 4. User Roles

| Role | Permissions |
|---|---|
| **user** | CRUD own monitors, view own incidents, trigger manual checks |
| **admin** | Everything a user can do + manage all users, view all monitors/incidents |

---

## 5. API Versioning

All API endpoints are prefixed with `/api/v1/`. This allows future breaking changes to be introduced under `/api/v2/` without affecting existing clients.

---

## 6. Data Retention

| Data | Retention |
|---|---|
| Check results | 30 days (raw), aggregated hourly beyond 30 days |
| Incidents | Indefinite |
| User accounts | Until deleted |
| Logs | 14 days |
