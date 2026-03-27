"""
Store endpoints: admin CRUD and public resolve.
"""
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import AdminUser
from app.schemas.common import DataResponse, ListResponse, PaginationMeta
from app.schemas.store import (
    StoreCreate,
    StoreUpdate,
    StoreResponse,
    StoreResolveRequest,
    StoreResolveResponse,
)
from app.services.store import StoreService

router = APIRouter()


@router.post("/stores", response_model=DataResponse[StoreResponse], status_code=201)
def create_store(
    data: StoreCreate,
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    service = StoreService(db)
    store = service.create_store(data, current_user.id)
    return DataResponse(data=StoreResponse.model_validate(store))


@router.get("/stores", response_model=ListResponse[StoreResponse])
def list_stores(
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    service = StoreService(db)
    stores = service.list_stores()
    total = len(stores)
    return ListResponse(
        data=[StoreResponse.model_validate(s) for s in stores],
        pagination=PaginationMeta(total=total, page=1, size=total),
    )


@router.get("/stores/{store_id}", response_model=DataResponse[StoreResponse])
def get_store(
    store_id: UUID,
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    service = StoreService(db)
    store = service.get_store(store_id)
    return DataResponse(data=StoreResponse.model_validate(store))


@router.patch("/stores/{store_id}", response_model=DataResponse[StoreResponse])
def update_store(
    store_id: UUID,
    data: StoreUpdate,
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    service = StoreService(db)
    store = service.update_store(store_id, data, current_user.id)
    return DataResponse(data=StoreResponse.model_validate(store))


@router.post("/stores/resolve", response_model=DataResponse[StoreResolveResponse])
def resolve_store(
    data: StoreResolveRequest,
    db: Session = Depends(get_db),
):
    service = StoreService(db)
    store = service.resolve_by_code(data.code)
    return DataResponse(data=StoreResolveResponse.model_validate(store))
