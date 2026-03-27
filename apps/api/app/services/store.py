"""
Store service for CRUD and resolve operations.
"""
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.store import Store
from app.schemas.store import StoreCreate, StoreUpdate
from app.services.audit import AuditService
from app.models.audit_log import AuditAction
from app.core.exceptions import NotFoundException, ConflictException


class StoreService:
    """Service for store operations."""

    def __init__(self, db: Session):
        self.db = db
        self.audit_service = AuditService(db)

    def create_store(self, data: StoreCreate, performed_by: UUID) -> Store:
        existing = self.db.query(Store).filter(Store.code == data.code).first()
        if existing:
            raise ConflictException("Store code already exists")

        store = Store(
            name=data.name,
            code=data.code,
            store_type=data.store_type,
            address=data.address,
            phone=data.phone,
            email=data.email,
            price_tier_id=data.price_tier_id,
        )
        self.db.add(store)
        self.db.flush()

        self.audit_service.log(
            action=AuditAction.CREATE,
            entity_type="store",
            entity_id=store.id,
            performed_by=performed_by,
            payload={"name": data.name, "code": data.code, "store_type": data.store_type},
        )

        self.db.commit()
        self.db.refresh(store)
        return store

    def list_stores(self) -> list[Store]:
        return self.db.query(Store).all()

    def get_store(self, store_id: UUID) -> Store:
        store = self.db.query(Store).filter(Store.id == store_id).first()
        if not store:
            raise NotFoundException(f"Store with id {store_id} not found")
        return store

    def update_store(self, store_id: UUID, data: StoreUpdate, performed_by: UUID) -> Store:
        store = self.get_store(store_id)
        updates = {}

        if data.name is not None:
            store.name = data.name
            updates["name"] = data.name
        if data.code is not None:
            existing = (
                self.db.query(Store)
                .filter(Store.code == data.code, Store.id != store_id)
                .first()
            )
            if existing:
                raise ConflictException("Store code already exists")
            store.code = data.code
            updates["code"] = data.code
        if data.store_type is not None:
            store.store_type = data.store_type
            updates["store_type"] = data.store_type
        if data.address is not None:
            store.address = data.address
            updates["address"] = data.address
        if data.phone is not None:
            store.phone = data.phone
            updates["phone"] = data.phone
        if data.email is not None:
            store.email = data.email
            updates["email"] = data.email
        if data.price_tier_id is not None:
            store.price_tier_id = data.price_tier_id
            updates["price_tier_id"] = str(data.price_tier_id)
        if data.is_active is not None:
            store.is_active = data.is_active
            updates["is_active"] = data.is_active

        if updates:
            self.audit_service.log(
                action=AuditAction.UPDATE,
                entity_type="store",
                entity_id=store.id,
                performed_by=performed_by,
                payload=updates,
            )

        self.db.commit()
        self.db.refresh(store)
        return store

    def resolve_by_code(self, code: str) -> Store:
        store = (
            self.db.query(Store)
            .filter(Store.code == code, Store.is_active.is_(True))
            .first()
        )
        if not store:
            raise NotFoundException("Store not found or inactive")
        return store
