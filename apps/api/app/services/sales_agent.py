"""Sales agent service."""
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.sales_agent import SalesAgent
from app.models.audit_log import AuditAction
from app.services.audit import AuditService
from app.core.exceptions import NotFoundException, ConflictException
from app.schemas.sales_agent import SalesAgentCreate, SalesAgentUpdate


class SalesAgentService:
    def __init__(self, db: Session):
        self.db = db
        self.audit_service = AuditService(db)

    def list_agents(self) -> list[SalesAgent]:
        return self.db.query(SalesAgent).order_by(SalesAgent.name.asc()).all()

    def get_agent(self, agent_id: UUID) -> SalesAgent:
        agent = self.db.query(SalesAgent).filter(SalesAgent.id == agent_id).first()
        if not agent:
            raise NotFoundException("Sales agent not found")
        return agent

    def create_agent(self, data: SalesAgentCreate, performed_by: UUID) -> SalesAgent:
        existing = self.db.query(SalesAgent).filter(SalesAgent.code == data.code).first()
        if existing:
            raise ConflictException("Sales agent code already exists")

        agent = SalesAgent(name=data.name, code=data.code, phone=data.phone)
        self.db.add(agent)
        self.db.flush()

        self.audit_service.log(
            action=AuditAction.CREATE,
            entity_type="sales_agent",
            entity_id=agent.id,
            performed_by=performed_by,
            payload={"name": data.name, "code": data.code, "phone": data.phone},
        )

        self.db.commit()
        self.db.refresh(agent)
        return agent

    def update_agent(self, agent_id: UUID, data: SalesAgentUpdate, performed_by: UUID) -> SalesAgent:
        agent = self.get_agent(agent_id)

        if data.code and data.code != agent.code:
            existing = self.db.query(SalesAgent).filter(SalesAgent.code == data.code).first()
            if existing:
                raise ConflictException("Sales agent code already exists")

        if data.name is not None:
            agent.name = data.name
        if data.code is not None:
            agent.code = data.code
        if data.phone is not None:
            agent.phone = data.phone
        if data.is_active is not None:
            agent.is_active = data.is_active

        self.audit_service.log(
            action=AuditAction.UPDATE,
            entity_type="sales_agent",
            entity_id=agent.id,
            performed_by=performed_by,
            payload={"name": agent.name, "code": agent.code, "phone": agent.phone, "is_active": agent.is_active},
        )

        self.db.commit()
        self.db.refresh(agent)
        return agent

    def resolve_by_code(self, code: str) -> SalesAgent:
        agent = self.db.query(SalesAgent).filter(SalesAgent.code == code, SalesAgent.is_active.is_(True)).first()
        if not agent:
            raise NotFoundException("Sales agent not found")
        return agent
