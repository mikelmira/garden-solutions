"""
Factory team schemas.
"""
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class FactoryTeamMemberCreate(BaseModel):
    """Create factory team member."""
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=255)
    code: str = Field(min_length=1, max_length=50)
    phone: str | None = None


class FactoryTeamMemberUpdate(BaseModel):
    """Update factory team member."""
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    code: str | None = None
    phone: str | None = None
    is_active: bool | None = None


class FactoryTeamMemberResponse(BaseModel):
    """Factory team member response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    factory_team_id: UUID
    name: str
    code: str
    phone: str | None = None
    is_active: bool


class FactoryTeamCreate(BaseModel):
    """Create factory team."""
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=255)
    code: str = Field(min_length=1, max_length=50)


class FactoryTeamUpdate(BaseModel):
    """Update factory team."""
    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    code: str | None = None
    is_active: bool | None = None


class FactoryTeamResponse(BaseModel):
    """Factory team response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    code: str
    is_active: bool
    members: list[FactoryTeamMemberResponse] | None = None
