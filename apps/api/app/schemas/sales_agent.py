"""
Sales agent schemas.
"""
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class SalesAgentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=255)
    code: str = Field(min_length=1, max_length=50)
    phone: str | None = Field(default=None, max_length=50)


class SalesAgentUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = Field(default=None, min_length=1, max_length=255)
    code: str | None = Field(default=None, min_length=1, max_length=50)
    phone: str | None = Field(default=None, max_length=50)
    is_active: bool | None = None


class SalesAgentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    code: str
    phone: str | None = None
    is_active: bool


class SalesAgentResolveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: str = Field(min_length=1, max_length=50)


class SalesAgentResolveResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    code: str
    phone: str | None = None
