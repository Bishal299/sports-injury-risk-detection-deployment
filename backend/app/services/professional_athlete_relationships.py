from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.athlete import Athlete
from app.models.professional_athlete_relationship import (
    ProfessionalAthleteRelationship,
    ProfessionalAthleteRelationshipRole,
    ProfessionalAthleteRelationshipStatus,
)
from app.models.professional_profile import (
    ProfessionalProfile,
    ProfessionalVerificationStatus,
)
from app.models.user import User, UserRole


ROLE_MAP = {
    ProfessionalAthleteRelationshipRole.COACH.value: UserRole.COACH,
    ProfessionalAthleteRelationshipRole.PHYSIOTHERAPIST.value: UserRole.PHYSIOTHERAPIST,
    ProfessionalAthleteRelationshipRole.SPORTS_SCIENTIST.value: UserRole.SPORTS_SCIENTIST,
}


def _normalize_role(professional_role: str) -> str:
    if hasattr(professional_role, "value"):
        professional_role = professional_role.value

    role = str(professional_role).strip().upper()
    if role not in ROLE_MAP:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid professional role"
        )

    return role


def _get_verified_professional_user(
    db: Session,
    professional_user_id: UUID,
    professional_role: str,
) -> User:
    professional_user = (
        db.query(User)
        .filter(User.user_id == professional_user_id)
        .first()
    )

    if not professional_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Professional user not found"
        )

    expected_user_role = ROLE_MAP[professional_role]
    if professional_user.role != expected_user_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Verified professional role required"
        )

    professional_profile = (
        db.query(ProfessionalProfile)
        .filter(
            ProfessionalProfile.user_id == professional_user_id,
            ProfessionalProfile.professional_role == professional_role,
            ProfessionalProfile.verification_status == ProfessionalVerificationStatus.VERIFIED.value,
        )
        .first()
    )

    if not professional_profile:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Verified professional profile required"
        )

    return professional_user


def _get_athlete(db: Session, athlete_id: UUID) -> Athlete:
    athlete = (
        db.query(Athlete)
        .filter(Athlete.athlete_id == athlete_id)
        .first()
    )

    if not athlete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Athlete not found"
        )

    return athlete


def _ensure_athlete_owner(
    db: Session,
    relationship: ProfessionalAthleteRelationship,
    athlete_user_id: UUID,
):
    athlete = (
        db.query(Athlete)
        .filter(
            Athlete.athlete_id == relationship.athlete_id,
            Athlete.user_id == athlete_user_id,
        )
        .first()
    )

    if not athlete:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Athlete authorization required"
        )


def create_request(
    db: Session,
    professional_user_id: UUID,
    athlete_id: UUID,
    professional_role: str,
    requested_by: UUID | None = None,
) -> ProfessionalAthleteRelationship:
    role = _normalize_role(professional_role)
    _get_verified_professional_user(db, professional_user_id, role)
    _get_athlete(db, athlete_id)

    existing = (
        db.query(ProfessionalAthleteRelationship)
        .filter(
            ProfessionalAthleteRelationship.professional_user_id == professional_user_id,
            ProfessionalAthleteRelationship.athlete_id == athlete_id,
            ProfessionalAthleteRelationship.professional_role == role,
            ProfessionalAthleteRelationship.status.in_([
                ProfessionalAthleteRelationshipStatus.PENDING.value,
                ProfessionalAthleteRelationshipStatus.ACTIVE.value,
            ]),
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A pending or active professional-athlete relationship already exists"
        )

    relationship = ProfessionalAthleteRelationship(
        professional_user_id=professional_user_id,
        athlete_id=athlete_id,
        professional_role=role,
        status=ProfessionalAthleteRelationshipStatus.PENDING.value,
        requested_by=requested_by or professional_user_id,
    )

    db.add(relationship)
    db.commit()
    db.refresh(relationship)

    return relationship


def get_relationship(
    db: Session,
    relationship_id: UUID,
) -> ProfessionalAthleteRelationship:
    relationship = (
        db.query(ProfessionalAthleteRelationship)
        .filter(ProfessionalAthleteRelationship.relationship_id == relationship_id)
        .first()
    )

    if not relationship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Professional-athlete relationship not found"
        )

    return relationship


