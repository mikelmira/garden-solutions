"""Delivery team endpoints."""
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import AdminUser
from app.schemas.common import DataResponse, ListResponse, PaginationMeta
from app.schemas.delivery_team import (
    DeliveryTeamCreate,
    DeliveryTeamUpdate,
    DeliveryTeamResponse,
    DeliveryTeamMemberCreate,
    DeliveryTeamMemberUpdate,
    DeliveryTeamMemberResponse,
    DeliveryTeamResolveRequest,
    DeliveryTeamResolveResponse,
)
from app.services.delivery_team import DeliveryTeamService

router = APIRouter()


@router.post("", response_model=DataResponse[DeliveryTeamResponse])
def create_delivery_team(
    data: DeliveryTeamCreate,
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    service = DeliveryTeamService(db)
    team = service.create_team(data, performed_by=current_user.id)
    return DataResponse(data=DeliveryTeamResponse.model_validate(team))


@router.get("", response_model=ListResponse[DeliveryTeamResponse])
def list_delivery_teams(
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    service = DeliveryTeamService(db)
    teams = service.list_teams()
    return ListResponse(data=[DeliveryTeamResponse.model_validate(t) for t in teams], pagination=PaginationMeta(total=len(teams), page=1, size=len(teams)))


@router.get("/{team_id}", response_model=DataResponse[DeliveryTeamResponse])
def get_delivery_team(
    team_id: UUID,
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    service = DeliveryTeamService(db)
    team = service.get_team(team_id)
    return DataResponse(data=DeliveryTeamResponse.model_validate(team))


@router.patch("/{team_id}", response_model=DataResponse[DeliveryTeamResponse])
def update_delivery_team(
    team_id: UUID,
    data: DeliveryTeamUpdate,
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    service = DeliveryTeamService(db)
    team = service.update_team(team_id, data, performed_by=current_user.id)
    return DataResponse(data=DeliveryTeamResponse.model_validate(team))


@router.post("/{team_id}/members", response_model=DataResponse[DeliveryTeamMemberResponse])
def add_delivery_team_member(
    team_id: UUID,
    data: DeliveryTeamMemberCreate,
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    service = DeliveryTeamService(db)
    member = service.add_member(team_id, data, performed_by=current_user.id)
    return DataResponse(data=DeliveryTeamMemberResponse.model_validate(member))


@router.patch("/{team_id}/members/{member_id}", response_model=DataResponse[DeliveryTeamMemberResponse])
def update_delivery_team_member(
    team_id: UUID,
    member_id: UUID,
    data: DeliveryTeamMemberUpdate,
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    service = DeliveryTeamService(db)
    member = service.update_member(team_id, member_id, data, performed_by=current_user.id)
    return DataResponse(data=DeliveryTeamMemberResponse.model_validate(member))


@router.delete("/{team_id}/members/{member_id}", response_model=DataResponse[DeliveryTeamMemberResponse])
def delete_delivery_team_member(
    team_id: UUID,
    member_id: UUID,
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    service = DeliveryTeamService(db)
    member = service.deactivate_member(team_id, member_id, performed_by=current_user.id)
    return DataResponse(data=DeliveryTeamMemberResponse.model_validate(member))


@router.post("/resolve", response_model=DataResponse[DeliveryTeamResolveResponse])
def resolve_delivery_team(
    data: DeliveryTeamResolveRequest,
    db: Session = Depends(get_db),
):
    service = DeliveryTeamService(db)
    team = service.resolve_by_code(data.code)
    return DataResponse(data=DeliveryTeamResolveResponse.model_validate(team))
