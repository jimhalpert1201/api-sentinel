# API Sentinel — Database Design

## 1. Entity-Relationship Diagram

```
┌──────────────┐       ┌───────────────┐       ┌────────────────┐
│    users     │       │   monitors    │       │ check_results  │
├──────────────┤       ├───────────────┤       ├────────────────┤
│ id (PK)      │──┐    │ id (PK)       │──┐    │ id (PK)        │
│ email        │  │    │ user_id (FK)  │  │    │ monitor_id(FK) │
│ username     │  └───►│ name          │  └───►│ status_code    │
│ hashed_pass  │  1:N  │ url           │  1:N  │ response_time  │
│ is_active    │       │ http_method   │       │ is_successful  │
│ role         │       │ interval_sec  │       │ error_message  │
│ created_at   │       │ timeout_sec   │       │ checked_at     │
│ updated_at   │       │ expected_code │       └────────────────┘
└──────────────┘       │ headers       │
                       │ body          │       ┌────────────────┐
                       │ is_active     │       │  incidents     │
                       │ created_at    │       ├────────────────┤
                       │ updated_at    │  ┌───►│ id (PK)        │
                       └───────┬───────┘  │    │ monitor_id(FK) │
                               │          │    │ status         │
                               └──────────┘    │ cause          │
                                     1:N       │ started_at     │
                                               │ acknowledged_at│
                       ┌───────────────────┐   │ resolved_at    │
                       │  incident_events  │   │ description    │
                       ├───────────────────┤   └───────┬────────┘
                       │ id (PK)           │           │
                       │ incident_id (FK)  │◄──────────┘
                       │ event_type        │     1:N
                       │ description       │
                       │ created_at        │
                       └───────────────────┘
```

---

## 2. Table Definitions

### 2.1 `users`

Stores registered user accounts.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PK, DEFAULT gen_random_uuid() | Unique user identifier |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL | User's email address |
| `username` | VARCHAR(100) | UNIQUE, NOT NULL | Display name |
| `hashed_password` | VARCHAR(255) | NOT NULL | bcrypt-hashed password |
| `is_active` | BOOLEAN | DEFAULT TRUE | Soft-delete flag |
| `role` | VARCHAR(20) | DEFAULT 'user' | 'user' or 'admin' |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | Account creation time |
| `updated_at` | TIMESTAMPTZ | DEFAULT NOW() | Last profile update |

**Indexes:**
- `ix_users_email` — UNIQUE on `email` (login lookups)
- `ix_users_username` — UNIQUE on `username`

---

### 2.2 `monitors`

Each row is an API endpoint a user wants to monitor.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PK, DEFAULT gen_random_uuid() | Unique monitor identifier |
| `user_id` | UUID | FK → users.id, NOT NULL | Owner of this monitor |
| `name` | VARCHAR(255) | NOT NULL | Human-readable name |
| `url` | VARCHAR(2048) | NOT NULL | Endpoint URL to monitor |
| `http_method` | VARCHAR(10) | DEFAULT 'GET' | HTTP method (GET, POST, HEAD, etc.) |
| `interval_seconds` | INTEGER | DEFAULT 60, CHECK > 0 | Seconds between automated checks |
| `timeout_seconds` | INTEGER | DEFAULT 30, CHECK > 0 | Timeout threshold per check |
| `expected_status_code` | INTEGER | DEFAULT 200 | Expected HTTP status code |
| `headers` | JSONB | NULLABLE | Custom request headers |
| `body` | JSONB | NULLABLE | Custom request body (for POST, etc.) |
| `is_active` | BOOLEAN | DEFAULT TRUE | Whether monitoring is enabled |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | When the monitor was added |
| `updated_at` | TIMESTAMPTZ | DEFAULT NOW() | Last configuration change |

**Indexes:**
- `ix_monitors_user_id` — on `user_id` (list monitors by user)
- `ix_monitors_is_active` — on `is_active` (scheduler queries active monitors)

**Foreign keys:**
- `user_id` → `users.id` ON DELETE CASCADE

---

### 2.3 `check_results`

One row per health check execution. This is the **highest-volume table**.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PK, DEFAULT gen_random_uuid() | Unique check identifier |
| `monitor_id` | UUID | FK → monitors.id, NOT NULL | Which monitor this check belongs to |
| `status_code` | INTEGER | NULLABLE | HTTP status code (null if timeout/DNS error) |
| `response_time_ms` | FLOAT | NOT NULL | Response time in milliseconds |
| `is_successful` | BOOLEAN | NOT NULL | Whether the check passed |
| `error_message` | TEXT | NULLABLE | Error details (timeout, DNS, connection refused, etc.) |
| `checked_at` | TIMESTAMPTZ | DEFAULT NOW(), NOT NULL | When the check was performed |

