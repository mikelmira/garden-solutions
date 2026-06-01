"""Email recipient schemas."""
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.email_recipient import EmailRecipientCategory


class EmailRecipientCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: EmailStr
    name: str | None = None
    category: str = Field(default=EmailRecipientCategory.MOULDING)

    @field_validator("category")
    @classmethod
    def _valid_category(cls, v: str) -> str:
        if not EmailRecipientCategory.is_valid(v):
            raise ValueError(
                f"category must be one of: {', '.join(EmailRecipientCategory.ALL)}"
            )
        return v


class EmailRecipientUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: EmailStr | None = None
    name: str | None = None
    category: str | None = None
    is_active: bool | None = None

    @field_validator("category")
    @classmethod
    def _valid_category(cls, v):
        if v is None:
            return v
        if not EmailRecipientCategory.is_valid(v):
            raise ValueError(
                f"category must be one of: {', '.join(EmailRecipientCategory.ALL)}"
            )
        return v


class EmailRecipientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    email: str
    name: str | None = None
    category: str
    is_active: bool
