# Phase 2: Authentication & User Management Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement production-grade JWT authentication and user profile management, featuring token rotation with database-backed revocation, bcrypt password security, rate limiting, and seamless protection for all existing monitor APIs.

**Architecture:** Layered architecture adhering to Ponytail's minimalist constraints. FastAPI endpoints handle HTTP requests with dual JSON/OAuth2 form support; pure services handle password verification and token lifecycle; database-backed `refresh_tokens` manage server-side revocation and replay protection; and FastAPI dependency injection (`get_current_user`) secures protected routes.

**Tech Stack:** Python 3.13, FastAPI, PyJWT, bcrypt, python-multipart, SQLAlchemy 2.0, Alembic, Pydantic v2, Pytest.

**Spec:** [docs/requirements.md](docs/requirements.md), [docs/database.md](docs/database.md), [docs/architecture.md](docs/architecture.md).

## Global Constraints

- **Minimalist engineering (Ponytail):** No bloated unmaintained frameworks (no `passlib`, no `python-jose`). Use `PyJWT` and native `bcrypt`.
- **Database agnostic:** Works seamlessly across local SQLite (`sentinel.db`) and PostgreSQL.
- **API Route Prefix:** `/api/v1/`.
- **Token Specifications:**
  - Access token: 15-minute TTL (`access_token_expire_minutes: 15`), signed with `jwt_secret_key` via HS256.
  - Refresh token: 7-day TTL (`refresh_token_expire_days: 7`), persisted in `refresh_tokens` table with SHA256 hashed secret for leak protection.
- **Password Complexity:** 8 to 128 characters, at least 1 digit or special character, non-whitespace.
- **Zero Secrets in Responses:** `hashed_password` must never appear in schemas or responses.
- **100% Test Pass Rate & High Coverage:** Full pytest test suite passes before milestone completion.

## Review Focus

1. **Expired Token Rejection:** Expired access or refresh tokens must return `401 Unauthorized` with `Token expired` error details.
2. **Refresh Token Reuse & Revocation Detection:** Using a revoked or already rotated refresh token must fail with `401 Unauthorized` and prevent unauthorized session access.
3. **Password Leakage Prevention:** Verify `hashed_password` and raw passwords never appear in any response schema (`UserResponse`, loggers, error traces).
4. **Inactive / Soft-Deleted User Lockout:** Inactive users (`is_active = False`) must be rejected at login and Bearer token resolution.
5. **Rate Limiting Threshold:** Repeated failed authentication attempts from an IP must be throttled with `429 Too Many Requests`.

---

### Task 1: Dependencies & Core Cryptography (PyJWT & bcrypt)

**Files:**
- Modify: `backend/requirements.txt`
- Create: `backend/app/auth/passwords.py`
- Create: `backend/app/auth/jwt.py`
- Test: `backend/tests/test_auth_crypto.py`

**Interfaces:**
- Produces:
  - `hash_password(plain_password: str) -> str`
  - `verify_password(plain_password: str, hashed_password: str) -> bool`
  - `create_access_token(user_id: uuid.UUID) -> str`
  - `create_refresh_token(user_id: uuid.UUID) -> tuple[str, str, datetime]` (returns `raw_token`, `jti`, `expires_at`)
  - `decode_token(token: str) -> dict[str, Any]`

- [ ] **Step 1: Write failing cryptography unit tests in `backend/tests/test_auth_crypto.py`**
  - Test password hashing produces salted bcrypt string.
  - Test `verify_password` returns True for valid password, False for incorrect password.
  - Test `create_access_token` creates valid JWT containing `sub`, `exp`, `type="access"`.
  - Test `create_refresh_token` produces unique `jti` and future expiration.
  - Test `decode_token` raises for expired tokens or mismatched secrets.
- [ ] **Step 2: Run pytest to verify test failure (Red)**
  - Run: `backend/venv/Scripts/pytest backend/tests/test_auth_crypto.py`
  - Expected: Failure due to missing modules or dependencies.
- [ ] **Step 3: Update `backend/requirements.txt` and install dependencies**
  - Add: `pyjwt>=2.9.0`, `bcrypt>=4.2.0`, `python-multipart>=0.0.12`.
  - Run: `backend/venv/Scripts/pip install pyjwt bcrypt python-multipart`.
- [ ] **Step 4: Implement `backend/app/auth/passwords.py`**
  - Implement `hash_password` and `verify_password` using `bcrypt.hashpw` / `bcrypt.checkpw` (or `pwdlib`).
- [ ] **Step 5: Implement `backend/app/auth/jwt.py`**
  - Implement token encoders and decoders using `jwt.encode` / `jwt.decode` with HS256 and `settings.jwt_secret_key`.
- [ ] **Step 6: Run pytest to verify all crypto tests pass (Green)**
  - Run: `backend/venv/Scripts/pytest backend/tests/test_auth_crypto.py`
  - Expected: All tests pass.
