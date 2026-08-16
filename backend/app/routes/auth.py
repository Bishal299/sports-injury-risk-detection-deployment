import os

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User, UserRole

from app.schemas.user import (
    UserCreate,
    UserResponse,
    UserLogin,
    TokenResponse,
    GoogleLoginRequest
)

from app.utils.security import (
    hash_password,
    verify_password,
    create_access_token
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


# =========================================================
# NORMAL REGISTER
# =========================================================

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):

    # Check if email already exists
    existing_user = (
        db.query(User)
        .filter(User.email == user_data.email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Hash password
    hashed_password = hash_password(user_data.password)

    # Create user
    new_user = User(
        name=user_data.name,
        email=user_data.email,
        password=hashed_password,
        role=user_data.role,
        phone=user_data.phone,
        profile_image=user_data.profile_image
    )

    # Save
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


# =========================================================
# NORMAL LOGIN
# =========================================================

@router.post(
    "/login",
    response_model=TokenResponse
)
def login_user(
    user_data: UserLogin,
    db: Session = Depends(get_db)
):

    # Find user
    user = (
        db.query(User)
        .filter(User.email == user_data.email)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Google users don't have a password
    if user.password is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This account uses Google Login. Please continue with Google."
        )

    # Verify password
    if not verify_password(
        user_data.password,
        user.password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Create application JWT
    access_token = create_access_token(
        data={
            "sub": str(user.user_id),
            "role": user.role.value
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


# =========================================================
# GOOGLE LOGIN
# =========================================================

@router.post(
    "/google",
    response_model=TokenResponse
)
def google_login(
    google_data: GoogleLoginRequest,
    db: Session = Depends(get_db)
):

    print("Google endpoint reached")
    print("Credential received:", bool(google_data.credential))


    # -----------------------------------------------------
    # Get Google Client ID
    # -----------------------------------------------------

    client_id = os.getenv("GOOGLE_CLIENT_ID")

    print("Google Client ID configured:", bool(client_id))

    if not client_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google Client ID is not configured"
        )


    # -----------------------------------------------------
    # Verify Google credential
    # -----------------------------------------------------

    try:

        idinfo = id_token.verify_oauth2_token(
            google_data.credential,
            google_requests.Request(),
            client_id
        )

    except ValueError as error:

        print("Google credential verification failed:", error)

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google credential"
        )


    # -----------------------------------------------------
    # Extract Google information
    # -----------------------------------------------------

    google_email = idinfo.get("email")
    google_name = idinfo.get("name")
    google_picture = idinfo.get("picture")

    email_verified = idinfo.get(
        "email_verified",
        False
    )


    # -----------------------------------------------------
    # Validate Google account
    # -----------------------------------------------------

    if not google_email:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google account email not found"
        )


    if not email_verified:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google email is not verified"
        )


    # -----------------------------------------------------
    # Check existing user
    # -----------------------------------------------------

    user = (
        db.query(User)
        .filter(User.email == google_email)
        .first()
    )


    # -----------------------------------------------------
    # Create new Google user
    # -----------------------------------------------------

    if not user:

        user = User(
            name=google_name or "Google User",
            email=google_email,
            password=None,
            role=UserRole.ATHLETE,
            profile_image=google_picture
        )

        db.add(user)
        db.commit()
        db.refresh(user)

    else:

        # Update profile image/name if available
        if google_name:
            user.name = google_name

        if google_picture:
            user.profile_image = google_picture

        db.commit()
        db.refresh(user)


    # -----------------------------------------------------
    # Create OUR JWT
    # -----------------------------------------------------

    access_token = create_access_token(
        data={
            "sub": str(user.user_id),
            "role": user.role.value
        }
    )


    # -----------------------------------------------------
    # Return token
    # -----------------------------------------------------

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }