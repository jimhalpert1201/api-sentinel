import uuid
from datetime import datetime
from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

from app.schemas.common import HttpMethod


class MonitorBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    url: HttpUrl
    http_method: HttpMethod = "GET"
    interval_seconds: int = Field(default=60, gt=0, le=86400)
    timeout_seconds: int = Field(default=30, gt=0, le=300)
    expected_status_code: int = Field(default=200, ge=100, le=599)
    headers: dict[str, Any] | None = None
    body: dict[str, Any] | None = None
    is_active: bool = True

    @model_validator(mode="after")
    def validate_timeout_against_interval(self) -> Self:
        if self.timeout_seconds > self.interval_seconds:
            raise ValueError("timeout_seconds cannot exceed interval_seconds")
        return self


class MonitorCreate(MonitorBase):
    pass


class MonitorUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    url: HttpUrl | None = None
    http_method: HttpMethod | None = None
    interval_seconds: int | None = Field(default=None, gt=0, le=86400)
    timeout_seconds: int | None = Field(default=None, gt=0, le=300)
    expected_status_code: int | None = Field(default=None, ge=100, le=599)
    headers: dict[str, Any] | None = None
    body: dict[str, Any] | None = None
    is_active: bool | None = None

    @model_validator(mode="after")
    def validate_timeout_against_interval(self) -> Self:
        if (
            self.timeout_seconds is not None
            and self.interval_seconds is not None
            and self.timeout_seconds > self.interval_seconds
        ):
            raise ValueError("timeout_seconds cannot exceed interval_seconds")
        return self


class MonitorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    url: str
    http_method: str
    interval_seconds: int
    timeout_seconds: int
    expected_status_code: int
    headers: dict[str, Any] | None = None
    body: dict[str, Any] | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
