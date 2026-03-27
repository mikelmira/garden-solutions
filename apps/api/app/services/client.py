"""
Client service with role-filtered queries.

Per Sprint 1 spec:
- Admin: All clients
- Sales: Only clients they created (created_by = user.id)
"""
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.client import Client
from app.models.user import User, UserRole
from app.schemas.client import ClientCreate, ClientUpdate
from app.services.audit import AuditService
from app.models.audit_log import AuditAction
from app.core.exceptions import NotFoundException, ForbiddenException


class ClientService:
    """Service for client operations."""

    def __init__(self, db: Session):
        self.db = db
        self.audit_service = AuditService(db)

    def get_clients(
        self,
        current_user: User,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[Client], int]:
        """
        Get clients with role-based filtering.

        - Admin: sees all clients
        - Sales: sees only clients they created
        """
        query = self.db.query(Client)

        # Role-based filtering per spec
        if current_user.role == UserRole.SALES:
            query = query.filter(Client.created_by == current_user.id)

        total = query.count()
        clients = query.offset(skip).limit(limit).all()

        return clients, total

    def get_client_by_id(self, client_id: UUID, current_user: User) -> Client:
        """
        Get a single client by ID with access control.
        """
        client = self.db.query(Client).filter(Client.id == client_id).first()

        if not client:
            raise NotFoundException(f"Client with id {client_id} not found")

        # Access control per spec
        if current_user.role == UserRole.SALES:
            if client.created_by != current_user.id:
                raise ForbiddenException("You do not have access to this client")

        return client

    def create_client(self, data: ClientCreate, current_user: User) -> Client:
        """
        Create a new client (admin only enforced at router level).
        """
        client = Client(
            name=data.name,
            tier_id=data.tier_id,
            created_by=current_user.id,
        )
        self.db.add(client)
        self.db.flush()

        # Audit log within same transaction
        self.audit_service.log(
            action=AuditAction.CREATE,
            entity_type="client",
            entity_id=client.id,
            performed_by=current_user.id,
            payload={"name": data.name, "tier_id": str(data.tier_id)},
        )

        self.db.commit()
        self.db.refresh(client)
        return client

    def update_client(self, client_id: UUID, data: ClientUpdate, current_user: User) -> Client:
        """
        Update client details (admin only enforced at router level).
        """
        client = self.db.query(Client).filter(Client.id == client_id).first()
        if not client:
            raise NotFoundException(f"Client with id {client_id} not found")

        updates = {}
        if data.name is not None:
            client.name = data.name
            updates["name"] = data.name
        if data.tier_id is not None:
            client.tier_id = data.tier_id
            updates["tier_id"] = str(data.tier_id)
        if data.address is not None:
            client.address = data.address
            updates["address"] = data.address
        if data.is_active is not None:
            client.is_active = data.is_active
            updates["is_active"] = data.is_active

        if updates:
            self.audit_service.log(
                action=AuditAction.UPDATE,
                entity_type="client",
                entity_id=client.id,
                performed_by=current_user.id,
                payload=updates,
            )

        self.db.commit()
        self.db.refresh(client)
        return client
