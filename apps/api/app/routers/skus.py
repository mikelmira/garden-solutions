"""
SKU endpoints (admin protected).
"""
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import AdminUser
from app.schemas.common import DataResponse
from app.schemas.product import SKUResponse, SKUUpdate
from app.services.product import ProductService

router = APIRouter()


@router.patch("/{sku_id}", response_model=DataResponse[SKUResponse])
def update_sku(
    sku_id: UUID,
    data: SKUUpdate,
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    """
    Update a SKU by ID (Admin only). Soft delete via is_active=false.
    """
    service = ProductService(db)
    sku = service.update_sku_by_id(sku_id, data, current_user)
    return DataResponse(data=SKUResponse.model_validate(sku))
