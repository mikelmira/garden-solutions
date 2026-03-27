"""
Price tier endpoints per docs:
- GET /api/v1/price-tiers (Protected)
"""
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import CurrentUser, AdminUser
from app.schemas.price_tier import PriceTierCreate, PriceTierResponse, PriceTierUpdate, PriceTierAssignments
from app.schemas.common import DataResponse, ListResponse, PaginationMeta
from app.services.price_tier import PriceTierService

router = APIRouter()


@router.get("", response_model=ListResponse[PriceTierResponse])
def list_price_tiers(
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    """
    List all price tiers.
    """
    skip = (page - 1) * size
    service = PriceTierService(db)
    tiers, total = service.get_price_tiers(skip=skip, limit=size)

    return ListResponse(
        data=[PriceTierResponse.model_validate(t) for t in tiers],
        pagination=PaginationMeta(total=total, page=page, size=size),
    )


@router.post("", response_model=DataResponse[PriceTierResponse], status_code=201)
def create_price_tier(
    data: PriceTierCreate,
    current_user: AdminUser,  # Admin only
    db: Session = Depends(get_db),
):
    """
    Create a new price tier (Admin only).
    """
    service = PriceTierService(db)
    tier = service.create_price_tier(data, current_user)

    return DataResponse(data=PriceTierResponse.model_validate(tier))


@router.patch("/{tier_id}", response_model=DataResponse[PriceTierResponse])
def update_price_tier(
    tier_id: UUID,
    data: PriceTierUpdate,
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    """
    Update a price tier.
    """
    service = PriceTierService(db)
    tier = service.update_price_tier(tier_id, data, current_user)
    return DataResponse(data=PriceTierResponse.model_validate(tier))


@router.get("/{tier_id}/usage", response_model=DataResponse[PriceTierAssignments])
def get_tier_usage(
    tier_id: UUID,
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    """
    Get usage counts for a tier (assignments check).
    """
    service = PriceTierService(db)
    client_count, store_count = service.get_tier_usage(tier_id)
    return DataResponse(data=PriceTierAssignments(client_count=client_count, store_count=store_count))


@router.delete("/{tier_id}", status_code=204)
def delete_price_tier(
    tier_id: UUID,
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    """
    Delete a price tier.
    Returns 409 Conflict if assigned to clients/stores.
    """
    service = PriceTierService(db)
    try:
        service.delete_price_tier(tier_id, current_user)
    except ValueError as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=409, detail=str(e))
