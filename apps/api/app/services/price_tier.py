"""
Price tier service.
"""
from decimal import Decimal
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.price_tier import PriceTier
from app.models.user import User
from app.schemas.price_tier import PriceTierCreate, PriceTierUpdate
from app.services.audit import AuditService
from app.models.audit_log import AuditAction
from app.core.exceptions import NotFoundException


class PriceTierService:
    """Service for price tier operations."""

    def __init__(self, db: Session):
        self.db = db
        self.audit_service = AuditService(db)

    def get_price_tiers(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[PriceTier], int]:
        """
        Get all price tiers.
        """
        query = self.db.query(PriceTier)
        total = query.count()
        tiers = query.offset(skip).limit(limit).all()
        return tiers, total

    def get_price_tier_by_id(self, tier_id: UUID) -> PriceTier:
        """
        Get a single price tier by ID.
        """
        tier = self.db.query(PriceTier).filter(PriceTier.id == tier_id).first()

        if not tier:
            raise NotFoundException(f"Price tier with id {tier_id} not found")

        return tier

    def create_price_tier(self, data: PriceTierCreate, current_user: User) -> PriceTier:
        """
        Create a new price tier (admin only).
        """
        tier = PriceTier(
            name=data.name,
            discount_percentage=data.discount_percentage,
        )
        self.db.add(tier)
        self.db.flush()

        self.audit_service.log(
            action=AuditAction.CREATE,
            entity_type="price_tier",
            entity_id=tier.id,
            performed_by=current_user.id,
            payload={
                "name": data.name,
                "discount_percentage": str(data.discount_percentage),
            },
        )

        self.db.commit()
        self.db.refresh(tier)
        return tier

    def update_price_tier(
        self, tier_id: UUID, data: PriceTierUpdate, current_user: User
    ) -> PriceTier:
        """Update a price tier."""
        tier = self.get_price_tier_by_id(tier_id)

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(tier, field, value)

        self.db.add(tier)
        
        self.audit_service.log(
            action=AuditAction.UPDATE,
            entity_type="price_tier",
            entity_id=tier.id,
            performed_by=current_user.id,
            payload={k: str(v) if isinstance(v, Decimal) else v for k, v in update_data.items()},
        )

        self.db.commit()
        self.db.refresh(tier)
        return tier

    def get_tier_usage(self, tier_id: UUID) -> tuple[int, int]:
        """Return count of (clients, stores) using this tier."""
        tier = self.get_price_tier_by_id(tier_id)
        # Using lazy='select' implies we might need to query explicitly for counts to be optimal,
        # but accessing the list works too if volume is low. 
        # For optimized counting:
        client_count = len(tier.clients)
        store_count = len(tier.stores)
        return client_count, store_count

    def delete_price_tier(self, tier_id: UUID, current_user: User) -> None:
        """Delete a price tier if unused."""
        tier = self.get_price_tier_by_id(tier_id)
        
        client_count, store_count = self.get_tier_usage(tier_id)
        if client_count > 0 or store_count > 0:
            raise ValueError(
                f"Tier is assigned to {client_count} clients and {store_count} stores. "
                "Remove assignments before deleting, or disable tier."
            )

        self.db.delete(tier)
        
        self.audit_service.log(
            action=AuditAction.DELETE,
            entity_type="price_tier",
            entity_id=tier.id,
            performed_by=current_user.id,
        )
        self.db.commit()
