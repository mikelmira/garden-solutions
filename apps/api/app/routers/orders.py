"""
Order endpoints per docs:
- GET /api/v1/orders (Protected, role-filtered)
- POST /api/v1/orders (Sales/Admin)
- GET /api/v1/orders/{id} (Protected)
- PATCH /api/v1/orders/{id}/status (Admin Only: APPROVED/CANCELLED only)
- POST /api/v1/orders/{id}/cancel (Admin Only: Cancel and return inventory)
"""
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import CurrentUser, AdminUser, SalesUser
from app.schemas.order import (
    OrderCreate,
    OrderResponse,
    OrderDetailResponse,
    OrderStatusUpdate,
    DeliveryTeamAssign,
    DeliveryAssignmentUpdate,
)
from app.schemas.common import DataResponse, ListResponse, PaginationMeta
from app.services.order import OrderService, is_order_ready_for_delivery
from app.services.delivery import DeliveryService
from app.core.exceptions import ConflictException

router = APIRouter()


def _enrich_order_response(order, db: Session) -> dict:
    """Add computed fields to order response."""
    payload = OrderResponse.model_validate(order).model_dump()
    payload["is_ready_for_delivery"] = is_order_ready_for_delivery(order)
    payload["delivery_paused"] = getattr(order, "delivery_paused", False)
    # Add client_name for list views
    if order.client:
        payload["client_name"] = order.client.name
    elif order.store:
        payload["client_name"] = f"Store: {order.store.name}"
    else:
        payload["client_name"] = None
    return payload


@router.get("", response_model=ListResponse[OrderResponse])
def list_orders(
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
    client_id: UUID | None = Query(None),
):
    """
    List orders with role-based filtering.

    - Admin: sees all orders
    - Sales: sees only their orders
    - Manufacturing: sees only Approved+ orders
    """
    skip = (page - 1) * size
    service = OrderService(db)
    orders, total = service.get_orders(
        current_user=current_user,
        skip=skip,
        limit=size,
        status=status,
        client_id=client_id,
    )

    # Enrich with computed fields
    data = [OrderResponse.model_validate(_enrich_order_response(o, db)) for o in orders]

    return ListResponse(
        data=data,
        pagination=PaginationMeta(total=total, page=page, size=size),
    )


@router.post("", response_model=DataResponse[OrderDetailResponse], status_code=201)
def create_order(
    data: OrderCreate,
    current_user: SalesUser,  # Sales or Admin
    db: Session = Depends(get_db),
):
    """
    Create a new order.

    - Status is set to Pending Approval
    - unit_price_rands is snapshot of (base_price * (1 - tier_discount))
    - Sales can only create orders for their assigned clients
    """
    if data.store_code or data.store_id:
        raise ConflictException("Store orders must be created via public store flow")

    if not data.client_id:
        raise ConflictException("client_id is required")

    service = OrderService(db)
    order = service.create_order(data, current_user)

    # Build response with items
    payload = OrderDetailResponse.model_validate(order).model_dump()
    payload["is_ready_for_delivery"] = is_order_ready_for_delivery(order)
    return DataResponse(data=OrderDetailResponse.model_validate(payload))


@router.get("/{order_id}", response_model=DataResponse[OrderDetailResponse])
def get_order(
    order_id: UUID,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    """
    Get a single order with its items.

    Access is controlled based on user role.
    """
    service = OrderService(db)
    order = service.get_order_by_id(order_id, current_user)

    delivery_service = DeliveryService(db)
    delivery_state = delivery_service._delivery_state(order)
    receiver_name = delivery_service.get_latest_receiver_name(order.id)
    payload = OrderDetailResponse.model_validate(order).model_dump()
    payload["delivery_state"] = delivery_state
    payload["delivery_receiver_name"] = receiver_name
    payload["is_ready_for_delivery"] = is_order_ready_for_delivery(order)

    return DataResponse(data=OrderDetailResponse.model_validate(payload))


@router.patch("/{order_id}/status", response_model=DataResponse[OrderResponse])
def update_order_status(
    order_id: UUID,
    data: OrderStatusUpdate,
    current_user: AdminUser,  # Admin only
    db: Session = Depends(get_db),
):
    """
    Update order status (Admin only).

    Admin can only set status to APPROVED or CANCELLED.
    Transition rules are enforced.
    """
    service = OrderService(db)
    order = service.update_order_status(order_id, data, current_user)

    return DataResponse(data=OrderResponse.model_validate(_enrich_order_response(order, db)))


class CancelOrderRequest(BaseModel):
    """Optional reason for cancellation."""
    reason: str | None = None


@router.post("/{order_id}/cancel", response_model=DataResponse[OrderResponse])
def cancel_order(
    order_id: UUID,
    current_user: AdminUser,
    db: Session = Depends(get_db),
    data: CancelOrderRequest | None = None,
):
    """
    Cancel an order and return allocated inventory (Admin only).

    This endpoint properly handles inventory reallocation:
    - Returns allocated stock to inventory
    - Re-runs FIFO allocation for other approved orders
    """
    service = OrderService(db)
    reason = data.reason if data else None
    order = service.cancel_order(order_id, current_user, reason)

    return DataResponse(data=OrderResponse.model_validate(_enrich_order_response(order, db)))


@router.patch("/{order_id}/assign-delivery-team", response_model=DataResponse[OrderResponse])
def assign_delivery_team(
    order_id: UUID,
    data: DeliveryTeamAssign,
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    service = OrderService(db)
    order = service.assign_delivery_team(order_id, data, current_user)
    return DataResponse(data=OrderResponse.model_validate(_enrich_order_response(order, db)))


@router.patch("/{order_id}/delivery-assignment", response_model=DataResponse[OrderResponse])
def update_delivery_assignment(
    order_id: UUID,
    data: DeliveryAssignmentUpdate,
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    service = OrderService(db)
    order = service.update_delivery_assignment(order_id, data, current_user)
    return DataResponse(data=OrderResponse.model_validate(_enrich_order_response(order, db)))


@router.delete("/{order_id}", status_code=204)
def delete_order(
    order_id: UUID,
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    """
    Hard delete an order (Admin only).
    
    This will:
    - Return allocated inventory
    - Create an audit log entry
    - Permanently remove the order and its items
    """
    service = OrderService(db)
    service.delete_order(order_id, current_user)
    return None