def list_professional_relationships(
    db: Session,
    professional_user_id: UUID,
    professional_role: str | None = None,
    relationship_status: str | None = None,
) -> list[ProfessionalAthleteRelationship]:
    query = db.query(ProfessionalAthleteRelationship).filter(
        ProfessionalAthleteRelationship.professional_user_id == professional_user_id
    )

    if professional_role:
        query = query.filter(
            ProfessionalAthleteRelationship.professional_role == _normalize_role(professional_role)
        )

    if relationship_status:
        query = query.filter(ProfessionalAthleteRelationship.status == relationship_status)

    return query.order_by(ProfessionalAthleteRelationship.created_at.desc()).all()


def list_athlete_relationships(
    db: Session,
    athlete_id: UUID,
    professional_role: str | None = None,
    relationship_status: str | None = None,
) -> list[ProfessionalAthleteRelationship]:
    query = db.query(ProfessionalAthleteRelationship).filter(
        ProfessionalAthleteRelationship.athlete_id == athlete_id
    )

    if professional_role:
        query = query.filter(
            ProfessionalAthleteRelationship.professional_role == _normalize_role(professional_role)
        )

    if relationship_status:
        query = query.filter(ProfessionalAthleteRelationship.status == relationship_status)

    return query.order_by(ProfessionalAthleteRelationship.created_at.desc()).all()


def accept_request(
    db: Session,
    relationship_id: UUID,
    athlete_user_id: UUID,
) -> ProfessionalAthleteRelationship:
    relationship = get_relationship(db, relationship_id)
    _ensure_athlete_owner(db, relationship, athlete_user_id)

    if relationship.status != ProfessionalAthleteRelationshipStatus.PENDING.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending professional requests can be accepted"
        )

    now = datetime.now(timezone.utc)
    relationship.status = ProfessionalAthleteRelationshipStatus.ACTIVE.value
    relationship.responded_at = now
    relationship.accepted_at = now

    db.commit()
    db.refresh(relationship)

    return relationship


def reject_request(
    db: Session,
    relationship_id: UUID,
    athlete_user_id: UUID,
) -> ProfessionalAthleteRelationship:
    relationship = get_relationship(db, relationship_id)
    _ensure_athlete_owner(db, relationship, athlete_user_id)

    if relationship.status != ProfessionalAthleteRelationshipStatus.PENDING.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending professional requests can be rejected"
        )

    relationship.status = ProfessionalAthleteRelationshipStatus.REJECTED.value
    relationship.responded_at = datetime.now(timezone.utc)
    relationship.accepted_at = None

    db.commit()
    db.refresh(relationship)

    return relationship


def revoke_relationship(
    db: Session,
    relationship_id: UUID,
    athlete_user_id: UUID,
) -> ProfessionalAthleteRelationship:
    relationship = get_relationship(db, relationship_id)
    _ensure_athlete_owner(db, relationship, athlete_user_id)

    if relationship.status != ProfessionalAthleteRelationshipStatus.ACTIVE.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only active professional relationships can be revoked"
        )

    relationship.status = ProfessionalAthleteRelationshipStatus.REVOKED.value
    relationship.responded_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(relationship)

    return relationship


def check_active_relationship(
    db: Session,
    professional_user_id: UUID,
    athlete_id: UUID,
    professional_role: str,
) -> bool:
    role = _normalize_role(professional_role)

    return (
        db.query(ProfessionalAthleteRelationship)
        .filter(
            ProfessionalAthleteRelationship.professional_user_id == professional_user_id,
            ProfessionalAthleteRelationship.athlete_id == athlete_id,
            ProfessionalAthleteRelationship.professional_role == role,
            ProfessionalAthleteRelationship.status == ProfessionalAthleteRelationshipStatus.ACTIVE.value,
        )
        .first()
        is not None
    )
