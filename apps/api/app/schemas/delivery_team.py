"""
Delivery team schemas.
"""
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class DeliveryTeamMemberCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=255)
    phone: str | None = Field(default=None, max_length=50)


class DeliveryTeamMemberUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = Field(default=None, min_length=1, max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    is_active: bool | None = None


class DeliveryTeamMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    delivery_team_id: UUID
    name: str
    phone: str | None
    is_active: bool


class DeliveryTeamCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=255)
    code: str = Field(min_length=1, max_length=50)


class DeliveryTeamUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = Field(default=None, min_length=1, max_length=255)
    code: str | None = Field(default=None, min_length=1, max_length=50)
    is_active: bool | None = None


class DeliveryTeamResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    code: str
    is_active: bool
    members: list[DeliveryTeamMemberResponse] | None = None


class DeliveryTeamResolveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: str = Field(min_length=1, max_length=50)


class DeliveryTeamResolveResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    code: str
