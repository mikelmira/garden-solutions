"""Painting team endpoints - mirrors factory_teams router."""
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import AdminUser
from app.schemas.common import DataResponse, ListResponse, PaginationMeta
from app.schemas.painting_team import (
    PaintingTeamCreate,
    PaintingTeamUpdate,
    PaintingTeamResponse,
    PaintingTeamMemberCreate,
    PaintingTeamMemberUpdate,
    PaintingTeamMemberResponse,
)
from app.services.painting_team import PaintingTeamService

router = APIRouter()


@router.post("", response_model=DataResponse[PaintingTeamResponse])
def create_painting_team(
    data: PaintingTeamCreate,
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    service = PaintingTeamService(db)
    team = service.create_team(data, performed_by=current_user.id)
    return DataResponse(data=PaintingTeamResponse.model_validate(team))


@router.get("", response_model=ListResponse[PaintingTeamResponse])
def list_painting_teams(
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    service = PaintingTeamService(db)
    teams = service.list_teams()
    return ListResponse(
        data=[PaintingTeamResponse.model_validate(t) for t in teams],
        pagination=PaginationMeta(total=len(teams), page=1, size=len(teams)),
    )


@router.get("/{team_id}", response_model=DataResponse[PaintingTeamResponse])
def get_painting_team(
    team_id: UUID,
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    service = PaintingTeamService(db)
    team = service.get_team(team_id)
    return DataResponse(data=PaintingTeamResponse.model_validate(team))


@router.patch("/{team_id}", response_model=DataResponse[PaintingTeamResponse])
def update_painting_team(
    team_id: UUID,
    data: PaintingTeamUpdate,
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    service = PaintingTeamService(db)
    team = service.update_team(team_id, data, performed_by=current_user.id)
    return DataResponse(data=PaintingTeamResponse.model_validate(team))


@router.post("/{team_id}/members", response_model=DataResponse[PaintingTeamMemberResponse])
def add_painting_team_member(
    team_id: UUID,
    data: PaintingTeamMemberCreate,
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    service = PaintingTeamService(db)
    member = service.add_member(team_id, data, performed_by=current_user.id)
    return DataResponse(data=PaintingTeamMemberResponse.model_validate(member))


@router.patch(
    "/{team_id}/members/{member_id}",
    response_model=DataResponse[PaintingTeamMemberResponse],
)
def update_painting_team_member(
    team_id: UUID,
    member_id: UUID,
    data: PaintingTeamMemberUpdate,
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    service = PaintingTeamService(db)
    member = service.update_member(team_id, member_id, data, performed_by=current_user.id)
    return DataResponse(data=PaintingTeamMemberResponse.model_validate(member))


@router.delete(
    "/{team_id}/members/{member_id}",
    response_model=DataResponse[PaintingTeamMemberResponse],
)
def delete_painting_team_member(
    team_id: UUID,
    member_id: UUID,
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    service = PaintingTeamService(db)
    member = service.deactivate_member(team_id, member_id, performed_by=current_user.id)
    return DataResponse(data=PaintingTeamMemberResponse.model_validate(member))
