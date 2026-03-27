"""Sales agent endpoints."""
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import AdminUser
from app.schemas.common import DataResponse, ListResponse, PaginationMeta
from app.schemas.sales_agent import (
    SalesAgentCreate,
    SalesAgentUpdate,
    SalesAgentResponse,
    SalesAgentResolveRequest,
    SalesAgentResolveResponse,
)
from app.services.sales_agent import SalesAgentService

router = APIRouter()


@router.post("", response_model=DataResponse[SalesAgentResponse])
def create_sales_agent(
    data: SalesAgentCreate,
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    service = SalesAgentService(db)
    agent = service.create_agent(data, performed_by=current_user.id)
    return DataResponse(data=SalesAgentResponse.model_validate(agent))


@router.get("", response_model=ListResponse[SalesAgentResponse])
def list_sales_agents(
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    service = SalesAgentService(db)
    agents = service.list_agents()
    return ListResponse(data=[SalesAgentResponse.model_validate(a) for a in agents], pagination=PaginationMeta(total=len(agents), page=1, size=len(agents)))


@router.get("/{agent_id}", response_model=DataResponse[SalesAgentResponse])
def get_sales_agent(
    agent_id: UUID,
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    service = SalesAgentService(db)
    agent = service.get_agent(agent_id)
    return DataResponse(data=SalesAgentResponse.model_validate(agent))


@router.patch("/{agent_id}", response_model=DataResponse[SalesAgentResponse])
def update_sales_agent(
    agent_id: UUID,
    data: SalesAgentUpdate,
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    service = SalesAgentService(db)
    agent = service.update_agent(agent_id, data, performed_by=current_user.id)
    return DataResponse(data=SalesAgentResponse.model_validate(agent))


@router.post("/resolve", response_model=DataResponse[SalesAgentResolveResponse])
def resolve_sales_agent(
    data: SalesAgentResolveRequest,
    db: Session = Depends(get_db),
):
    service = SalesAgentService(db)
    agent = service.resolve_by_code(data.code)
    return DataResponse(data=SalesAgentResolveResponse.model_validate(agent))
