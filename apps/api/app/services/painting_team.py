"""Painting team service - mirrors factory_team_service."""
from uuid import UUID
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundException, ConflictException
from app.models.painting_team import PaintingTeam
from app.models.painting_team_member import PaintingTeamMember
from app.schemas.painting_team import (
    PaintingTeamCreate,
    PaintingTeamUpdate,
    PaintingTeamMemberCreate,
    PaintingTeamMemberUpdate,
)
from app.services.audit import AuditService
from app.models.audit_log import AuditAction


class PaintingTeamService:
    def __init__(self, db: Session):
        self.db = db
        self.audit_service = AuditService(db)

    def list_teams(self) -> list[PaintingTeam]:
        return self.db.query(PaintingTeam).order_by(PaintingTeam.name.asc()).all()

    def get_team(self, team_id: UUID) -> PaintingTeam:
        team = self.db.query(PaintingTeam).filter(PaintingTeam.id == team_id).first()
        if not team:
            raise NotFoundException("Painting team not found")
        return team

    def create_team(self, data: PaintingTeamCreate, performed_by: UUID) -> PaintingTeam:
        existing = self.db.query(PaintingTeam).filter(PaintingTeam.code == data.code).first()
        if existing:
            raise ConflictException("Painting team code already exists")

        team = PaintingTeam(name=data.name, code=data.code)
        self.db.add(team)
        self.db.flush()

        self.audit_service.log(
            action=AuditAction.CREATE,
            entity_type="painting_team",
            entity_id=team.id,
            performed_by=performed_by,
            payload={"name": team.name, "code": team.code},
        )
        self.db.commit()
        self.db.refresh(team)
        return team

    def update_team(self, team_id: UUID, data: PaintingTeamUpdate, performed_by: UUID) -> PaintingTeam:
        team = self.get_team(team_id)
        if data.code and data.code != team.code:
            existing = self.db.query(PaintingTeam).filter(PaintingTeam.code == data.code).first()
            if existing:
                raise ConflictException("Painting team code already exists")

        if data.name is not None:
            team.name = data.name
        if data.code is not None:
            team.code = data.code
        if data.is_active is not None:
            team.is_active = data.is_active

        self.audit_service.log(
            action=AuditAction.UPDATE,
            entity_type="painting_team",
            entity_id=team.id,
            performed_by=performed_by,
            payload={"name": team.name, "code": team.code, "is_active": team.is_active},
        )
        self.db.commit()
        self.db.refresh(team)
        return team

    def add_member(
        self, team_id: UUID, data: PaintingTeamMemberCreate, performed_by: UUID
    ) -> PaintingTeamMember:
        team = self.get_team(team_id)

        existing = (
            self.db.query(PaintingTeamMember)
            .filter(PaintingTeamMember.code == data.code)
            .first()
        )
        if existing:
            raise ConflictException("Painting member code already exists")

        member = PaintingTeamMember(
            painting_team_id=team.id,
            name=data.name,
            code=data.code,
            phone=data.phone,
        )
        self.db.add(member)
        self.db.flush()

        self.audit_service.log(
            action=AuditAction.CREATE,
            entity_type="painting_team_member",
            entity_id=member.id,
            performed_by=performed_by,
            payload={
                "painting_team_id": str(team.id),
                "name": data.name,
                "code": data.code,
                "phone": data.phone,
            },
        )
        self.db.commit()
        self.db.refresh(member)
        return member

    def update_member(
        self,
        team_id: UUID,
        member_id: UUID,
        data: PaintingTeamMemberUpdate,
        performed_by: UUID,
    ) -> PaintingTeamMember:
        team = self.get_team(team_id)
        member = (
            self.db.query(PaintingTeamMember)
            .filter(
                PaintingTeamMember.id == member_id,
                PaintingTeamMember.painting_team_id == team.id,
            )
            .first()
        )
        if not member:
            raise NotFoundException("Painting team member not found")

        if data.code and data.code != member.code:
            existing = (
                self.db.query(PaintingTeamMember)
                .filter(PaintingTeamMember.code == data.code)
                .first()
            )
            if existing:
                raise ConflictException("Painting member code already exists")

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
            entity_type="painting_team_member",
            entity_id=member.id,
            performed_by=performed_by,
            payload={
                "painting_team_id": str(team.id),
                "name": member.name,
                "code": member.code,
                "phone": member.phone,
                "is_active": member.is_active,
            },
        )
        self.db.commit()
        self.db.refresh(member)
        return member

    def deactivate_member(
        self, team_id: UUID, member_id: UUID, performed_by: UUID
    ) -> PaintingTeamMember:
        return self.update_member(
            team_id, member_id, PaintingTeamMemberUpdate(is_active=False), performed_by
        )

    def resolve_by_code(self, code: str) -> PaintingTeamMember:
        member = (
            self.db.query(PaintingTeamMember)
            .join(PaintingTeam, PaintingTeam.id == PaintingTeamMember.painting_team_id)
            .filter(
                PaintingTeamMember.code == code,
                PaintingTeamMember.is_active.is_(True),
                PaintingTeam.is_active.is_(True),
            )
            .first()
        )
        if not member:
            raise NotFoundException("Painting team member not found")
        return member
