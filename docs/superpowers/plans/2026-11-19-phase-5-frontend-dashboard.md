# Phase 5 Implementation Plan: React + Vite Web Dashboard

- **Branch:** `feature/phase-5-frontend-dashboard`
- **Target Release:** `v0.3.0` (Milestone 5)
- **Base Branch:** `develop` (Commit: `fc86796`)
- **Author:** Antigravity Architect

---

## 1. Overview & Objectives

Phase 5 delivers the interactive web dashboard for API Sentinel, enabling users to authenticate, inspect monitor status in real-time, view uptime/latency charts, trigger manual checks, and manage incidents:
1. **Authentication Flow (NFR-013, NFR-016)**: Login and Registration pages with JWT storage, queued single-in-flight token refreshing on 401 (preventing replay attack lockouts), 429 rate limit error banners, and protected routes.
2. **System Overview Header (FR-063)**: Real-time dashboard KPI summary cards (Total Monitors, Monitors UP, Monitors DOWN, Active Incidents) computed via incident correlation.
3. **Monitors Dashboard & Full CRUD (FR-060, FR-014)**: Visual grid of monitor cards with derived status badges (🟢 UP / 🔴 DOWN / ⚪ PAUSED), ping times, manual "Check Now" button, pause/resume toggle, and modal form for creating, editing, and deleting monitors with `webhook_url`.
4. **Monitor Detail & Interactive Charts (FR-061, FR-032, FR-033)**: Monitor detail page featuring sliding window charts (`24h`, `7d`, `30d`) for uptime and response time percentiles using Recharts (with null-safe tooltips and `connectNulls`), plus paginated historical check logs with status filtering (All, Passed, Failed).
5. **Incidents Management (FR-062, FR-043, FR-044)**: Dedicated incident tracking view with monitor name resolution, status filters (All, Open, Acknowledged, Resolved), timeline event logs, and in-place "Acknowledge" action.

---

## 2. Technology Stack & Architecture

- **Build Tool & Framework:** Vite + React 18 + TypeScript (`frontend/`)
- **Styling:** Tailwind CSS (Modern dark/slate monitoring theme)
- **Routing:** React Router DOM v6 with `ProtectedRoute` guards
- **State & HTTP:** Axios with subscriber-queued token refresh interceptor (preventing concurrent token reuse lockouts)
- **Charting:** Recharts (responsive SVG AreaChart with null-safe tooltips)
- **Icons:** Lucide React (`lucide-react`)
- **Vite Proxy:** Proxies `/api` to `http://127.0.0.1:8000` to prevent CORS issues during local development.

---

## 3. Directory Structure (`frontend/`)

```
frontend/
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── index.css
│   ├── types/
│   │   ├── auth.ts               # User, TokenResponse, LoginRequest, RegisterRequest
│   │   ├── monitor.ts            # MonitorResponse, MonitorCreate, MonitorUpdate, CheckResult
│   │   ├── metrics.ts            # MetricSummary, TimeSeriesPoint, MonitorMetricsResponse
│   │   └── incident.ts           # IncidentResponse, IncidentEvent
│   ├── api/
│   │   ├── client.ts             # Axios instance + queued token refresh interceptor
│   │   ├── auth.ts               # login, register, logout, getProfile
│   │   ├── monitors.ts           # listMonitors, getMonitor, createMonitor, updateMonitor, deleteMonitor, triggerCheck, getMetrics, getChecks
│   │   └── incidents.ts          # listIncidents, getIncident, acknowledgeIncident, getEvents
│   ├── context/
│   │   └── AuthContext.tsx       # Auth provider, current user, login, logout
│   ├── components/
│   │   ├── Layout.tsx            # Navigation bar, user profile, system overview summary
│   │   ├── ProtectedRoute.tsx    # Redirects unauthenticated users to /login
│   │   ├── MonitorCard.tsx       # Single monitor status card with "Check Now", Edit, and Delete
│   │   ├── MonitorModal.tsx      # Create/Edit monitor dialog with webhook_url & interval validation
│   │   ├── LatencyChart.tsx      # Recharts area chart with connectNulls and null-safe tooltips
│   │   └── IncidentTimeline.tsx  # Chronological incident event list
│   └── pages/
│       ├── LoginPage.tsx         # User authentication form with 429 rate limit banner
│       ├── RegisterPage.tsx      # User registration form with complexity hints
│       ├── DashboardPage.tsx     # Monitors grid + KPI cards + Create button
│       ├── MonitorDetailPage.tsx # Deep-dive charts + filtered check log
│       └── IncidentsPage.tsx     # Incident list with monitor name resolution & acknowledge actions
```

---

## 4. Implementation Tasks

### Task 1: Vite + React Scaffolding, Tailwind Setup & Resilient API Client
- [ ] **Step 1.1**: Scaffold Vite React TypeScript project in `frontend/`:
  - Initialize project with React, TypeScript, and Vite.
- [ ] **Step 1.2**: Install dependencies:
  - `npm install react-router-dom axios lucide-react recharts`
  - `npm install -D tailwindcss postcss autoprefixer @types/node`
  - Initialize Tailwind configuration (`tailwind.config.js`, `postcss.config.js`).
- [ ] **Step 1.3**: Configure `vite.config.ts` with proxy:
  - Proxy `/api` to `http://127.0.0.1:8000` with `changeOrigin: true`.
