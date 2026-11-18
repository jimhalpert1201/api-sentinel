# Git Commit Safety Protocol & Branch Verification Matrix

> **Purpose:** Standard Operating Procedure (SOP) to audit commits before pushing, verify target branch eligibility, scan for security leaks, validate test coverage, and render an unambiguous verdict: **SAFE TO PUSH** or **NOT SAFE TO PUSH**.

---

## 1. Branch Routing & Permission Matrix

API Sentinel enforces strict branch gating. Before pushing, you must identify your **Current Branch** and your **Target Remote Branch**.

| Target Branch | Allowed Push Methods | Direct Push Allowed? | Required Checks Before Merging |
|---|---|---|---|
| `main` | **Pull Request Only** (from `develop`) | ❌ **STRICTLY BLOCKED** | 100% CI pass, code review approval, zero migrations drift, release tag. |
| `develop` | **Pull Request or Fast-Forward Push** (from `feature/*`) | ⚠️ **CONDITIONAL** (Local audit must be 100% GREEN) | 100% CI pass, all unit/integration tests pass, $\ge 90\%$ test coverage. |
| `feature/*` | **Direct Push** to feature branch | ✅ **ALLOWED** | Working tree clean, Ruff linting passes, no secrets in commit diff. |

---

## 2. Pre-Push Verification Checklist

Before pushing any commit, execute each checkpoint sequentially. If any checkpoint fails, the verdict is immediately **NOT SAFE TO PUSH**.

```
[Target Branch Check] ──> [Secret Scan] ──> [Lint & Format] ──> [Test & Coverage] ──> [Migration Check]
        │                       │                 │                    │                     │
        └───────────────────────┴─────────────────┴────────────────────┴────────── Fail? ────┴──> [NOT SAFE TO PUSH]
                                                                                               │
                                                                                        All Pass?
                                                                                               │
                                                                                               ▼
                                                                                       [SAFE TO PUSH]
```

### Checkpoint 1: Target Branch Identification
- Confirm current branch: `git branch --show-current`
- Confirm upstream remote tracking: `git status -sb`
- **Rule:** If pushing directly to `origin/main`, **HALT**. Direct pushes to `main` are rejected. You must push to `develop` or a feature branch and open a PR.

### Checkpoint 2: Secret & Credential Leak Scan
- Check unstaged and staged diffs: `git diff HEAD~1`
- Verify that **none** of the following appear in tracked files:
  - Private keys (`BEGIN RSA PRIVATE KEY`, `BEGIN PRIVATE KEY`)
  - Live API tokens or secrets (JWT secret keys, database passwords, Telegram bot tokens)
  - Real environment files (`.env`, `*.key`, `*.pem`)
- **Rule:** If any credential or unencrypted `.env` is detected in the diff, **HALT**. Run `git reset` and remove before committing.

### Checkpoint 3: Static Analysis & Formatting
- Run Ruff linter:
  ```bash
  backend\venv\Scripts\ruff check backend
  ```
- Run Ruff format check:
  ```bash
  backend\venv\Scripts\ruff format --check backend
  ```
- **Rule:** Zero linting errors and zero formatting discrepancies.

### Checkpoint 4: Automated Test Suite & Coverage
- Run full pytest suite with coverage:
  ```bash
  backend\venv\Scripts\pytest --cov=backend/app backend/tests
  ```
- **Rule:** 
  - Pass rate: **100%** (0 failing, 0 errors).
  - Coverage threshold: $\ge 90\%$ line coverage.

### Checkpoint 5: Database Schema & Migration Parity
- Verify Alembic database state matches model definitions:
  ```bash
  cd backend && .\venv\Scripts\alembic upgrade head
  ```
- **Rule:** No uncommitted model changes without a corresponding Alembic migration revision.

---

## 3. Verdict Markdown Report Template

When performing an audit (either locally before pushing or automatically in CI), output the audit in this standardized markdown template:

```markdown
# 🛡️ Commit Safety Audit Report

- **Date / Timestamp:** 2026-11-18 11:15:00 UTC
- **Current Branch:** `feature/phase-2-auth`
- **Target Branch:** `origin/develop`
- **Head Commit:** `aedb947` — "feat(auth): implement password hashing"
- **Commit Range:** `origin/develop..HEAD` (3 commits)

---

### Audit Checklist

| Checkpoint | Status | Details |
|---|:---:|---|
| **1. Branch Policy** | ✅ PASSED | Pushing to `develop` via feature branch; `main` not targeted directly |
| **2. Secret Leak Scan** | ✅ PASSED | 0 high-entropy keys or `.env` files detected in diff |
| **3. Linting (Ruff)** | ✅ PASSED | All rules clean (`0 errors`) |
| **4. Code Formatting** | ✅ PASSED | All backend files formatted to standard |
| **5. Test Suite** | ✅ PASSED | 27 / 27 tests passing (100%) |
| **6. Test Coverage** | ✅ PASSED | 99% coverage ($\ge 90\%$ threshold met) |
| **7. Alembic Migrations**| ✅ PASSED | Models and Alembic revisions in sync (`head: 0cf1ee85ef89`) |

---

### Official Verdict

# 🟢 VERDICT: SAFE TO PUSH

> All 7 quality gates passed. Safe to execute `git push origin feature/phase-2-auth` and open PR against `develop`.
```

---

### Failure Example (Blocked)

```markdown
# 🛡️ Commit Safety Audit Report

- **Current Branch:** `main`
- **Target Branch:** `origin/main`

### Official Verdict

# 🔴 VERDICT: NOT SAFE TO PUSH (BLOCKED)

> **Failure Reason:** Direct push to `main` is strictly prohibited by repository branch protection rules.
> **Required Remediation:** 
> 1. Run `git checkout -b feature/<feature-name>`
> 2. Push to your feature branch: `git push -u origin feature/<feature-name>`
> 3. Open a Pull Request targeting `develop`.
```
