"""
Order service per Sprint 1 spec.

- POST creates Order + OrderItems, status = "Pending Approval"
- unit_price_rands = base_price * (1 - tier.discount)
- All writes create AuditLog within same transaction
- Role-based access:
  - Admin: All orders
  - Sales: Only orders they created
"""
from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.order import Order, OrderStatus, OrderSource
from app.models.order_item import OrderItem
from app.models.client import Client
from app.models.sku import SKU
from app.models.user import User, UserRole
from app.models.delivery_team import DeliveryTeam
from app.models.sales_agent import SalesAgent
from app.models.store import Store
from app.schemas.order import OrderCreate, OrderStatusUpdate, DeliveryTeamAssign, DeliveryAssignmentUpdate
from app.services.audit import AuditService
from app.models.audit_log import AuditAction
from app.core.exceptions import NotFoundException, ForbiddenException, ConflictException
from app.services.inventory import InventoryService
from app.core.logging import log_order_created, log_order_approved, log_order_cancelled, log_delivery_assigned


def is_order_ready_for_delivery(order: Order) -> bool:
    """
    Check if an order is ready for delivery.
    Ready = all items have quantity_allocated >= quantity_ordered.
    """
    if not order.items:
        return False

    for item in order.items:
        if item.quantity_allocated < item.quantity_ordered:
            return False

    return True