- [ ] **Step 1.4**: Configure Tailwind theme and base styles in `src/index.css`.
- [ ] **Step 1.5**: Implement TypeScript type definitions in `src/types/` (`auth.ts`, `monitor.ts`, `metrics.ts`, `incident.ts`).
- [ ] **Step 1.6**: Implement `src/api/client.ts` with subscriber-queued token refresh interceptor:
  - Queues failed requests during token refresh.
  - Automatically retries queued requests once new token arrives.
  - Prevents token replay lockout attacks.
- [ ] **Step 1.7**: Implement `src/api/auth.ts`:
  - `login`, `register`, `logout` (passing `refresh_token`), `getProfile` (`/api/v1/users/me`).
- [ ] **Step 1.8**: Implement `src/context/AuthContext.tsx` and `src/components/ProtectedRoute.tsx`.
- [ ] **Step 1.9**: Verify build passes (`npm run build`).
- [ ] **Step 1.10**: Commit Task 1.

### Task 2: Authentication Pages (Login & Register)
- [ ] **Step 2.1**: Implement `src/pages/LoginPage.tsx` with email/password validation, 429 rate limit warning, and redirection.
- [ ] **Step 2.2**: Implement `src/pages/RegisterPage.tsx` with password complexity hints ($\ge 8$ chars, digits/specials) and post-register redirect to `/login` with success banner.
- [ ] **Step 2.3**: Configure routing in `src/App.tsx` (`/login`, `/register`, and protected dashboard routes).
- [ ] **Step 2.4**: Implement `src/components/Layout.tsx` with top navigation bar, active link indicators, and user logout button.
- [ ] **Step 2.5**: Verify build passes (`npm run build`).
- [ ] **Step 2.6**: Commit Task 2.

### Task 3: Monitors Dashboard & Full CRUD
- [ ] **Step 3.1**: Implement `src/api/monitors.ts` (`listMonitors`, `getMonitor`, `createMonitor`, `updateMonitor`, `deleteMonitor`, `triggerCheck`, `getMetrics`, `getChecks`).
- [ ] **Step 3.2**: Implement `src/components/MonitorCard.tsx`:
  - Status derivation: 🟢 UP (active and no open incident), 🔴 DOWN (has active incident), ⚪ PAUSED (`is_active = false`).
  - Ping latency badge and manual "Check Now" button with spinner.
  - Quick action buttons (Edit, Pause/Resume, Delete with confirmation).
- [ ] **Step 3.3**: Implement `src/components/MonitorModal.tsx`:
  - Form fields: Name, URL, Method, Interval (s), Timeout (s), Expected Status, Webhook URL.
  - Client-side validation: Enforces `timeout_seconds <= interval_seconds`.
- [ ] **Step 3.4**: Implement `src/pages/DashboardPage.tsx`:
  - Fetches monitors and active incidents concurrently.
  - Computes KPI counters (Total, Up, Down, Active Incidents) via incident correlation.
  - Renders responsive monitor card grid and "Create Monitor" modal trigger.
- [ ] **Step 3.5**: Verify build passes (`npm run build`).
- [ ] **Step 3.6**: Commit Task 3.

### Task 4: Monitor Detail Page, Null-Safe Charts & Filtered History
- [ ] **Step 4.1**: Implement `src/components/LatencyChart.tsx`:
  - Recharts AreaChart with window tabs (`24h`, `7d`, `30d`).
  - Configures `connectNulls={true}` to prevent broken chart lines on empty intervals.
  - Null-safe tooltip formatter: `value != null ? `${Number(value).toFixed(2)} ms` : "No checks recorded"`.
  - Date formatting on X-axis (`HH:mm` for 24h, `MMM d` for 7d/30d).
- [ ] **Step 4.2**: Implement paginated check history table:
  - Consumes unwrapped `items` from `PaginatedResponse`.
  - Status filter dropdown (All, Passed, Failed).
  - Date/time, status code, response time, and error messages.
- [ ] **Step 4.3**: Implement `src/pages/MonitorDetailPage.tsx`:
  - Monitor header with edit/delete actions and live "Check Now" trigger.
  - Metric summary cards (Uptime %, Avg Latency, p50, p95, p99).
  - Embeds `LatencyChart` and check history table.
- [ ] **Step 4.4**: Verify build passes (`npm run build`).
- [ ] **Step 4.5**: Commit Task 4.

### Task 5: Incident Management Page & Timeline
- [ ] **Step 5.1**: Implement `src/api/incidents.ts` (`listIncidents`, `getIncident`, `acknowledgeIncident`, `getEvents`).
- [ ] **Step 5.2**: Implement `src/components/IncidentTimeline.tsx` displaying chronological audit events (`created`, `acknowledged`, `resolved`).
- [ ] **Step 5.3**: Implement `src/pages/IncidentsPage.tsx`:
  - Fetches incidents and monitors to map `monitor_id` to human-readable `monitor_name`.
  - Filter tabs: All, Open, Acknowledged, Resolved.
  - Card list with incident duration, cause badge, and inline "Acknowledge" button with optional notes dialog.
- [ ] **Step 5.4**: Verify build passes (`npm run build`).
- [ ] **Step 5.5**: Commit Task 5.

### Task 6: Concurrent Launcher (`run.bat`), Verification & Code Review
- [ ] **Step 6.1**: Update `run.bat` to concurrently start both FastAPI backend on port 8000 and Vite dev server on port 5173.
- [ ] **Step 6.2**: Verify backend test suite (`130/130` passing) and frontend build (`npm run build`).
- [ ] **Step 6.3**: Senior Code Reviewer subagent audit.
- [ ] **Step 6.4**: Report results to user and await instructions before merging into `develop`.
