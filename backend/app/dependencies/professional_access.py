from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.professional_athlete_relationship import ProfessionalAthleteRelationship
from app.models.professional_profile import ProfessionalProfile, ProfessionalVerificationStatus
from app.models.user import User
from app.services.professional_athlete_relationships import (
    ROLE_MAP,
    _normalize_role,
    check_active_relationship,
)


ROLE_PERMISSIONS = {
    "COACH": {
        "athlete_profile",
        "risk_results",
        "videos",
        "analyses",
        "performance_information",
        "reports",
    },
    "PHYSIOTHERAPIST": {
        "athlete_profile",
        "risk_results",
        "videos",
        "analyses",
        "injury_information",
        "rehabilitation",
        "recovery",
        "movement_analytics",
        "physiotherapist_notes",
        "recovery_reports",
    },
    "SPORTS_SCIENTIST": {
        "biomechanical_data",
        "performance_analytics",
        "movement_trends",
        "statistical_analysis",
    },
}


def normalize_professional_role(professional_role: str) -> str:
    return _normalize_role(professional_role)


def require_role_permission(professional_role: str, permission: str) -> str:
    role = normalize_professional_role(professional_role)
    if permission not in ROLE_PERMISSIONS.get(role, set()):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Professional role permission required",
        )
    return role


def get_verified_professional_profile(
    db: Session,
    current_user: User,
    professional_role: str,
) -> ProfessionalProfile:
    role = normalize_professional_role(professional_role)
    expected_user_role = ROLE_MAP.get(role)

    if expected_user_role is None or current_user.role != expected_user_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Verified professional role required",
        )

    profile = (
        db.query(ProfessionalProfile)
        .filter(
            ProfessionalProfile.user_id == current_user.user_id,
            ProfessionalProfile.professional_role == role,
            ProfessionalProfile.verification_status == ProfessionalVerificationStatus.VERIFIED.value,
        )
        .first()
    )

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Verified professional profile required",
        )

    return profile


def has_active_professional_relationship(
    db: Session,
    professional_user_id: UUID,
    athlete_id: UUID,
    professional_role: str,
) -> bool:
    return check_active_relationship(
        db=db,
        professional_user_id=professional_user_id,
        athlete_id=athlete_id,
        professional_role=professional_role,
    )


def require_active_professional_relationship(
    db: Session,
    current_user: User,
    athlete_id: UUID,
    professional_role: str,
    permission: str | None = None,
):
    role = require_role_permission(professional_role, permission) if permission else normalize_professional_role(professional_role)
    get_verified_professional_profile(db, current_user, role)

    if not has_active_professional_relationship(
        db=db,
        professional_user_id=current_user.user_id,
        athlete_id=athlete_id,
        professional_role=role,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Active professional-athlete relationship required"
        )


def require_active_professional_access(
    db: Session,
    current_user: User,
    athlete_id: UUID,
    professional_role: str,
    permission: str,
) -> ProfessionalAthleteRelationship:
    role = require_role_permission(professional_role, permission)
    get_verified_professional_profile(db, current_user, role)

    relationship = (
        db.query(ProfessionalAthleteRelationship)
        .filter(
            ProfessionalAthleteRelationship.professional_user_id == current_user.user_id,
            ProfessionalAthleteRelationship.athlete_id == athlete_id,
            ProfessionalAthleteRelationship.professional_role == role,
            ProfessionalAthleteRelationship.status == "ACTIVE",
        )
        .first()
    )

    if not relationship:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Active professional-athlete relationship required",
        )

    return relationship
