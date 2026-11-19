import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, selectinload

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.incident import Incident, IncidentEvent
from app.models.monitor import Monitor
from app.models.user import User
from app.schemas.incident import (
    IncidentEventResponse,
    IncidentResponse,
    IncidentUpdate,
)

router = APIRouter()


@router.get(
    "",
    response_model=list[IncidentResponse],
    summary="List all incidents",
)
def list_incidents(
    status: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all incidents for monitors owned by the authenticated user."""
    query = (
        db.query(Incident)
        .options(selectinload(Incident.events))
        .join(Monitor, Incident.monitor_id == Monitor.id)
        .filter(Monitor.user_id == current_user.id)
    )
    if status is not None:
        query = query.filter(Incident.status == status)

    return query.order_by(Incident.started_at.desc()).all()


@router.get(
    "/{id}",
    response_model=IncidentResponse,
    summary="Get incident details",
)
def get_incident(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve details and timeline events for an owned incident."""
    incident = (
        db.query(Incident)
        .options(selectinload(Incident.events))
        .join(Monitor, Incident.monitor_id == Monitor.id)
        .filter(Incident.id == id, Monitor.user_id == current_user.id)
        .first()
    )
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )
    return incident


@router.get(
    "/{id}/events",
    response_model=list[IncidentEventResponse],
    summary="Get incident timeline events",
)
def get_incident_events(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve chronologically ordered events for an owned incident."""
    incident = (
        db.query(Incident)
        .join(Monitor, Incident.monitor_id == Monitor.id)
        .filter(Incident.id == id, Monitor.user_id == current_user.id)
        .first()
    )
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )

    return (
        db.query(IncidentEvent)
        .filter(IncidentEvent.incident_id == id)
        .order_by(IncidentEvent.created_at.asc())
        .all()
    )


@router.patch(
    "/{id}",
    response_model=IncidentResponse,
    summary="Update or acknowledge an incident",
)
@router.patch(
    "/{id}/acknowledge",
    response_model=IncidentResponse,
    summary="Acknowledge an incident",
)
def acknowledge_incident(
    id: uuid.UUID,
    data: IncidentUpdate | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Acknowledge an incident and transition status to acknowledged."""
    incident = (
        db.query(Incident)
        .join(Monitor, Incident.monitor_id == Monitor.id)
        .filter(Incident.id == id, Monitor.user_id == current_user.id)
        .first()
    )
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )

    updated = False
    if data and data.description is not None:
        incident.description = data.description
        updated = True

    if incident.status == "open":
        now = datetime.now(UTC)
        incident.status = "acknowledged"
        incident.acknowledged_at = now

        event = IncidentEvent(
            incident_id=incident.id,
            event_type="incident_acknowledged",
            description=f"Incident acknowledged by user {current_user.username}.",
            created_at=now,
        )
        db.add(event)
        updated = True

    if updated:
        db.commit()
        db.refresh(incident)

    return incident
