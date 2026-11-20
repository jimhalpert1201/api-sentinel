#!/bin/bash
set -e

# Pre-flight: verify write access to SQLite storage directory
touch /app/data/.perm_check && rm -f /app/data/.perm_check || {
    echo "[FATAL] /app/data is not writable by user $(whoami) (UID $(id -u))"
    exit 1
}

echo "==> Running Alembic migrations..."
alembic upgrade head

if [ "${SEED_SAMPLE_USERS}" = "true" ]; then
    echo "==> Seeding sample users..."
    python scripts/seed_users.py
fi

echo "==> Starting Uvicorn server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
