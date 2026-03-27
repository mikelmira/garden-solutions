"""Public (no-auth) endpoints for ordering, delivery team, and moulding views."""
from datetime import date
from uuid import UUID
from fastapi import APIRouter, Depends, Query, Header
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import get_settings
from app.schemas.common import DataResponse, ListResponse, PaginationMeta
from app.schemas.client import PublicClientResponse
from app.schemas.product import ProductDetailResponse
from app.schemas.order import OrderCreate, OrderDetailResponse
from app.schemas.delivery import DeliveryOutcomeRequest, DeliveryQueueOrderResponse
from app.schemas.manufacturing import (
    ManufacturingDayResponse,
    ManufacturingDayItemResponse,
    MouldingItemUpdate,
)
from app.services.order import OrderService
from app.services.delivery import DeliveryService
from app.services.manufacturing_day import ManufacturingDayService
from app.models.client import Client
from app.models.product import Product
from app.models.user import User
from app.core.exceptions import NotFoundException, ConflictException, ForbiddenException
from app.models.factory_team_member import FactoryTeamMember
from app.models.factory_team import FactoryTeam

settings = get_settings()


router = APIRouter()


@router.post("/orders", response_model=DataResponse[OrderDetailResponse], status_code=201)
def create_public_order(
    data: OrderCreate,
    db: Session = Depends(get_db),
):
    """
    Create order without auth using sales_agent_code.
    """
    if data.sales_agent_code and data.store_code:
        raise ConflictException("Provide only one of sales_agent_code or store_code")

    if data.store_id:
        raise ConflictException("store_id is not allowed for public orders")

    if data.sales_agent_id:
        raise ConflictException("sales_agent_id is not allowed for public orders")

    if data.sales_agent_code and not data.client_id:
        raise ConflictException("client_id is required for sales agent orders")

    if data.store_code and data.client_id:
        raise ConflictException("Store orders must not include client_id")

    if not data.sales_agent_code and not data.store_code:
        raise ConflictException("sales_agent_code or store_code is required")

    # Use admin user for created_by attribution
    admin_user = db.query(User).filter(User.role == "admin").first()
    if not admin_user:
        raise NotFoundException("Admin user not found")

    service = OrderService(db)
    order = service.create_order(data, admin_user)
    return DataResponse(data=OrderDetailResponse.model_validate(order))


@router.get("/clients", response_model=ListResponse[PublicClientResponse])
def public_clients(
    db: Session = Depends(get_db),
):
    clients = db.query(Client).filter(Client.is_active.is_(True)).all()
    total = len(clients)
    return ListResponse(
        data=[PublicClientResponse.model_validate(c) for c in clients],
        pagination=PaginationMeta(total=total, page=1, size=total),
    )


@router.get("/products", response_model=ListResponse[ProductDetailResponse])
def public_products(
    db: Session = Depends(get_db),
):
    products = db.query(Product).filter(Product.is_active.is_(True)).all()
    total = len(products)
    data = []
    for product in products:
        product_resp = ProductDetailResponse.model_validate(product)
        product_resp.skus = [sku for sku in product_resp.skus if sku.is_active]
        data.append(product_resp)
    return ListResponse(
        data=data,
        pagination=PaginationMeta(total=total, page=1, size=total),
    )


@router.get("/delivery/queue", response_model=ListResponse[DeliveryQueueOrderResponse])
def public_delivery_queue(
    team_code: str = Query(..., min_length=1),
    delivery_date: date | None = Query(None, alias="date"),
    db: Session = Depends(get_db),
):
    service = DeliveryService(db)
    target_date = delivery_date or date.today()
    orders, total = service.get_public_queue(team_code, target_date)
    return ListResponse(
        data=[DeliveryQueueOrderResponse.model_validate(o) for o in orders],
        pagination=PaginationMeta(total=total, page=1, size=total),
    )


@router.patch("/delivery/orders/{order_id}/outcome", response_model=DataResponse[OrderDetailResponse])
def public_delivery_outcome(
    order_id: UUID,
    data: DeliveryOutcomeRequest,
    db: Session = Depends(get_db),
):
    service = DeliveryService(db)
    order = service.record_public_outcome(order_id, data)
    return DataResponse(data=OrderDetailResponse.model_validate(order))


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC MOULDING ENDPOINTS (factory code validation)
# ─────────────────────────────────────────────────────────────────────────────


def _is_valid_factory_code(db: Session, code: str) -> bool:
    if not code:
        return False
    # Check member codes first
    member = (
        db.query(FactoryTeamMember)
        .join(FactoryTeam, FactoryTeam.id == FactoryTeamMember.factory_team_id)
        .filter(
            FactoryTeamMember.code == code,
            FactoryTeamMember.is_active.is_(True),
            FactoryTeam.is_active.is_(True),
        )
        .first()
    )
    if member:
        return True
    # Also accept team codes
    team = (
        db.query(FactoryTeam)
        .filter(FactoryTeam.code == code, FactoryTeam.is_active.is_(True))
        .first()
    )
    return team is not None


def validate_factory_code(
    x_factory_code: str = Header(..., alias="X-Factory-Code"),
    db: Session = Depends(get_db),
):
    """Validate factory code from header."""
    if not _is_valid_factory_code(db, x_factory_code):
        raise ForbiddenException("Invalid factory code")
    return x_factory_code


@router.post("/moulding/verify", response_model=DataResponse[dict])
def verify_factory_code(
    factory_code: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
):
    """
    Verify factory code for moulding access.
    Returns success if code is valid.
    """
    if not _is_valid_factory_code(db, factory_code):
        raise ForbiddenException("Invalid factory code")

    return DataResponse(data={"valid": True, "code": factory_code})


@router.get("/moulding/today", response_model=DataResponse[ManufacturingDayResponse | None])
def public_moulding_today(
    x_factory_code: str = Header(..., alias="X-Factory-Code"),
    db: Session = Depends(get_db),
):
    """
    Get today's manufacturing plan for the moulding page.
    Returns null if no plan exists for today.
    Access: Factory code validation via X-Factory-Code header.
    """
    if not _is_valid_factory_code(db, x_factory_code):
        raise ForbiddenException("Invalid factory code")

    service = ManufacturingDayService(db)
    plan = service.get_today_plan()

    if not plan:
        return DataResponse(data=None)

    response = service.format_plan_response(plan)
    return DataResponse(data=ManufacturingDayResponse.model_validate(response))


@router.patch("/moulding/items/{item_id}", response_model=DataResponse[ManufacturingDayItemResponse])
def public_moulding_update_item(
    item_id: UUID,
    data: MouldingItemUpdate,
    x_factory_code: str = Header(..., alias="X-Factory-Code"),
    db: Session = Depends(get_db),
):
    """
    Update completed quantity for a manufacturing day item.

    When completion increases:
    - Inventory is updated with delta
    - FIFO allocation runs for that SKU

    When completion decreases:
    - Inventory is reduced by delta
    - FIFO allocation is re-run for that SKU

    Access: Factory code validation via X-Factory-Code header.
    """
    if not _is_valid_factory_code(db, x_factory_code):
        raise ForbiddenException("Invalid factory code")

    service = ManufacturingDayService(db)

    item = service.update_item_completion(
        item_id=item_id,
        quantity_completed=data.quantity_completed,
        performed_by=None,  # Public endpoint, no user
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
