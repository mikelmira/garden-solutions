"""Painting team schemas - mirrors factory team shape."""
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class PaintingTeamMemberCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=255)
    code: str = Field(min_length=1, max_length=50)
    phone: str | None = None


class PaintingTeamMemberUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = None
    code: str | None = None
    phone: str | None = None
    is_active: bool | None = None


class PaintingTeamMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    painting_team_id: UUID
    name: str
    code: str
    phone: str | None = None
    is_active: bool


class PaintingTeamCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=255)
    code: str = Field(min_length=1, max_length=50)


class PaintingTeamUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = None
    code: str | None = None
    is_active: bool | None = None


class PaintingTeamResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    code: str
    is_active: bool
    members: list[PaintingTeamMemberResponse] | None = None
