import asyncio
import uuid
from collections.abc import Callable
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.check_result import CheckResult
from app.models.monitor import Monitor
from app.services.check_service import run_monitor_check


def get_monitors_due_for_check(db: Session, now: datetime) -> list[Monitor]:
    """
    Find active monitors that are due for a health check:
    - Never checked before (last_checked is None)
    - Elapsed time since latest check >= monitor.interval_seconds
    Uses a correlated subquery on CheckResult.checked_at to eliminate N+1 queries.
    """
    latest_check_subq = (
        db.query(CheckResult.checked_at)
        .filter(CheckResult.monitor_id == Monitor.id)
        .order_by(CheckResult.checked_at.desc())
        .limit(1)
        .correlate(Monitor)
        .scalar_subquery()
    )

    active_monitors = (
        db.query(Monitor, latest_check_subq.label("last_checked"))
        .filter(Monitor.is_active.is_(True))
        .all()
    )

    due_monitors: list[Monitor] = []
    for monitor, last_checked in active_monitors:
        if last_checked is None:
            due_monitors.append(monitor)
        else:
            if last_checked.tzinfo is None:
                last_checked = last_checked.replace(tzinfo=UTC)
            elapsed = (now - last_checked).total_seconds()
            if elapsed >= monitor.interval_seconds:
                due_monitors.append(monitor)

    return due_monitors


async def run_scheduler_tick(
    session_factory: Callable[[], Session] = SessionLocal,
) -> int:
    """
    Execute a single check pass across all due monitors.
    Bounded by an asyncio semaphore and uses isolated sessions to prevent SQLite locks.
    """
    now = datetime.now(UTC)
    with session_factory() as db:
        due = get_monitors_due_for_check(db, now)
        monitor_ids: list[uuid.UUID] = [m.id for m in due]

    if not monitor_ids:
        return 0

    semaphore = asyncio.Semaphore(10)

    async def _execute_single(monitor_id: uuid.UUID) -> None:
        async with semaphore:
            with session_factory() as db:
                monitor = db.query(Monitor).filter_by(id=monitor_id).first()
                if monitor and monitor.is_active:
                    await run_monitor_check(db=db, monitor=monitor)

    tasks = [_execute_single(mid) for mid in monitor_ids]
    await asyncio.gather(*tasks, return_exceptions=True)
    return len(monitor_ids)


class AsyncMonitorScheduler:
    """
    In-process asynchronous monitor scheduler running inside FastAPI lifespan.
    Periodically checks for due monitors and triggers health probes.
    """

    def __init__(
        self,
        interval_seconds: int = 10,
        session_factory: Callable[[], Session] = SessionLocal,
    ):
        self.interval_seconds = interval_seconds
        self.session_factory = session_factory
        self._running = False
        self._task: asyncio.Task | None = None

    @property
    def is_running(self) -> bool:
        return self._running

    async def _tick(self) -> int:
        return await run_scheduler_tick(session_factory=self.session_factory)

    async def _loop(self) -> None:
        while self._running:
            try:
                await self._tick()
            except Exception:
                pass

            try:
                await asyncio.sleep(self.interval_seconds)
            except asyncio.CancelledError:
                break

    def start(self) -> None:
        """Launch background loop task."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        """Cleanly cancel background loop and await termination."""
        if not self._running:
            return
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
