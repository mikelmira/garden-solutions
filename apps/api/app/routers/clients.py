"""
Client endpoints per Sprint 1 spec:
- GET /api/v1/clients (Admin: all, Sales: only clients they created)
- POST /api/v1/clients (Admin Only)
"""
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import CurrentUser, AdminUser
from app.schemas.client import ClientCreate, ClientUpdate, ClientResponse, ClientDetailResponse
from app.schemas.common import DataResponse, ListResponse, PaginationMeta
from app.services.client import ClientService

router = APIRouter()


@router.get("", response_model=ListResponse[ClientResponse])
def list_clients(
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    """
    List clients with role-based filtering.

    - Admin: sees all clients
    - Sales: sees only clients they created
    """
    skip = (page - 1) * size
    service = ClientService(db)
    clients, total = service.get_clients(
        current_user=current_user,
        skip=skip,
        limit=size,
    )

    return ListResponse(
        data=[ClientResponse.model_validate(c) for c in clients],
        pagination=PaginationMeta(total=total, page=page, size=size),
    )


@router.post("", response_model=DataResponse[ClientResponse], status_code=201)
def create_client(
    data: ClientCreate,
    current_user: AdminUser,  # Admin only per spec
    db: Session = Depends(get_db),
):
    """
    Create a new client (Admin only).
    """
    service = ClientService(db)
    client = service.create_client(data, current_user)

    return DataResponse(data=ClientResponse.model_validate(client))


@router.patch("/{client_id}", response_model=DataResponse[ClientResponse])
def update_client(
    client_id: UUID,
    data: ClientUpdate,
    current_user: AdminUser,  # Admin only per spec
    db: Session = Depends(get_db),
):
    """
    Update a client (Admin only). Soft delete via is_active=false.
    """
    service = ClientService(db)
    client = service.update_client(client_id, data, current_user)

    return DataResponse(data=ClientResponse.model_validate(client))
