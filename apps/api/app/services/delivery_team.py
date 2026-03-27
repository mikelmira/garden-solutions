"""Delivery team service."""
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.delivery_team import DeliveryTeam
from app.models.delivery_team_member import DeliveryTeamMember
from app.models.audit_log import AuditAction
from app.services.audit import AuditService
from app.core.exceptions import NotFoundException, ConflictException
from app.schemas.delivery_team import (
    DeliveryTeamCreate,
    DeliveryTeamUpdate,
    DeliveryTeamMemberCreate,
    DeliveryTeamMemberUpdate,
)


class DeliveryTeamService:
    def __init__(self, db: Session):
        self.db = db
        self.audit_service = AuditService(db)

    def list_teams(self) -> list[DeliveryTeam]:
        return self.db.query(DeliveryTeam).order_by(DeliveryTeam.name.asc()).all()

    def get_team(self, team_id: UUID) -> DeliveryTeam:
        team = self.db.query(DeliveryTeam).filter(DeliveryTeam.id == team_id).first()
        if not team:
            raise NotFoundException("Delivery team not found")
        return team

    def create_team(self, data: DeliveryTeamCreate, performed_by: UUID) -> DeliveryTeam:
        existing = self.db.query(DeliveryTeam).filter(DeliveryTeam.code == data.code).first()
        if existing:
            raise ConflictException("Delivery team code already exists")

        team = DeliveryTeam(name=data.name, code=data.code)
        self.db.add(team)
        self.db.flush()

        self.audit_service.log(
            action=AuditAction.CREATE,
            entity_type="delivery_team",
            entity_id=team.id,
            performed_by=performed_by,
            payload={"name": data.name, "code": data.code},
        )

        self.db.commit()
        self.db.refresh(team)
        return team

    def update_team(self, team_id: UUID, data: DeliveryTeamUpdate, performed_by: UUID) -> DeliveryTeam:
        team = self.get_team(team_id)

        if data.code and data.code != team.code:
            existing = self.db.query(DeliveryTeam).filter(DeliveryTeam.code == data.code).first()
            if existing:
                raise ConflictException("Delivery team code already exists")

        if data.name is not None:
            team.name = data.name
        if data.code is not None:
            team.code = data.code
        if data.is_active is not None:
            team.is_active = data.is_active

        self.audit_service.log(
            action=AuditAction.UPDATE,
            entity_type="delivery_team",
            entity_id=team.id,
            performed_by=performed_by,
            payload={"name": team.name, "code": team.code, "is_active": team.is_active},
        )

        self.db.commit()
        self.db.refresh(team)
        return team

    def add_member(self, team_id: UUID, data: DeliveryTeamMemberCreate, performed_by: UUID) -> DeliveryTeamMember:
        team = self.get_team(team_id)
        member = DeliveryTeamMember(
            delivery_team_id=team.id,
            name=data.name,
            phone=data.phone,
            is_active=True,
        )
        self.db.add(member)
        self.db.flush()

        self.audit_service.log(
            action=AuditAction.CREATE,
            entity_type="delivery_team_member",
            entity_id=member.id,
            performed_by=performed_by,
            payload={"delivery_team_id": str(team.id), "name": data.name, "phone": data.phone},
        )

        self.db.commit()
        self.db.refresh(member)
        return member

    def update_member(
        self,
        team_id: UUID,
        member_id: UUID,
        data: DeliveryTeamMemberUpdate,
        performed_by: UUID,
    ) -> DeliveryTeamMember:
        team = self.get_team(team_id)
        member = (
            self.db.query(DeliveryTeamMember)
            .filter(DeliveryTeamMember.id == member_id, DeliveryTeamMember.delivery_team_id == team.id)
            .first()
        )
        if not member:
            raise NotFoundException("Delivery team member not found")

        if data.name is not None:
            member.name = data.name
        if data.phone is not None:
            member.phone = data.phone
        if data.is_active is not None:
            member.is_active = data.is_active

        self.audit_service.log(
            action=AuditAction.UPDATE,
            entity_type="delivery_team_member",
            entity_id=member.id,
            performed_by=performed_by,
            payload={"delivery_team_id": str(team.id), "name": member.name, "phone": member.phone, "is_active": member.is_active},
        )

        self.db.commit()
        self.db.refresh(member)
        return member

    def deactivate_member(self, team_id: UUID, member_id: UUID, performed_by: UUID) -> DeliveryTeamMember:
        return self.update_member(team_id, member_id, DeliveryTeamMemberUpdate(is_active=False), performed_by)

    def resolve_by_code(self, code: str) -> DeliveryTeam:
        team = self.db.query(DeliveryTeam).filter(DeliveryTeam.code == code, DeliveryTeam.is_active.is_(True)).first()
        if not team:
            raise NotFoundException("Delivery team not found")
        return team
