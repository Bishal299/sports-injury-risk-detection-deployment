from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import require_roles
from app.models.coach_profile import CoachProfile, CoachVerificationStatus
from app.models.professional_profile import (
    ProfessionalProfile,
    ProfessionalVerificationStatus,
)
from app.models.professional_role_request import (
    ProfessionalRequestedRole,
    ProfessionalRoleRequest,
    ProfessionalRoleRequestStatus,
)
from app.models.user import User, UserRole
from app.models.notification import NotificationType
from app.schemas.professional_role_request import (
    ProfessionalRoleRequestReject,
    ProfessionalRoleRequestResponse,
)
from app.services.notifications import create_notification


router = APIRouter(
    prefix="/admin/professional-role-requests",
    tags=["Admin Professional Role Requests"]
)


def _get_role_request(request_id: UUID, db: Session) -> ProfessionalRoleRequest:
    role_request = (
        db.query(ProfessionalRoleRequest)
        .filter(ProfessionalRoleRequest.request_id == request_id)
        .first()
    )

    if not role_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Professional role request not found"
        )

    return role_request


def _ensure_admin_user(admin_user: User):
    if admin_user.role != UserRole.ADMINISTRATOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )


def _map_requested_role_to_user_role(requested_role: str) -> UserRole:
    role_map = {
        ProfessionalRequestedRole.COACH.value: UserRole.COACH,
        ProfessionalRequestedRole.PHYSIOTHERAPIST.value: UserRole.PHYSIOTHERAPIST,
        ProfessionalRequestedRole.SPORTS_SCIENTIST.value: UserRole.SPORTS_SCIENTIST,
    }

    return role_map[requested_role]


def _upsert_professional_profile(
    role_request: ProfessionalRoleRequest,
    verification_status: ProfessionalVerificationStatus,
    db: Session,
) -> ProfessionalProfile:
    professional_profile = (
        db.query(ProfessionalProfile)
        .filter(
            ProfessionalProfile.user_id == role_request.user_id,
            ProfessionalProfile.professional_role == role_request.requested_role,
        )
        .first()
    )

    if not professional_profile:
        professional_profile = ProfessionalProfile(
            user_id=role_request.user_id,
            professional_role=role_request.requested_role,
        )
        db.add(professional_profile)

    professional_profile.verification_status = verification_status.value
    professional_profile.primary_sport = role_request.primary_sport
    professional_profile.years_of_experience = role_request.years_of_experience
    professional_profile.specialization = role_request.specialization
    professional_profile.organization = role_request.organization
    professional_profile.certifications = role_request.certifications
    professional_profile.professional_bio = role_request.professional_bio

    return professional_profile


@router.get(
    "",
    response_model=list[ProfessionalRoleRequestResponse],
)
def list_professional_role_requests(
    request_status: ProfessionalRoleRequestStatus | None = None,
    requested_role: ProfessionalRequestedRole | None = None,
    search: str | None = Query(default=None, max_length=120),
    admin_user: User = Depends(require_roles(UserRole.ADMINISTRATOR)),
    db: Session = Depends(get_db),
):
    _ensure_admin_user(admin_user)

    query = db.query(ProfessionalRoleRequest).join(
        User,
        ProfessionalRoleRequest.user_id == User.user_id,
    )

    if request_status:
        query = query.filter(ProfessionalRoleRequest.status == request_status.value)

    if requested_role:
        query = query.filter(ProfessionalRoleRequest.requested_role == requested_role.value)

    if search:
        search_term = f"%{search.strip()}%"
        if search_term != "%%":
            query = query.filter(
                or_(
                    User.name.ilike(search_term),
                    User.email.ilike(search_term),
                    User.phone.ilike(search_term),
                    ProfessionalRoleRequest.primary_sport.ilike(search_term),
                    ProfessionalRoleRequest.organization.ilike(search_term),
                    ProfessionalRoleRequest.specialization.ilike(search_term),
                )
            )

    return query.order_by(ProfessionalRoleRequest.submitted_at.desc()).all()


@router.get(
    "/{request_id}",
    response_model=ProfessionalRoleRequestResponse,
)
def get_professional_role_request(
    request_id: UUID,
    admin_user: User = Depends(require_roles(UserRole.ADMINISTRATOR)),
    db: Session = Depends(get_db),
):
    _ensure_admin_user(admin_user)
    return _get_role_request(request_id, db)