- [ ] **Step 7: Commit changes**
  - Commit: `feat(auth): implement bcrypt password hashing and PyJWT token utilities`

---

### Task 2: RefreshToken Model & Alembic Migration

**Files:**
- Create: `backend/app/models/refresh_token.py`
- Modify: `backend/app/models/__init__.py`
- Create: `backend/alembic/versions/*_add_refresh_tokens_table.py`
- Test: `backend/tests/test_refresh_token_model.py`

**Interfaces:**
- Consumes: `app.core.database.Base`, `app.models.user.User`
- Produces: `app.models.refresh_token.RefreshToken`

- [ ] **Step 1: Write failing model tests in `backend/tests/test_refresh_token_model.py`**
  - Test creating `RefreshToken` linked to a `User`.
  - Test cascade delete: deleting `User` removes their refresh tokens.
  - Test uniqueness/lookup by `jti` and `token_hash`.
- [ ] **Step 2: Run pytest to confirm failure (Red)**
  - Run: `backend/venv/Scripts/pytest backend/tests/test_refresh_token_model.py`
  - Expected: Failure due to missing model.
- [ ] **Step 3: Implement `backend/app/models/refresh_token.py`**
  - Model fields: `id` (UUID PK), `user_id` (FK -> users.id ondelete="CASCADE"), `token_hash` (String(64), indexed), `jti` (String(36), unique, indexed), `expires_at` (DateTime TZ), `revoked_at` (DateTime TZ, nullable), `created_at` (DateTime TZ).
- [ ] **Step 4: Register model in `backend/app/models/__init__.py`**
  - Add `RefreshToken` to exports and `__all__`.
- [ ] **Step 5: Generate and run Alembic migration**
  - Run: `cd backend && .\venv\Scripts\alembic revision --autogenerate -m "add_refresh_tokens_table"`
  - Run: `cd backend && .\venv\Scripts\alembic upgrade head`
- [ ] **Step 6: Run pytest to verify model tests pass (Green)**
  - Run: `backend/venv/Scripts/pytest backend/tests/test_refresh_token_model.py`
  - Expected: All tests pass.
- [ ] **Step 7: Commit changes**
  - Commit: `feat(database): add RefreshToken model and alembic migration`

---

### Task 3: Pydantic Schemas & In-Memory Rate Limiter

**Files:**
- Create: `backend/app/schemas/user.py`
- Modify: `backend/app/schemas/__init__.py`
- Create: `backend/app/core/rate_limiter.py`
- Test: `backend/tests/test_user_schemas.py`
- Test: `backend/tests/test_rate_limiter.py`

**Interfaces:**
- Produces:
  - `UserRegister`, `UserResponse`, `UserUpdate`, `LoginRequest`, `TokenResponse`, `RefreshTokenRequest`, `ChangePasswordRequest`
  - `RateLimiter`: class or function `check_rate_limit(key: str, max_requests: int, window_seconds: int) -> bool`

- [ ] **Step 1: Write failing tests in `test_user_schemas.py` and `test_rate_limiter.py`**
  - Schema tests: valid email/username/password parsing; reject weak passwords (< 8 chars, no digit/special, whitespace); verify `UserResponse` excludes passwords.
  - Rate limiter tests: allows requests within threshold; rejects requests exceeding limit within window; resets after window expires.
- [ ] **Step 2: Run pytest to confirm failure (Red)**
  - Run: `backend/venv/Scripts/pytest backend/tests/test_user_schemas.py backend/tests/test_rate_limiter.py`
  - Expected: Missing modules error.
- [ ] **Step 3: Implement `backend/app/schemas/user.py`**
  - Implement `UserRegister` with password complexity validator (`@field_validator("password")`).
  - Implement `UserResponse` with `from_attributes = True` (`id`, `email`, `username`, `role`, `is_active`, `created_at`, `updated_at`).
  - Implement `UserUpdate`, `LoginRequest`, `TokenResponse`, `RefreshTokenRequest`, `ChangePasswordRequest`.
- [ ] **Step 4: Implement `backend/app/core/rate_limiter.py`**
  - Minimalist in-memory sliding window rate limiter tracking client IP timestamps in a deque/list.
- [ ] **Step 5: Run pytest to confirm tests pass (Green)**
  - Run: `backend/venv/Scripts/pytest backend/tests/test_user_schemas.py backend/tests/test_rate_limiter.py`
  - Expected: All tests pass.
- [ ] **Step 6: Commit changes**
  - Commit: `feat(auth): implement user schemas, password validation, and rate limiter`

---

### Task 4: Authentication Service & API Endpoints (`/api/v1/auth`)

**Files:**
- Create: `backend/app/services/auth_service.py`
- Create: `backend/app/api/v1/endpoints/auth.py`
- Modify: `backend/app/auth/dependencies.py`
- Modify: `backend/app/api/v1/router.py`
- Test: `backend/tests/test_api_auth.py`