class OrderService:
    """Service for order operations."""

    def __init__(self, db: Session):
        self.db = db
        self.audit_service = AuditService(db)

    def get_orders(
        self,
        current_user: User,
        skip: int = 0,
        limit: int = 100,
        status: str | None = None,
        client_id: UUID | None = None,
    ) -> tuple[list[Order], int]:
        """
        Get orders with role-based filtering per spec.

        - Admin: sees all orders
        - Sales: sees only orders they created
        """
        query = self.db.query(Order)

        # Role-based filtering per spec
        if current_user.role == UserRole.SALES:
            query = query.filter(Order.created_by == current_user.id)

        # Optional filters
        if status:
            query = query.filter(Order.status == status)
        if client_id:
            query = query.filter(Order.client_id == client_id)

        query = query.order_by(Order.created_at.desc())

        total = query.count()
        orders = query.offset(skip).limit(limit).all()

        return orders, total

    def get_order_by_id(self, order_id: UUID, current_user: User) -> Order:
        """
        Get a single order by ID with access control.
        """
        order = self.db.query(Order).filter(Order.id == order_id).first()

        if not order:
            raise NotFoundException(f"Order with id {order_id} not found")

        # Access control per spec
        if current_user.role == UserRole.SALES:
            if order.created_by != current_user.id:
                raise ForbiddenException("You do not have access to this order")

        return order

    def create_order(self, data: OrderCreate, current_user: User) -> Order:
        """
        Create a new order with price snapshot.

        Per spec:
        - Status must be "Pending Approval"
        - unit_price_rands = base_price * (1 - tier.discount)
        - Create AuditLog entry
        """
        if data.store_code and data.store_id:
            raise ConflictException("Provide only one of store_code or store_id")

        if (data.store_code or data.store_id) and (data.sales_agent_code or data.sales_agent_id):
            raise ConflictException("Store orders cannot include sales agent identifiers")

        if (data.store_code or data.store_id) and data.client_id:
            raise ConflictException("Store orders must not include client_id")

        if not (data.store_code or data.store_id) and not data.client_id:
            raise ConflictException("client_id is required for client orders")

        discount = Decimal("0.00")
        client = None
        if data.client_id:
            client = self.db.query(Client).filter(Client.id == data.client_id).first()
            if not client:
                raise NotFoundException(f"Client with id {data.client_id} not found")
            discount = client.price_tier.discount_percentage

        # Calculate delivery date (default: +14 days per spec)
        delivery_date = data.delivery_date or (date.today() + timedelta(days=14))

        sales_agent_id = None
        sales_agent_code = None
        store_id = None
        store_code = None
        order_source = None
        if data.sales_agent_id:
            agent = self.db.query(SalesAgent).filter(SalesAgent.id == data.sales_agent_id, SalesAgent.is_active.is_(True)).first()
            if not agent:
                raise NotFoundException("Sales agent not found or inactive")
            sales_agent_id = agent.id
            order_source = OrderSource.CLIENT
        elif data.sales_agent_code:
            agent = self.db.query(SalesAgent).filter(SalesAgent.code == data.sales_agent_code, SalesAgent.is_active.is_(True)).first()
            if not agent:
                raise NotFoundException("Sales agent not found or inactive")
            sales_agent_id = agent.id
            sales_agent_code = agent.code
            order_source = OrderSource.CLIENT

        if data.store_id:
            store = (
                self.db.query(Store)
                .filter(Store.id == data.store_id, Store.is_active.is_(True))
                .first()
            )
            if not store:
                raise NotFoundException("Store not found or inactive")
            store_id = store.id
            order_source = OrderSource.STORE
            if store.price_tier:
                discount = store.price_tier.discount_percentage
        elif data.store_code:
            store = (
                self.db.query(Store)
                .filter(Store.code == data.store_code, Store.is_active.is_(True))
                .first()
            )
            if not store:
                raise NotFoundException("Store not found or inactive")
            store_id = store.id
            store_code = store.code
            order_source = OrderSource.STORE
            if store.price_tier:
                discount = store.price_tier.discount_percentage
        elif data.client_id:
            order_source = OrderSource.CLIENT

        # Create order - status MUST be Pending Approval per spec
        order = Order(
            client_id=data.client_id,
            created_by=current_user.id,
            sales_agent_id=sales_agent_id,
            store_id=store_id,
            order_source=order_source,
            delivery_date=delivery_date,
            status=OrderStatus.PENDING_APPROVAL,
            notes=data.notes,
            total_price_rands=Decimal("0.00"),
        )
        self.db.add(order)
        self.db.flush()

        # Create order items with price snapshot
        total_price = Decimal("0.00")
        items_data = []

        for item_data in data.items:
            sku = self.db.query(SKU).filter(SKU.id == item_data.sku_id).first()
            if not sku:
                raise NotFoundException(f"SKU with id {item_data.sku_id} not found")

            if not sku.is_active:
                raise ConflictException(f"SKU {sku.code} is not active")

            # Calculate effective price per spec: base_price * (1 - discount)
            effective_price = sku.base_price_rands * (Decimal("1") - discount)
            effective_price = effective_price.quantize(Decimal("0.01"))

            order_item = OrderItem(
                order_id=order.id,
                sku_id=sku.id,
                quantity_ordered=item_data.quantity_ordered,
                unit_price_rands=effective_price,
            )
            self.db.add(order_item)

            line_total = effective_price * item_data.quantity_ordered
            total_price += line_total

            items_data.append({
                "sku_id": str(sku.id),
                "quantity": item_data.quantity_ordered,
                "unit_price": str(effective_price),
            })

        order.total_price_rands = total_price

        # Audit log within same transaction
        payload = {
            "client_id": str(data.client_id) if data.client_id else None,
            "delivery_date": str(delivery_date),
            "total_price_rands": str(total_price),
            "items": items_data,
        }
        if sales_agent_id:
            payload["sales_agent_id"] = str(sales_agent_id)
        if sales_agent_code:
            payload["sales_agent_code"] = sales_agent_code
        if store_id:
            payload["store_id"] = str(store_id)
        if store_code:
            payload["store_code"] = store_code
        if order_source:
            payload["order_source"] = order_source

        self.audit_service.log(
            action=AuditAction.CREATE,
            entity_type="order",
            entity_id=order.id,
            performed_by=current_user.id,
            payload=payload,
        )

        self.db.commit()
        self.db.refresh(order)

        # Lifecycle log
        client_name = order.client.name if order.client else (order.store.name if order.store else None)
        log_order_created(
            order_id=order.id,
            client_name=client_name,
            total_price=order.total_price_rands,
            item_count=len(data.items),
            created_by=current_user.id,
        )

        return order

    def update_order_status(
        self, order_id: UUID, data: OrderStatusUpdate, current_user: User
    ) -> Order:
        """
        Update order status (admin only).

        Per spec:
        - Only allowed transitions:
          - Pending Approval -> Approved
          - Pending Approval -> Cancelled
        - Create AuditLog entry
        - When status becomes "approved", auto-run FIFO allocation
        """
        order = self.db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise NotFoundException(f"Order with id {order_id} not found")

        old_status = order.status
        new_status = data.status

        # Per spec: only Pending Approval can transition to Approved or Cancelled
        if old_status != OrderStatus.PENDING_APPROVAL:
            raise ConflictException(
                f"Cannot change status from '{old_status}'. Only 'pending_approval' orders can be updated."
            )

        if new_status not in [OrderStatus.APPROVED, OrderStatus.CANCELLED]:
            raise ConflictException(
                f"Invalid target status '{new_status}'. Must be 'approved' or 'cancelled'."
            )

        order.status = new_status

        # Audit log within same transaction
        self.audit_service.log(
            action=AuditAction.UPDATE,
            entity_type="order",
            entity_id=order.id,
            performed_by=current_user.id,
            payload={"status": {"old": old_status, "new": new_status}},
        )

        # Lifecycle log
        if new_status == OrderStatus.APPROVED:
            log_order_approved(order_id=order.id, approved_by=current_user.id)

        # Auto-run FIFO allocation when order is approved
        if new_status == OrderStatus.APPROVED:
            inventory_service = InventoryService(self.db)
            # Get SKU IDs from this order for targeted allocation
            sku_ids = [item.sku_id for item in order.items]
            inventory_service.allocate_inventory_fifo(
                sku_ids=sku_ids,
                performed_by=current_user.id,
            )

        self.db.commit()
        self.db.refresh(order)
        return order

    def assign_delivery_team(
        self,
        order_id: UUID,
        data: DeliveryTeamAssign,
        current_user: User,
    ) -> Order:
        try:
            order = self.db.query(Order).filter(Order.id == order_id).first()
            if not order:
                raise NotFoundException(f"Order with id {order_id} not found")

            team = self.db.query(DeliveryTeam).filter(DeliveryTeam.id == data.delivery_team_id, DeliveryTeam.is_active.is_(True)).first()
            if not team:
                raise NotFoundException("Delivery team not found or inactive")

            old_team = order.delivery_team_id
            order.delivery_team_id = team.id
            log_delivery_assigned(order_id=order.id, team_id=team.id, assigned_by=current_user.id)
            if not order.delivery_status:
                order.delivery_status = "outstanding"

            self.audit_service.log(
                action=AuditAction.UPDATE,
                entity_type="delivery_assignment",
                entity_id=order.id,
                performed_by=current_user.id,
                payload={
                    "delivery_team_id": str(team.id),
                    "old_delivery_team_id": str(old_team) if old_team else None,
                },
            )

            self.db.commit()
            self.db.refresh(order)
            return order
        except Exception:
            self.db.rollback()
            raise

    def update_delivery_assignment(
        self,
        order_id: UUID,
        data: DeliveryAssignmentUpdate,
        current_user: User,
    ) -> Order:
        try:
            order = self.db.query(Order).filter(Order.id == order_id).first()
            if not order:
                raise NotFoundException(f"Order with id {order_id} not found")

            payload: dict = {}

            if data.delivery_team_id is not None:
                team = (
                    self.db.query(DeliveryTeam)
                    .filter(DeliveryTeam.id == data.delivery_team_id, DeliveryTeam.is_active.is_(True))
                    .first()
                )
                if not team:
                    raise NotFoundException("Delivery team not found or inactive")
                payload["delivery_team_id"] = str(data.delivery_team_id)
                order.delivery_team_id = team.id
                if not order.delivery_status:
                    order.delivery_status = "outstanding"

            if data.delivery_date is not None:
                payload["delivery_date"] = str(data.delivery_date)
                order.delivery_date = data.delivery_date

            if data.paused is not None:
                payload["delivery_paused"] = data.paused
                order.delivery_paused = data.paused

            if payload:
                self.audit_service.log(
                    action=AuditAction.UPDATE,
                    entity_type="delivery_assignment",
                    entity_id=order.id,
                    performed_by=current_user.id,
                    payload=payload,
                )

            self.db.commit()
            self.db.refresh(order)
            return order
        except Exception:
            self.db.rollback()
            raise

    def cancel_order(
        self,
        order_id: UUID,
        current_user: User,
        reason: str | None = None,
    ) -> Order:
        """
        Cancel an order and return allocated inventory.

        When cancelled:
        - Return allocated stock to inventory
        - Re-run FIFO allocation for released stock
        """
        order = self.db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise NotFoundException(f"Order with id {order_id} not found")

        if order.status == OrderStatus.CANCELLED:
            raise ConflictException("Order is already cancelled")

        if order.status not in [OrderStatus.PENDING_APPROVAL, OrderStatus.APPROVED]:
            raise ConflictException(
                f"Cannot cancel order with status '{order.status}'. Only pending or approved orders can be cancelled."
            )

        old_status = order.status
        order.status = OrderStatus.CANCELLED

        # Return allocated inventory
        inventory_service = InventoryService(self.db)
        dealloc_result = inventory_service.deallocate_order(order, performed_by=current_user.id)

        # Re-run FIFO allocation if we returned any stock
        if dealloc_result["total_returned"] > 0:
            # Get SKU IDs from this order for targeted reallocation
            sku_ids = [item.sku_id for item in order.items]
            inventory_service.allocate_inventory_fifo(sku_ids=sku_ids, performed_by=current_user.id)

        # Audit log
        self.audit_service.log(
            action=AuditAction.UPDATE,
            entity_type="order",
            entity_id=order.id,
            performed_by=current_user.id,
            payload={
                "status": {"old": old_status, "new": OrderStatus.CANCELLED},
                "reason": reason,
                "inventory_returned": dealloc_result["total_returned"],
            },
        )


        # Lifecycle log
        log_order_cancelled(
            order_id=order.id,
            reason=reason,
            cancelled_by=current_user.id,
            inventory_returned=dealloc_result["total_returned"],
        )

        self.db.commit()
        self.db.refresh(order)
        return order

    def delete_order(
        self,
        order_id: UUID,
        current_user: User,
    ) -> None:
        """
        Hard delete an order (Admin only).
        
        Steps:
        1. Deallocate inventory (return stock)
        2. Create Audit Log (deletion record)
        3. Delete order (cascade deletes items)
        """
        order = self.db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise NotFoundException(f"Order with id {order_id} not found")

        # Inventory Deallocation
        inventory_service = InventoryService(self.db)
        dealloc_result = inventory_service.deallocate_order(order, performed_by=current_user.id)
        
        # If we returned stock, we might want to re-run FIFO allocation for other orders,
        # similar to cancellation.
        if dealloc_result["total_returned"] > 0:
             sku_ids = [item.sku_id for item in order.items]
             inventory_service.allocate_inventory_fifo(sku_ids=sku_ids, performed_by=current_user.id)

        # Audit Log - Log BEFORE delete so we have a record
        # Note: Since we are hard deleting, the entity_id in audit log will point to a non-existent record.
        # This is acceptable for hard deletes, or we could keep the ID for historical reference.
        self.audit_service.log(
            action=AuditAction.DELETE,
            entity_type="order",
            entity_id=order.id,
            performed_by=current_user.id,
            payload={
                "order_snapshot": {
                    "client_name": order.client.name if order.client else (order.store.name if order.store else None),
                    "total_price": str(order.total_price_rands),
                    "created_at": str(order.created_at),
                    "status": order.status
                },
                "inventory_returned": dealloc_result["total_returned"]
            },
        )

        self.db.delete(order)
        self.db.commit()
