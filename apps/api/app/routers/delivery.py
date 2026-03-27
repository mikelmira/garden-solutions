"""
Delivery endpoints per Sprint 3.
"""
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import DeliveryUser
from app.schemas.common import DataResponse, ListResponse, PaginationMeta
from app.schemas.delivery import DeliveryQueueOrderResponse, DeliveryComplete, DeliveryPartial
from app.schemas.order import OrderDetailResponse
from app.services.delivery import DeliveryService

router = APIRouter()


@router.get("/queue", response_model=ListResponse[DeliveryQueueOrderResponse])
def get_delivery_queue(
    current_user: DeliveryUser,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    """
    Return ready-for-delivery orders.
    Access: Delivery + Admin.
    """
    skip = (page - 1) * size
    service = DeliveryService(db)
    orders, total = service.get_queue(skip=skip, limit=size)

    return ListResponse(
        data=[DeliveryQueueOrderResponse.model_validate(o) for o in orders],
        pagination=PaginationMeta(total=total, page=page, size=size),
    )


@router.patch("/orders/{order_id}/complete", response_model=DataResponse[OrderDetailResponse])
def complete_delivery(
    order_id: UUID,
    data: DeliveryComplete,
    current_user: DeliveryUser,
    db: Session = Depends(get_db),
):
    """
    Mark delivery as complete if all items are fully delivered.
    Access: Delivery + Admin.
    """
    service = DeliveryService(db)
    order = service.mark_delivery_complete(order_id, data, performed_by=current_user.id)
    delivery_state = service._delivery_state(order)
    receiver_name = service.get_latest_receiver_name(order.id)
    payload = OrderDetailResponse.model_validate(order).model_dump()
    payload["delivery_state"] = delivery_state
    payload["delivery_receiver_name"] = receiver_name
    return DataResponse(data=OrderDetailResponse.model_validate(payload))


@router.patch("/orders/{order_id}/partial", response_model=DataResponse[OrderDetailResponse])
def partial_delivery(
    order_id: UUID,
    data: DeliveryPartial,
    current_user: DeliveryUser,
    db: Session = Depends(get_db),
):
    """
    Record a partial delivery attempt with item updates.
    Access: Delivery + Admin.
    """
    service = DeliveryService(db)
    order = service.record_partial_delivery(order_id, data, performed_by=current_user.id)
    delivery_state = service._delivery_state(order)
    receiver_name = service.get_latest_receiver_name(order.id)
    payload = OrderDetailResponse.model_validate(order).model_dump()
    payload["delivery_state"] = delivery_state
    payload["delivery_receiver_name"] = receiver_name
    return DataResponse(data=OrderDetailResponse.model_validate(payload))