**Interfaces:**
- Consumes: `app.services.auth_service`, `app.auth.jwt`, `app.auth.passwords`
- Produces:
  - Endpoints: `POST /api/v1/auth/register`, `POST /api/v1/auth/login`, `POST /api/v1/auth/refresh`, `POST /api/v1/auth/logout`
  - Dependency: `get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User`

- [ ] **Step 1: Write failing integration tests in `backend/tests/test_api_auth.py`**
  - `POST /auth/register` creates user and returns 201 with `UserResponse`.
  - `POST /auth/register` rejects duplicate email or username with 409 Conflict.
  - `POST /auth/login` with JSON payload returns access + refresh tokens.
  - `POST /auth/login` with OAuth2 form data returns access + refresh tokens.
  - `POST /auth/login` with wrong password returns 401 Unauthorized.
  - `POST /auth/refresh` rotates refresh token and returns new tokens.
  - `POST /auth/refresh` with revoked/invalid token returns 401 Unauthorized.
  - `POST /auth/logout` revokes refresh token.
- [ ] **Step 2: Run pytest to confirm failure (Red)**
  - Run: `backend/venv/Scripts/pytest backend/tests/test_api_auth.py`
  - Expected: 404 or missing router.
- [ ] **Step 3: Implement `backend/app/services/auth_service.py`**
  - Functions: `register_user`, `authenticate_user`, `refresh_session`, `revoke_refresh_token`.
- [ ] **Step 4: Implement `backend/app/api/v1/endpoints/auth.py`**
  - Endpoints wired with rate limiting and dual JSON / form data login support.
- [ ] **Step 5: Update `backend/app/auth/dependencies.py`**
  - Replace Phase 1 dev fallback with real Bearer JWT validation via `OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")`.
  - Validate token expiration, user existence, and `is_active` flag.
- [ ] **Step 6: Register router in `backend/app/api/v1/router.py`**
  - Mount `auth.router` under prefix `/auth`.
- [ ] **Step 7: Run pytest to verify all auth endpoints pass (Green)**
  - Run: `backend/venv/Scripts/pytest backend/tests/test_api_auth.py`
  - Expected: All integration tests pass.
- [ ] **Step 8: Commit changes**
  - Commit: `feat(auth): implement authentication service, endpoints, and JWT Bearer dependency`

---

### Task 5: User Profile Endpoints & Route Protection Verification

**Files:**
- Create: `backend/app/services/user_service.py`
- Create: `backend/app/api/v1/endpoints/users.py`
- Modify: `backend/app/api/v1/router.py`
- Test: `backend/tests/test_api_users.py`
- Modify: `backend/tests/test_api_monitors.py`

**Interfaces:**
- Produces:
  - `GET /api/v1/users/me` -> returns `UserResponse`
  - `PATCH /api/v1/users/me` -> updates username / email
  - `POST /api/v1/users/me/password` -> changes password after verifying current password

- [ ] **Step 1: Write integration tests in `backend/tests/test_api_users.py`**
  - `GET /users/me` returns current user profile with valid Bearer token.
  - `GET /users/me` without token returns 401 Unauthorized.
  - `PATCH /users/me` updates username and email with uniqueness checks.
  - `POST /users/me/password` successfully changes password when current password matches.
  - `POST /users/me/password` fails with 400 when current password is wrong.
- [ ] **Step 2: Run pytest to confirm failure (Red)**
  - Run: `backend/venv/Scripts/pytest backend/tests/test_api_users.py`
  - Expected: Failure.
- [ ] **Step 3: Implement `backend/app/services/user_service.py`**
  - Standalone functions for profile updates and password change.
- [ ] **Step 4: Implement `backend/app/api/v1/endpoints/users.py`**
  - Wire endpoints using `current_user: User = Depends(get_current_user)`.
- [ ] **Step 5: Mount users router in `backend/app/api/v1/router.py`**
  - Mount `users.router` under prefix `/users`.
- [ ] **Step 6: Verify and update existing monitor tests in `test_api_monitors.py`**
  - Confirm `/api/v1/monitors` returns 401 when accessed without authorization.
  - Supply valid JWT Bearer tokens in test fixtures.
- [ ] **Step 7: Run full pytest suite (Green)**
  - Run: `backend/venv/Scripts/pytest backend/tests`
  - Expected: All test suites pass.
- [ ] **Step 8: Commit changes**
  - Commit: `feat(users): implement user profile endpoints and verify global route security`

---

### Task 6: Quality Gate & Code Review Checkpoint

**Files:**
- All modified backend files

**Steps:**
- [ ] Run full Pytest test suite with code coverage (`--cov=backend/app`).
- [ ] Verify test coverage $\ge 90\%$.
- [ ] Run `ruff check backend` and `ruff format --check backend`.
- [ ] Review changes using CodeRabbit and SonarQube rules.
- [ ] Final commit for Phase 2 Milestone.
