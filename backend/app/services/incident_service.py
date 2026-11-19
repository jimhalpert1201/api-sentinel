import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.check_result import CheckResult
from app.models.incident import Incident, IncidentEvent


def evaluate_monitor_incidents(
    db: Session,
    monitor_id: uuid.UUID,
    latest_check: CheckResult,
    threshold: int = 3,
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
        return active_incident

    return active_incident
