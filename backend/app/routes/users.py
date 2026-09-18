from fastapi import APIRouter, Depends

from app.dependencies.auth import get_current_user
from app.database import get_db
from app.schemas.user import UserResponse, UserUpdate
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


@router.get(
    "/me",
    response_model=UserResponse
)
def get_me(
    current_user=Depends(get_current_user)
):
    return current_user


@router.put(
    "/me",
    response_model=UserResponse
)
def update_me(
    user_data: UserUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user_data.name is not None:
        current_user.name = user_data.name

    if user_data.phone is not None:
        current_user.phone = user_data.phone

    if user_data.profile_image is not None:
        current_user.profile_image = user_data.profile_image

    db.commit()
    db.refresh(current_user)

    return current_user
