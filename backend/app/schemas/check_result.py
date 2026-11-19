import uuid
from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel, ConfigDict


@dataclass
class CheckExecutionResult:
    """Internal result payload returned by HTTP probe executor."""

    status_code: int | None
    response_time_ms: float
    is_successful: bool
    error_message: str | None = None


class CheckResultResponse(BaseModel):
    """Public check result response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    monitor_id: uuid.UUID
    status_code: int | None
    response_time_ms: float
    is_successful: bool
    error_message: str | None
    checked_at: datetime
