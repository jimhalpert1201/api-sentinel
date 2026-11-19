import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class IncidentEventResponse(BaseModel):
    """Public incident event timeline log schema."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    incident_id: uuid.UUID
    event_type: str
    description: str
    created_at: datetime


class IncidentResponse(BaseModel):
    """Public incident response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    monitor_id: uuid.UUID
    status: str
    cause: str
    started_at: datetime
    acknowledged_at: datetime | None = None
    resolved_at: datetime | None = None
    description: str | None = None
    events: list[IncidentEventResponse] = []


class IncidentUpdate(BaseModel):
    """Payload for updating or acknowledging an incident."""

    status: str | None = None
    description: str | None = None
