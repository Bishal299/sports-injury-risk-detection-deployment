from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import require_roles
from app.models.user import User, UserRole
from app.schemas.user import (
    AdminPasswordChange,
    AdminSelfProfileResponse,
    AdminSelfProfileUpdate,
)
from app.utils.security import hash_password, verify_password


router = APIRouter(prefix="/admin/profile", tags=["Admin Profile"])


def _admin_profile_response(user: User) -> AdminSelfProfileResponse:
    return AdminSelfProfileResponse(
        user_id=user.user_id,
        name=user.name,
        email=user.email,
        role=user.role,
        phone=user.phone,
        profile_image=user.profile_image,
        created_at=user.created_at,
        status="ACTIVE",
        last_login=None,
        has_local_password=bool(user.password),
    )


@router.get("", response_model=AdminSelfProfileResponse)
def get_admin_profile(
    admin_user: User = Depends(require_roles(UserRole.ADMINISTRATOR)),
):
    return _admin_profile_response(admin_user)


@router.put("", response_model=AdminSelfProfileResponse)
def update_admin_profile(
    profile_data: AdminSelfProfileUpdate,
    admin_user: User = Depends(require_roles(UserRole.ADMINISTRATOR)),
    db: Session = Depends(get_db),
):
    name = profile_data.name.strip()
    if not name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Full name is required",
        )

    admin_user.name = name
    admin_user.phone = profile_data.phone
    admin_user.profile_image = profile_data.profile_image

    db.commit()
    db.refresh(admin_user)

    return _admin_profile_response(admin_user)


@router.post("/password")
def change_admin_password(
    password_data: AdminPasswordChange,
    admin_user: User = Depends(require_roles(UserRole.ADMINISTRATOR)),
    db: Session = Depends(get_db),
):
    if not admin_user.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password changes are not available for this login method",
        )

    if password_data.new_password != password_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match",
        )

    if not verify_password(password_data.current_password, admin_user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    admin_user.password = hash_password(password_data.new_password)
    db.commit()

    return {"message": "Password updated successfully"}
