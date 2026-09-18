from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.dependencies.auth import require_roles
from app.models.user import User, UserRole
from app.schemas.user import (
    AdminCreateAdministrator,
    AdminUserDetail,
    AdminUserListResponse,
    AdminUserSummary,
    UserResponse,
)
from app.utils.security import hash_password


router = APIRouter(prefix="/admin/users", tags=["Admin Users"])

SUPPORTED_ACCOUNT_STATUSES = {"ACTIVE"}


def _account_status(user: User) -> str:
    del user
    return "ACTIVE"


def _professional_status(user: User) -> str | None:
    statuses = [
        profile.verification_status
        for profile in (user.professional_profiles or [])
        if profile.verification_status
    ]
    if not statuses:
        return None
    if "VERIFIED" in statuses:
        return "VERIFIED"
    if "PENDING" in statuses:
        return "PENDING"
    if "REJECTED" in statuses:
        return "REJECTED"
    return statuses[0]


def _user_summary(user: User) -> AdminUserSummary:
    return AdminUserSummary(
        user_id=user.user_id,
        name=user.name,
        email=user.email,
        role=user.role,
        status=_account_status(user),
        created_at=user.created_at,
        professional_status=_professional_status(user),
    )


def _safe_athlete_profile(user: User) -> dict | None:
    athlete = user.athlete
    if not athlete:
        return None
    return {
        "athlete_id": athlete.athlete_id,
        "sport": athlete.sport,
        "position": athlete.position,
        "age": athlete.age,
        "height": athlete.height,
        "weight": athlete.weight,
        "training_load": athlete.training_load,
        "flexibility": athlete.flexibility,
        "strength": athlete.strength,
        "balance": athlete.balance,
        "endurance": athlete.endurance,
    }


def _safe_professional_profiles(user: User) -> list[dict]:
    return [
        {
            "professional_profile_id": profile.professional_profile_id,
            "professional_role": profile.professional_role,
            "verification_status": profile.verification_status,
            "primary_sport": profile.primary_sport,
            "specialization": profile.specialization,
            "organization": profile.organization,
            "years_of_experience": profile.years_of_experience,
            "professional_bio": profile.professional_bio,
        }
        for profile in (user.professional_profiles or [])
    ]


def _safe_professional_requests(user: User) -> list[dict]:
    return [
        {
            "request_id": request.request_id,
            "requested_role": request.requested_role,
            "status": request.status,
            "primary_sport": request.primary_sport,
            "organization": request.organization,
            "submitted_at": request.submitted_at,
            "reviewed_at": request.reviewed_at,
        }
        for request in (user.professional_role_requests or [])
    ]


@router.get("", response_model=AdminUserListResponse)
def list_admin_users(
    search: str | None = Query(default=None, max_length=120),
    role: UserRole | None = Query(default=None),
    account_status: str | None = Query(default=None),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    admin_user: User = Depends(require_roles(UserRole.ADMINISTRATOR)),
    db: Session = Depends(get_db),
):
    del admin_user

    normalized_status = account_status.upper() if account_status else None
    if normalized_status and normalized_status not in SUPPORTED_ACCOUNT_STATUSES:
        return AdminUserListResponse(users=[], total=0, limit=limit, offset=offset)

    query = (
        db.query(User)
        .options(
            joinedload(User.athlete),
            joinedload(User.professional_profiles),
            joinedload(User.professional_role_requests),
        )
    )

    if search:
        search_term = f"%{search.strip()}%"
        if search_term != "%%":
            query = query.filter(or_(User.name.ilike(search_term), User.email.ilike(search_term)))

    if role:
        query = query.filter(User.role == role)

    total = query.with_entities(func.count(User.user_id)).scalar() or 0
    users = (
        query.order_by(User.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return AdminUserListResponse(
        users=[_user_summary(user) for user in users],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{user_id}", response_model=AdminUserDetail)
def get_admin_user_detail(
    user_id: UUID,
    admin_user: User = Depends(require_roles(UserRole.ADMINISTRATOR)),
    db: Session = Depends(get_db),
):
    del admin_user
    user = (
        db.query(User)
        .options(
            joinedload(User.athlete),
            joinedload(User.professional_profiles),
            joinedload(User.professional_role_requests),
        )
        .filter(User.user_id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    summary = _user_summary(user).model_dump()
    return AdminUserDetail(
        **summary,
        phone=user.phone,
        profile_image=user.profile_image,
        athlete_profile=_safe_athlete_profile(user),
        professional_profiles=_safe_professional_profiles(user),
        professional_requests=_safe_professional_requests(user),
    )


@router.post("/administrators", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_administrator(
    user_data: AdminCreateAdministrator,
    admin_user: User = Depends(require_roles(UserRole.ADMINISTRATOR)),
    db: Session = Depends(get_db),
):
    del admin_user

    name = user_data.name.strip()
    if not name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Full name is required",
        )

    if user_data.password != user_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match",
        )

    existing_user = (
        db.query(User)
        .filter(func.lower(User.email) == user_data.email.lower())
        .first()
    )
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user = User(
        name=name,
        email=user_data.email,
        password=hash_password(user_data.password),
        role=UserRole.ADMINISTRATOR,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
