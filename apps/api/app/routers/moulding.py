"""
Moulding endpoints for factory team operations.

The /moulding page is used by factory team (manufacturing role)
to record production completion against the daily plan.

Endpoints:
- GET /moulding/today - Get today's manufacturing plan
- PATCH /moulding/items/{item_id} - Update completion for a plan item
"""
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import ManufacturingUser
from app.schemas.common import DataResponse
from app.schemas.manufacturing import (
    ManufacturingDayResponse,
    ManufacturingDayItemResponse,
    MouldingItemUpdate,
)
from app.services.manufacturing_day import ManufacturingDayService

router = APIRouter()


@router.get("/today", response_model=DataResponse[ManufacturingDayResponse | None])
def get_today_plan(
    current_user: ManufacturingUser,
    db: Session = Depends(get_db),
):
    """
    Get today's manufacturing plan for the moulding page.
    Returns null if no plan exists for today.
    Access: Manufacturing role.
    """
    service = ManufacturingDayService(db)
    plan = service.get_today_plan()

    if not plan:
        return DataResponse(data=None)

    response = service.format_plan_response(plan)
    return DataResponse(data=ManufacturingDayResponse.model_validate(response))


@router.patch("/items/{item_id}", response_model=DataResponse[ManufacturingDayItemResponse])
def update_item_completion(
    item_id: UUID,
    data: MouldingItemUpdate,
    current_user: ManufacturingUser,
    db: Session = Depends(get_db),
):
    """
    Update completed quantity for a manufacturing day item.

    When completion increases:
    - Inventory is updated with delta
    - FIFO allocation runs for that SKU

    Access: Manufacturing role.
    """
    service = ManufacturingDayService(db)

    item = service.update_item_completion(
        item_id=item_id,
        quantity_completed=data.quantity_completed,
        performed_by=current_user.id,
    )

    # Format response
    sku = item.sku
    product_name = sku.product.name if sku and sku.product else "Unknown"

    response = {
        "id": item.id,
        "sku_id": item.sku_id,
        "sku_code": sku.code if sku else "Unknown",
        "product_name": product_name,
        "size": sku.size if sku else "",
        "color": sku.color if sku else "",
        "quantity_planned": item.quantity_planned,
        "quantity_completed": item.quantity_completed,
        "display_string": f"{item.quantity_planned}x {product_name} - {sku.size if sku else ''} {sku.color if sku else ''}",
        "remaining": item.quantity_planned - item.quantity_completed,
    }

    return DataResponse(data=ManufacturingDayItemResponse.model_validate(response))