**Indexes:**
- `ix_check_results_monitor_id_checked_at` — COMPOSITE on (`monitor_id`, `checked_at` DESC) — primary query pattern
- `ix_check_results_checked_at` — on `checked_at` (data retention cleanup)

**Foreign keys:**
- `monitor_id` → `monitors.id` ON DELETE CASCADE

> **Note:** This table will grow fast. Plan for partitioning by `checked_at` or periodic cleanup of records older than 30 days.

---

### 2.4 `incidents`

Created when a monitor fails consecutively. Tracks the lifecycle from detection through resolution.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PK, DEFAULT gen_random_uuid() | Unique incident identifier |
| `monitor_id` | UUID | FK → monitors.id, NOT NULL | Which monitor triggered this incident |
| `status` | VARCHAR(20) | DEFAULT 'open', NOT NULL | 'open', 'acknowledged', or 'resolved' |
| `cause` | VARCHAR(30) | NOT NULL | 'downtime', 'high_latency', or 'error_rate' |
| `started_at` | TIMESTAMPTZ | DEFAULT NOW(), NOT NULL | When the incident was detected |
| `acknowledged_at` | TIMESTAMPTZ | NULLABLE | When a user acknowledged the incident |
| `resolved_at` | TIMESTAMPTZ | NULLABLE | When the incident was resolved |
| `description` | TEXT | NULLABLE | Auto-generated or user-provided description |

**Indexes:**
- `ix_incidents_monitor_id` — on `monitor_id`
- `ix_incidents_status` — on `status` (dashboard queries open incidents)
- `ix_incidents_monitor_id_status` — COMPOSITE on (`monitor_id`, `status`) — check if monitor has an open incident

**Foreign keys:**
- `monitor_id` → `monitors.id` ON DELETE CASCADE

---

### 2.5 `incident_events`

An append-only timeline log for each incident.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PK, DEFAULT gen_random_uuid() | Unique event identifier |
| `incident_id` | UUID | FK → incidents.id, NOT NULL | Parent incident |
| `event_type` | VARCHAR(30) | NOT NULL | 'created', 'acknowledged', 'escalated', 'resolved', 'comment' |
| `description` | TEXT | NOT NULL | Human-readable event description |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW(), NOT NULL | When the event occurred |

**Indexes:**
- `ix_incident_events_incident_id` — on `incident_id` (timeline queries)

**Foreign keys:**
- `incident_id` → `incidents.id` ON DELETE CASCADE

---

## 3. Relationships Summary

| Relationship | Type | Cascade |
|---|---|---|
| users → monitors | One-to-Many | DELETE CASCADE |
| monitors → check_results | One-to-Many | DELETE CASCADE |
| monitors → incidents | One-to-Many | DELETE CASCADE |
| incidents → incident_events | One-to-Many | DELETE CASCADE |

---

## 4. Enumerated Values

### `users.role`
- `user` — Standard user (default)
- `admin` — Administrator

### `monitors.http_method`
- `GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `HEAD`, `OPTIONS`

### `incidents.status`
- `open` — Active incident, not yet acknowledged
- `acknowledged` — A user has seen and accepted the incident
- `resolved` — The issue has been fixed (auto or manual)

### `incidents.cause`
- `downtime` — Consecutive failed health checks
- `high_latency` — Response time exceeds threshold
- `error_rate` — Error rate exceeds threshold over time window

### `incident_events.event_type`
- `created` — Incident was detected
- `acknowledged` — A user acknowledged the incident
- `escalated` — Severity was raised
- `resolved` — Incident was resolved
- `comment` — Manual note added by a user

---

## 5. Data Volume Estimates

Assuming 100 monitors checked every 60 seconds:

| Table | Rows / day | Rows / month | Notes |
|---|---|---|---|
| `check_results` | 144,000 | ~4.3 million | Highest volume — plan for retention/cleanup |
| `incidents` | 10–50 | 300–1,500 | Depends on API reliability |
| `incident_events` | 30–150 | 900–4,500 | ~3 events per incident |
| `monitors` | — | ~100 | Relatively static |
| `users` | — | ~10–50 | Relatively static |

---

## 6. Migration Strategy

- Use **Alembic** for all schema changes
- Never modify tables directly in production
- Each migration gets a descriptive name: `add_monitors_table`, `add_headers_to_monitors`
- Migrations are version-controlled in `backend/alembic/versions/`
- Run with: `alembic upgrade head`
- Rollback with: `alembic downgrade -1`
