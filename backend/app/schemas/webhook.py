import uuid
from datetime import datetime

from pydantic import BaseModel


class WebhookPayload(BaseModel):
    """Payload contract for outbound incident notifications."""

    event: str  # "incident_created" | "incident_resolved"
    incident_id: uuid.UUID
    monitor_id: uuid.UUID
    monitor_name: str
    monitor_url: str
    status: str
    cause: str
    started_at: datetime
    resolved_at: datetime | None = None
    description: str | None = None
