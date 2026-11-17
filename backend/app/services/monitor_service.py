import uuid

from sqlalchemy.orm import Session

from app.models.monitor import Monitor
from app.schemas.monitor import MonitorCreate, MonitorUpdate


def list_monitors(db: Session, user_id: uuid.UUID) -> list[Monitor]:
    """Retrieve all monitors owned by user."""
    return db.query(Monitor).filter_by(user_id=user_id).order_by(Monitor.created_at.desc()).all()


def get_monitor(db: Session, monitor_id: uuid.UUID, user_id: uuid.UUID) -> Monitor | None:
    """Retrieve a single monitor owned by user."""
    return db.query(Monitor).filter_by(id=monitor_id, user_id=user_id).first()


def create_monitor(db: Session, user_id: uuid.UUID, data: MonitorCreate) -> Monitor:
    """Create a new monitor record for user."""
    monitor = Monitor(
        user_id=user_id,
        name=data.name,
        url=str(data.url),
        http_method=data.http_method,
        interval_seconds=data.interval_seconds,
        timeout_seconds=data.timeout_seconds,
        expected_status_code=data.expected_status_code,
        headers=data.headers,
        body=data.body,
        is_active=data.is_active,
    )
    db.add(monitor)
    db.commit()
    db.refresh(monitor)
    return monitor


def update_monitor(db: Session, monitor: Monitor, data: MonitorUpdate) -> Monitor:
    """Partially update an existing monitor record."""
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key == "url" and value is not None:
            setattr(monitor, key, str(value))
        else:
            setattr(monitor, key, value)

    db.commit()
    db.refresh(monitor)
    return monitor


def delete_monitor(db: Session, monitor: Monitor) -> None:
    """Delete a monitor and cascade delete related check results and incidents."""
    db.delete(monitor)
    db.commit()
