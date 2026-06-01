"""
Painting stage endpoints.

Endpoints:
- GET /painting/outstanding - Outstanding paint demand per order_item
- GET /painting/days/today - Today's painting plan
- GET /painting/days?date=YYYY-MM-DD - Painting plan for a specific date
- POST /painting/days - Create a new daily painting plan (admin only)
- POST /painting/days/today/items - Add items to today's plan (admin only)
- PATCH /painting/days/items/{item_id} - Record completion against a plan item
"""
from datetime import date
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import PaintingUser, AdminUser
from app.core.exceptions import NotFoundException
from app.schemas.common import DataResponse
from app.schemas.painting import (
    PaintingPlanCreate,
    PaintingPlanAddItems,
    PaintingPlanItemComplete,
    PaintingPlanResponse,
    PaintingPlanItemResponse,
    PaintingDemandResponse,
)
from app.services.painting_day import PaintingDayService

router = APIRouter()


@router.get("/outstanding", response_model=DataResponse[PaintingDemandResponse])
def get_outstanding_paint_demand(
    current_user: PaintingUser,
    db: Session = Depends(get_db),
):
    """Outstanding paint demand per order_item (manufactured - painted - planned today)."""
    service = PaintingDayService(db)
    demand = service.get_outstanding_demand()
    return DataResponse(data=PaintingDemandResponse.model_validate(demand))


@router.get("/days/today", response_model=DataResponse[PaintingPlanResponse | None])
def get_today_painting_plan(
    current_user: PaintingUser,
    db: Session = Depends(get_db),
):
    service = PaintingDayService(db)
    plan = service.get_today_plan()
    if not plan:
        return DataResponse(data=None)
    return DataResponse(
        data=PaintingPlanResponse.model_validate(service.format_plan_response(plan))
    )


@router.get("/days", response_model=DataResponse[PaintingPlanResponse | None])
def get_painting_plan_by_date(
    current_user: PaintingUser,
    db: Session = Depends(get_db),
    plan_date: date = Query(..., alias="date"),
):
    service = PaintingDayService(db)
    plan = service.get_plan_by_date(plan_date)
    if not plan:
        return DataResponse(data=None)
    return DataResponse(
        data=PaintingPlanResponse.model_validate(service.format_plan_response(plan))
    )


@router.post("/days", response_model=DataResponse[PaintingPlanResponse], status_code=201)
def create_painting_day(
    data: PaintingPlanCreate,
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    """Create today's (or another day's) painting plan."""
    service = PaintingDayService(db)
    items = [
        {"order_item_id": it.order_item_id, "quantity_planned": it.quantity_planned}
        for it in data.items
    ]
    plan = service.create_plan(plan_date=data.plan_date, items=items, created_by=current_user.id)
    return DataResponse(
        data=PaintingPlanResponse.model_validate(service.format_plan_response(plan))
    )


@router.post("/days/today/items", response_model=DataResponse[PaintingPlanResponse])
def add_items_to_today_painting_plan(
    data: PaintingPlanAddItems,
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    service = PaintingDayService(db)
    plan = service.get_today_plan()
    if not plan:
        raise NotFoundException("No painting plan exists for today. Create one first.")
    items = [
        {"order_item_id": it.order_item_id, "quantity_planned": it.quantity_planned}
        for it in data.items
    ]
    plan = service.add_items_to_plan(plan=plan, items=items, added_by=current_user.id)
    return DataResponse(
        data=PaintingPlanResponse.model_validate(service.format_plan_response(plan))
    )


@router.patch(
    "/days/items/{item_id}", response_model=DataResponse[PaintingPlanItemResponse]
)
def update_painting_completion(
    item_id: UUID,
    data: PaintingPlanItemComplete,
    current_user: PaintingUser,
    db: Session = Depends(get_db),
):
    """Record completion against a painting day item."""
    service = PaintingDayService(db)
    item = service.update_item_completion(
        item_id=item_id,
        quantity_completed=data.quantity_completed,
        performed_by=current_user.id,
    )
    payload = {
        "id": item.id,
        "order_item_id": item.order_item_id,
        "quantity_planned": item.quantity_planned,
        "quantity_completed": item.quantity_completed,
        "remaining": item.quantity_planned - item.quantity_completed,
    }
    return DataResponse(data=PaintingPlanItemResponse.model_validate(payload))
