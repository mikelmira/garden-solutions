"""Factory team service."""
from uuid import UUID
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundException, ConflictException
from app.models.factory_team import FactoryTeam
from app.models.factory_team_member import FactoryTeamMember
from app.schemas.factory_team import (
    FactoryTeamCreate,
    FactoryTeamUpdate,
    FactoryTeamMemberCreate,
    FactoryTeamMemberUpdate,
)
from app.services.audit import AuditService
from app.models.audit_log import AuditAction


class FactoryTeamService:
    def __init__(self, db: Session):
        self.db = db
        self.audit_service = AuditService(db)

    def list_teams(self) -> list[FactoryTeam]:
        return self.db.query(FactoryTeam).order_by(FactoryTeam.name.asc()).all()

    def get_team(self, team_id: UUID) -> FactoryTeam:
        team = self.db.query(FactoryTeam).filter(FactoryTeam.id == team_id).first()
        if not team:
            raise NotFoundException("Factory team not found")
        return team

    def create_team(self, data: FactoryTeamCreate, performed_by: UUID) -> FactoryTeam:
        existing = self.db.query(FactoryTeam).filter(FactoryTeam.code == data.code).first()
        if existing:
            raise ConflictException("Factory team code already exists")

        team = FactoryTeam(name=data.name, code=data.code)
        self.db.add(team)
        self.db.flush()

        self.audit_service.log(
            action=AuditAction.CREATE,
            entity_type="factory_team",
            entity_id=team.id,
            performed_by=performed_by,
            payload={"name": team.name, "code": team.code},
        )

        self.db.commit()
        self.db.refresh(team)
        return team

    def update_team(self, team_id: UUID, data: FactoryTeamUpdate, performed_by: UUID) -> FactoryTeam:
        team = self.get_team(team_id)
        if data.code and data.code != team.code:
            existing = self.db.query(FactoryTeam).filter(FactoryTeam.code == data.code).first()
            if existing:
                raise ConflictException("Factory team code already exists")

        if data.name is not None:
            team.name = data.name
        if data.code is not None:
            team.code = data.code
        if data.is_active is not None:
            team.is_active = data.is_active

        self.audit_service.log(
            action=AuditAction.UPDATE,
            entity_type="factory_team",
            entity_id=team.id,
            performed_by=performed_by,
            payload={"name": team.name, "code": team.code, "is_active": team.is_active},
        )

        self.db.commit()
        self.db.refresh(team)
        return team

    def add_member(self, team_id: UUID, data: FactoryTeamMemberCreate, performed_by: UUID) -> FactoryTeamMember:
        team = self.get_team(team_id)

        existing = self.db.query(FactoryTeamMember).filter(FactoryTeamMember.code == data.code).first()
        if existing:
            raise ConflictException("Factory member code already exists")

        member = FactoryTeamMember(
            factory_team_id=team.id,
            name=data.name,
            code=data.code,
            phone=data.phone,
        )
        self.db.add(member)
        self.db.flush()

        self.audit_service.log(
            action=AuditAction.CREATE,
            entity_type="factory_team_member",
            entity_id=member.id,
            performed_by=performed_by,
            payload={"factory_team_id": str(team.id), "name": data.name, "code": data.code, "phone": data.phone},
        )

        self.db.commit()
        self.db.refresh(member)
        return member

    def update_member(
        self,
        team_id: UUID,
        member_id: UUID,
        data: FactoryTeamMemberUpdate,
        performed_by: UUID,
    ) -> FactoryTeamMember:
        team = self.get_team(team_id)
        member = (
            self.db.query(FactoryTeamMember)
            .filter(FactoryTeamMember.id == member_id, FactoryTeamMember.factory_team_id == team.id)
            .first()
        )
        if not member:
            raise NotFoundException("Factory team member not found")

        if data.code and data.code != member.code:
            existing = self.db.query(FactoryTeamMember).filter(FactoryTeamMember.code == data.code).first()
            if existing:
                raise ConflictException("Factory member code already exists")

        if data.name is not None:
            member.name = data.name
        if data.code is not None:
            member.code = data.code
        if data.phone is not None:
            member.phone = data.phone
        if data.is_active is not None:
            member.is_active = data.is_active

        self.audit_service.log(
            action=AuditAction.UPDATE,
            entity_type="factory_team_member",
            entity_id=member.id,
            performed_by=performed_by,
            payload={"factory_team_id": str(team.id), "name": member.name, "code": member.code, "phone": member.phone, "is_active": member.is_active},
        )

        self.db.commit()
        self.db.refresh(member)
        return member

    def deactivate_member(self, team_id: UUID, member_id: UUID, performed_by: UUID) -> FactoryTeamMember:
        return self.update_member(team_id, member_id, FactoryTeamMemberUpdate(is_active=False), performed_by)

    def resolve_by_code(self, code: str) -> FactoryTeamMember:
        member = (
            self.db.query(FactoryTeamMember)
            .join(FactoryTeam, FactoryTeam.id == FactoryTeamMember.factory_team_id)
            .filter(FactoryTeamMember.code == code, FactoryTeamMember.is_active.is_(True), FactoryTeam.is_active.is_(True))
            .first()
        )
        if not member:
            raise NotFoundException("Factory team member not found")
        return member