@router.post(
    "/{request_id}/approve",
    response_model=ProfessionalRoleRequestResponse,
)
def approve_professional_role_request(
    request_id: UUID,
    admin_user: User = Depends(require_roles(UserRole.ADMINISTRATOR)),
    db: Session = Depends(get_db),
):
    _ensure_admin_user(admin_user)
    role_request = _get_role_request(request_id, db)

    if role_request.status != ProfessionalRoleRequestStatus.PENDING.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending professional role requests can be approved"
        )

    user = role_request.user
    user.role = _map_requested_role_to_user_role(role_request.requested_role)

    role_request.status = ProfessionalRoleRequestStatus.APPROVED.value
    role_request.reviewed_at = datetime.now(timezone.utc)
    role_request.reviewed_by = admin_user.user_id
    role_request.rejection_reason = None

    _upsert_professional_profile(
        role_request,
        ProfessionalVerificationStatus.VERIFIED,
        db,
    )

    if role_request.requested_role == ProfessionalRequestedRole.COACH.value:
        coach_profile = (
            db.query(CoachProfile)
            .filter(CoachProfile.user_id == user.user_id)
            .first()
        )

        if not coach_profile:
            coach_profile = CoachProfile(user_id=user.user_id)
            db.add(coach_profile)

        coach_profile.primary_sport = role_request.primary_sport
        coach_profile.years_of_experience = role_request.years_of_experience
        coach_profile.coaching_specialization = role_request.specialization
        coach_profile.organization = role_request.organization
        coach_profile.certifications = role_request.certifications
        coach_profile.professional_bio = role_request.professional_bio
        coach_profile.verification_status = CoachVerificationStatus.VERIFIED.value

    create_notification(
        db,
        recipient_user_id=role_request.user_id,
        notification_type=NotificationType.PROFESSIONAL_ROLE_APPROVED,
        title="Professional role approved",
        message=f"Your {role_request.requested_role.replace('_', ' ').title()} application was approved.",
        actor_user_id=admin_user.user_id,
        entity_type="professional_role_request",
        entity_id=role_request.request_id,
        action_url="/request-professional-role",
    )

    db.commit()
    db.refresh(role_request)

    return role_request


@router.post(
    "/{request_id}/reject",
    response_model=ProfessionalRoleRequestResponse,
)
def reject_professional_role_request(
    request_id: UUID,
    rejection_data: ProfessionalRoleRequestReject,
    admin_user: User = Depends(require_roles(UserRole.ADMINISTRATOR)),
    db: Session = Depends(get_db),
):
    _ensure_admin_user(admin_user)
    role_request = _get_role_request(request_id, db)

    if role_request.status != ProfessionalRoleRequestStatus.PENDING.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending professional role requests can be rejected"
        )

    rejection_reason = (rejection_data.rejection_reason or "").strip()
    if not rejection_reason:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Rejection reason is required",
        )

    role_request.status = ProfessionalRoleRequestStatus.REJECTED.value
    role_request.reviewed_at = datetime.now(timezone.utc)
    role_request.reviewed_by = admin_user.user_id
    role_request.rejection_reason = rejection_reason

    _upsert_professional_profile(
        role_request,
        ProfessionalVerificationStatus.REJECTED,
        db,
    )

    if role_request.requested_role == ProfessionalRequestedRole.COACH.value:
        coach_profile = (
            db.query(CoachProfile)
            .filter(CoachProfile.user_id == role_request.user_id)
            .first()
        )
        if coach_profile:
            coach_profile.verification_status = CoachVerificationStatus.REJECTED.value

    create_notification(
        db,
        recipient_user_id=role_request.user_id,
        notification_type=NotificationType.PROFESSIONAL_ROLE_REJECTED,
        title="Professional role rejected",
        message=f"Your {role_request.requested_role.replace('_', ' ').title()} application was rejected.",
        actor_user_id=admin_user.user_id,
        entity_type="professional_role_request",
        entity_id=role_request.request_id,
        action_url="/request-professional-role",
    )

    db.commit()
    db.refresh(role_request)

    return role_request
