"""Factory team endpoints."""
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import AdminUser
from app.schemas.common import DataResponse, ListResponse, PaginationMeta
from app.schemas.factory_team import (
    FactoryTeamCreate,
    FactoryTeamUpdate,
    FactoryTeamResponse,
    FactoryTeamMemberCreate,
    FactoryTeamMemberUpdate,
    FactoryTeamMemberResponse,
)
from app.services.factory_team import FactoryTeamService

router = APIRouter()


@router.post("", response_model=DataResponse[FactoryTeamResponse])
def create_factory_team(
    data: FactoryTeamCreate,
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    service = FactoryTeamService(db)
    team = service.create_team(data, performed_by=current_user.id)
    return DataResponse(data=FactoryTeamResponse.model_validate(team))


@router.get("", response_model=ListResponse[FactoryTeamResponse])
def list_factory_teams(
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    service = FactoryTeamService(db)
    teams = service.list_teams()
    return ListResponse(
        data=[FactoryTeamResponse.model_validate(t) for t in teams],
        pagination=PaginationMeta(total=len(teams), page=1, size=len(teams)),
    )


@router.get("/{team_id}", response_model=DataResponse[FactoryTeamResponse])
def get_factory_team(
    team_id: UUID,
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    service = FactoryTeamService(db)
    team = service.get_team(team_id)
    return DataResponse(data=FactoryTeamResponse.model_validate(team))


@router.patch("/{team_id}", response_model=DataResponse[FactoryTeamResponse])
def update_factory_team(
    team_id: UUID,
    data: FactoryTeamUpdate,
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    service = FactoryTeamService(db)
    team = service.update_team(team_id, data, performed_by=current_user.id)
    return DataResponse(data=FactoryTeamResponse.model_validate(team))


@router.post("/{team_id}/members", response_model=DataResponse[FactoryTeamMemberResponse])
def add_factory_team_member(
    team_id: UUID,
    data: FactoryTeamMemberCreate,
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    service = FactoryTeamService(db)
    member = service.add_member(team_id, data, performed_by=current_user.id)
    return DataResponse(data=FactoryTeamMemberResponse.model_validate(member))


@router.patch("/{team_id}/members/{member_id}", response_model=DataResponse[FactoryTeamMemberResponse])
def update_factory_team_member(
    team_id: UUID,
    member_id: UUID,
    data: FactoryTeamMemberUpdate,
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    service = FactoryTeamService(db)
    member = service.update_member(team_id, member_id, data, performed_by=current_user.id)
    return DataResponse(data=FactoryTeamMemberResponse.model_validate(member))


@router.delete("/{team_id}/members/{member_id}", response_model=DataResponse[FactoryTeamMemberResponse])
def delete_factory_team_member(
    team_id: UUID,
    member_id: UUID,
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    service = FactoryTeamService(db)
    member = service.deactivate_member(team_id, member_id, performed_by=current_user.id)
    return DataResponse(data=FactoryTeamMemberResponse.model_validate(member))
