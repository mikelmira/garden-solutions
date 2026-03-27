"""
Order item endpoints for manufacturing updates.
"""
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import ManufacturingUser, DeliveryUser
from app.schemas.common import DataResponse
from app.schemas.order import OrderItemResponse
from app.schemas.manufacturing import OrderItemManufacturedUpdate
from app.schemas.delivery import OrderItemDeliveredUpdate
from app.services.manufacturing import ManufacturingService
from app.services.delivery import DeliveryService

router = APIRouter()


@router.patch("/{item_id}/manufactured", response_model=DataResponse[OrderItemResponse])
def update_order_item_manufactured(
    item_id: UUID,
    data: OrderItemManufacturedUpdate,
    current_user: ManufacturingUser,
    db: Session = Depends(get_db),
):
    """
    Update manufactured quantity for an order item.
    Access: Admin + Manufacturing.
    """
    service = ManufacturingService(db)
    item = service.update_item_manufactured(
        item_id=item_id,
        quantity_manufactured=data.quantity_manufactured,
        performed_by=current_user.id,
    )

    return DataResponse(data=OrderItemResponse.model_validate(item))


@router.patch("/{item_id}/delivered", response_model=DataResponse[OrderItemResponse])
def update_order_item_delivered(
    item_id: UUID,
    data: OrderItemDeliveredUpdate,
    current_user: DeliveryUser,
    db: Session = Depends(get_db),
):
    """
    Update delivered quantity for an order item.
    Access: Delivery + Admin.
    """
    service = DeliveryService(db)
    item = service.update_item_delivered(
        item_id=item_id,
        data=data,
        performed_by=current_user.id,
    )

    return DataResponse(data=OrderItemResponse.model_validate(item))
