"""EmailAutomation schemas."""
from datetime import datetime, date as date_cls, time as time_cls
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.email_automation import (
    EmailAutomationFrequency,
    EmailAutomationPlanType,
)


class EmailAutomationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=255)
    plan_type: str
    frequency: str
    # HH:MM (24h) — required for daily / weekdays / weekly.
    send_time: time_cls | None = None
    day_of_week: int | None = Field(default=None, ge=0, le=6)
    # Full datetime — required for 'once'.
    send_at: datetime | None = None
    recipients: list[EmailStr]

    @field_validator("plan_type")
    @classmethod
    def _valid_plan_type(cls, v):
        if not EmailAutomationPlanType.is_valid(v):
            raise ValueError(f"plan_type must be one of: {', '.join(EmailAutomationPlanType.ALL)}")
        return v

    @field_validator("frequency")
    @classmethod
    def _valid_frequency(cls, v):
        if not EmailAutomationFrequency.is_valid(v):
            raise ValueError(f"frequency must be one of: {', '.join(EmailAutomationFrequency.ALL)}")
        return v


class EmailAutomationUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = None
    plan_type: str | None = None
    frequency: str | None = None
    send_time: time_cls | None = None
    day_of_week: int | None = Field(default=None, ge=0, le=6)
    send_at: datetime | None = None
    recipients: list[EmailStr] | None = None
    is_active: bool | None = None

    @field_validator("plan_type")
    @classmethod
    def _valid_plan_type(cls, v):
        if v is None:
            return v
        if not EmailAutomationPlanType.is_valid(v):
            raise ValueError(f"plan_type must be one of: {', '.join(EmailAutomationPlanType.ALL)}")
        return v

    @field_validator("frequency")
    @classmethod
    def _valid_frequency(cls, v):
        if v is None:
            return v
        if not EmailAutomationFrequency.is_valid(v):
            raise ValueError(f"frequency must be one of: {', '.join(EmailAutomationFrequency.ALL)}")
        return v


class EmailAutomationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    plan_type: str
    frequency: str
    send_time: time_cls | None = None
    day_of_week: int | None = None
    send_at: datetime | None = None
    recipients: list[str]
    is_active: bool
    last_sent_at: datetime | None = None
    next_run_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class OnceOffSendRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    plan_type: str
    recipients: list[EmailStr] = Field(min_length=1)
    for_date: date_cls | None = None

    @field_validator("plan_type")
    @classmethod
    def _valid_plan_type(cls, v):
        if not EmailAutomationPlanType.is_valid(v):
            raise ValueError(f"plan_type must be one of: {', '.join(EmailAutomationPlanType.ALL)}")
        return v


class OnceOffSendResponse(BaseModel):
    sent: bool
    plan_type: str
    recipients: list[str]
    for_date: date_cls
    note: str | None = None
