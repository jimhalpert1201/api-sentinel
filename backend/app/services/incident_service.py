import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.check_result import CheckResult
from app.models.incident import Incident, IncidentEvent
from app.models.monitor import Monitor
from app.schemas.webhook import WebhookPayload
from app.services.webhook_service import dispatch_incident_webhook_safely


def evaluate_monitor_incidents(
    db: Session,
    monitor_id: uuid.UUID,
    latest_check: CheckResult,
    threshold: int = 3,
    monitor: Monitor | None = None,
) -> Incident | None:
    """
    Evaluate consecutive health checks for a monitor and manage Incident state transitions.
    - If N consecutive checks fail and no active incident exists -> open Incident.
    - If N consecutive checks succeed and an active incident exists -> resolve Incident.
    - Flapping results reset counters without modifying active incident state.
    """
    # Fetch recent checks ordered descending
    recent_checks = (
        db.query(CheckResult)
        .filter(CheckResult.monitor_id == monitor_id)
        .order_by(CheckResult.checked_at.desc())
        .limit(threshold)
        .all()
    )

    if len(recent_checks) < threshold:
        return None

    # Check for existing active incident (open or acknowledged)
    active_incident = (
        db.query(Incident)
        .filter(
            Incident.monitor_id == monitor_id,
            Incident.status.in_(["open", "acknowledged"]),
        )
        .first()
    )

    # Condition 1: Consecutive Failures >= threshold
    all_failed = all(not c.is_successful for c in recent_checks)
    if all_failed:
        if not active_incident:
            now = datetime.now(UTC)
            incident = Incident(
                monitor_id=monitor_id,
                status="open",
                cause="consecutive_failures",
                started_at=now,
                description=f"Monitor failed {threshold} consecutive health checks.",
            )
            db.add(incident)
            db.flush()

            event = IncidentEvent(
                incident_id=incident.id,
                event_type="incident_created",
                description=(
                    f"Incident automatically opened after {threshold} consecutive check failures."
                ),
                created_at=now,
            )
            db.add(event)
            db.commit()
            db.refresh(incident)

            if monitor is None:
                monitor = db.query(Monitor).filter_by(id=monitor_id).first()

            if monitor and monitor.webhook_url:
                payload = WebhookPayload(
                    event="incident_created",
                    incident_id=incident.id,
                    monitor_id=monitor.id,
                    monitor_name=monitor.name,
                    monitor_url=monitor.url,
                    status=incident.status,
                    cause=incident.cause,
                    started_at=incident.started_at,
                    resolved_at=incident.resolved_at,
                    description=incident.description,
                )
                dispatch_incident_webhook_safely(monitor.webhook_url, payload)

            return incident
        return active_incident

    # Condition 2: Consecutive Successes >= threshold (Auto-Resolution)
    all_passed = all(c.is_successful for c in recent_checks)
    if all_passed and active_incident:
        now = datetime.now(UTC)
        active_incident.status = "resolved"
        active_incident.resolved_at = now

        event = IncidentEvent(
            incident_id=active_incident.id,
            event_type="incident_resolved",
            description=(
                f"Incident automatically resolved after {threshold} "
                "consecutive successful health checks."
            ),
            created_at=now,
        )
        db.add(event)
        db.commit()
        db.refresh(active_incident)

        if monitor is None:
            monitor = db.query(Monitor).filter_by(id=monitor_id).first()

        if monitor and monitor.webhook_url:
            payload = WebhookPayload(
                event="incident_resolved",
                incident_id=active_incident.id,
                monitor_id=monitor.id,
                monitor_name=monitor.name,
                monitor_url=monitor.url,
                status=active_incident.status,
                cause=active_incident.cause,
                started_at=active_incident.started_at,
                resolved_at=active_incident.resolved_at,
                description=active_incident.description,
            )
            dispatch_incident_webhook_safely(monitor.webhook_url, payload)

        return active_incident

    return active_incident
