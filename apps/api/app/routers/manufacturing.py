"""
Manufacturing endpoints per Sprint 2 + Manufacturing Day Plans.

Endpoints:
- GET /manufacturing/queue - Legacy queue for approved orders
- GET /manufacturing/outstanding - Outstanding demand aggregated by SKU
- GET /manufacturing/days/today - Get today's plan
- GET /manufacturing/days?date=YYYY-MM-DD - Get plan by date
- POST /manufacturing/days - Create a new daily plan
- PATCH /manufacturing/order-items/{item_id} - Legacy item update
"""
from datetime import date
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import ManufacturingUser, AdminUser
from app.schemas.common import ListResponse, PaginationMeta, DataResponse
from app.schemas.manufacturing import (
    ManufacturingQueueOrderResponse,
    OrderItemManufacturedUpdate,
    OutstandingDemandResponse,
    ManufacturingDayCreate,
    ManufacturingDayAddItems,
    ManufacturingDayResponse,
)
from app.core.exceptions import NotFoundException
from app.schemas.order import OrderItemResponse
from app.services.manufacturing import ManufacturingService
from app.services.manufacturing_day import ManufacturingDayService

router = APIRouter()


@router.get("/queue", response_model=ListResponse[ManufacturingQueueOrderResponse])
def get_manufacturing_queue(
    current_user: ManufacturingUser,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    """
    Return approved orders with items and manufactured counts.
    Access: Admin + Manufacturing.
    """
    skip = (page - 1) * size
    service = ManufacturingService(db)
    orders, total = service.get_queue(skip=skip, limit=size)

    return ListResponse(
        data=[ManufacturingQueueOrderResponse.model_validate(o) for o in orders],
        pagination=PaginationMeta(total=total, page=page, size=size),
    )


@router.get("/outstanding", response_model=DataResponse[OutstandingDemandResponse])
def get_outstanding_demand(
    current_user: ManufacturingUser,
    db: Session = Depends(get_db),
):
    """
    Get outstanding manufacturing demand aggregated by SKU.
    Shows breakdown by order for admin expandable UI.
    Access: Admin + Manufacturing.
    """
    service = ManufacturingDayService(db)
    demand = service.get_outstanding_demand()
    return DataResponse(data=OutstandingDemandResponse.model_validate(demand))


@router.get("/days/today", response_model=DataResponse[ManufacturingDayResponse | None])
def get_today_plan(
    current_user: ManufacturingUser,
    db: Session = Depends(get_db),
):
    """
    Get today's manufacturing plan.
    Returns null if no plan exists for today.
    Access: Admin + Manufacturing.
    """
    service = ManufacturingDayService(db)
    plan = service.get_today_plan()

    if not plan:
        return DataResponse(data=None)

    response = service.format_plan_response(plan)
    return DataResponse(data=ManufacturingDayResponse.model_validate(response))


@router.get("/days", response_model=DataResponse[ManufacturingDayResponse | None])
def get_plan_by_date(
    current_user: ManufacturingUser,
    db: Session = Depends(get_db),
    plan_date: date = Query(..., alias="date"),
):
    """
    Get manufacturing plan for a specific date.
    Returns null if no plan exists for the date.
    Access: Admin + Manufacturing.
    """
    service = ManufacturingDayService(db)
    plan = service.get_plan_by_date(plan_date)

    if not plan:
        return DataResponse(data=None)

    response = service.format_plan_response(plan)
    return DataResponse(data=ManufacturingDayResponse.model_validate(response))


@router.post("/days", response_model=DataResponse[ManufacturingDayResponse], status_code=201)
def create_manufacturing_day(
    data: ManufacturingDayCreate,
    current_user: AdminUser,  # Only admin can create plans
    db: Session = Depends(get_db),
):
    """
    Create a new manufacturing day plan.

    Validation:
    - Plan date must not already exist
    - Quantities must be > 0
    - Quantities must not exceed outstanding demand

    Access: Admin only.
    """
    service = ManufacturingDayService(db)

    items = [
        {"sku_id": item.sku_id, "quantity_planned": item.quantity_planned}
        for item in data.items
    ]

    plan = service.create_plan(
        plan_date=data.plan_date,
        items=items,
        created_by=current_user.id,
    )

    response = service.format_plan_response(plan)
    return DataResponse(data=ManufacturingDayResponse.model_validate(response))


@router.post("/days/today/items", response_model=DataResponse[ManufacturingDayResponse])
def add_items_to_today_plan(
    data: ManufacturingDayAddItems,
    current_user: AdminUser,  # Only admin can modify plans
    db: Session = Depends(get_db),
):
    """
    Add items to today's manufacturing plan.

    Validation:
    - Today's plan must exist
    - Quantities must be > 0
    - Quantities must not exceed outstanding demand
    - SKU must not already be in the plan

    Access: Admin only.
    """
    service = ManufacturingDayService(db)
    plan = service.get_today_plan()

    if not plan:
        raise NotFoundException("No manufacturing plan exists for today. Create one first.")

    items = [
        {"sku_id": item.sku_id, "quantity_planned": item.quantity_planned}
        for item in data.items
    ]

    plan = service.add_items_to_plan(
        plan=plan,
        items=items,
        added_by=current_user.id,
    )

    response = service.format_plan_response(plan)
    return DataResponse(data=ManufacturingDayResponse.model_validate(response))


@router.patch("/order-items/{item_id}", response_model=DataResponse[OrderItemResponse])
def update_manufacturing_item(
    item_id: UUID,
    data: OrderItemManufacturedUpdate,
    current_user: ManufacturingUser,
    db: Session = Depends(get_db),
):
    """
    Update manufactured quantity for an order item (legacy endpoint).
    """
    service = ManufacturingService(db)
    item = service.update_item_manufactured(
        item_id=item_id,
        quantity_manufactured=data.quantity_manufactured,
        performed_by=current_user.id,
    )

    return DataResponse(data=OrderItemResponse.model_validate(item))
