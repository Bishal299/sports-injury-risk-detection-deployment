import os

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User, UserRole
from app.models.coach_profile import CoachProfile, CoachVerificationStatus
from app.models.professional_profile import ProfessionalProfile, ProfessionalVerificationStatus

from app.schemas.user import (
    UserCreate,
    UserResponse,
    UserLogin,
    TokenResponse,
    AuthMeResponse,
    GoogleLoginRequest,
    VerifyPortalRequest,
    VerifyPortalResponse,
)

from app.utils.security import (
    hash_password,
    verify_password,
    create_access_token,
    set_auth_cookie,
    clear_auth_cookie,
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
    if user_data.role != UserRole.ATHLETE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Professional roles require admin approval"
        )

    normalized_email = user_data.email.strip().lower()

    # Check if email already exists
    existing_user = (
        db.query(User)
        .filter(func.lower(User.email) == normalized_email)
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
        name=user_data.name.strip(),
        email=normalized_email,
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
    response: Response,
    db: Session = Depends(get_db)
):
    normalized_email = user_data.email.strip().lower()

    # Find user (case-insensitive)
    user = (
        db.query(User)
        .filter(func.lower(User.email) == normalized_email)
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

    # Create application JWT (absolute 24 hours, non-sliding)
    access_token = create_access_token(
        data={
            "sub": str(user.user_id),
            "role": user.role.value
        }
    )

    # Set HttpOnly browser-session cookie
    set_auth_cookie(response, access_token)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user,
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
    response: Response,
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


    clean_google_email = google_email.strip().lower()

    # -----------------------------------------------------
    # Check existing user
    # -----------------------------------------------------

    user = (
        db.query(User)
        .filter(func.lower(User.email) == clean_google_email)
        .first()
    )


    # -----------------------------------------------------
    # Create new Google user
    # -----------------------------------------------------

    if not user:

        user = User(
            name=google_name or "Google User",
            email=clean_google_email,
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
    # Create OUR JWT (absolute 24 hours, non-sliding)
    # -----------------------------------------------------

    access_token = create_access_token(
        data={
            "sub": str(user.user_id),
            "role": user.role.value
        }
    )

    # Set HttpOnly browser-session cookie
    set_auth_cookie(response, access_token)

    # -----------------------------------------------------
    # Return token
    # -----------------------------------------------------

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user,
    }


# =========================================================
# AUTH ME & LOGOUT
# =========================================================

@router.get(
    "/me",
    response_model=AuthMeResponse
)
def get_authenticated_user(
    current_user: User = Depends(get_current_user)
):
    return AuthMeResponse(
        id=str(current_user.user_id),
        user_id=str(current_user.user_id),
        name=current_user.name,
        email=current_user.email,
        role=current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role),
        phone=current_user.phone,
        profile_image=current_user.profile_image,
    )


@router.post(
    "/logout"
)
def logout_user(
    response: Response
):
    clear_auth_cookie(response)
    return {"message": "Logged out successfully"}



# =========================================================
# ROLE-BASED PORTAL ACCESS VERIFICATION
# =========================================================

def _get_default_route_for_user_role(role: UserRole) -> str:
    if role == UserRole.ADMINISTRATOR:
        return "/admin/dashboard"
    if role == UserRole.COACH:
        return "/coach/dashboard"
    if role == UserRole.PHYSIOTHERAPIST:
        return "/physiotherapist/dashboard"
    if role == UserRole.SPORTS_SCIENTIST:
        return "/sports-scientist/dashboard"
    return "/dashboard"


@router.post(
    "/verify-portal",
    response_model=VerifyPortalResponse
)
def verify_portal_access(
    request_data: VerifyPortalRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    requested = request_data.portal_role.strip().upper().replace(" ", "_")

    portal_map = {
        "ATHLETE": UserRole.ATHLETE,
        "COACH": UserRole.COACH,
        "PHYSIOTHERAPIST": UserRole.PHYSIOTHERAPIST,
        "SPORTS_SCIENTIST": UserRole.SPORTS_SCIENTIST,
        "ADMINISTRATOR": UserRole.ADMINISTRATOR,
        "ADMIN": UserRole.ADMINISTRATOR,
    }

    if requested not in portal_map:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid portal role requested"
        )

    target_role = portal_map[requested]
    is_athlete = (current_user.role == UserRole.ATHLETE)
    user_default_route = _get_default_route_for_user_role(current_user.role)

    # 1. ATHLETE
    if target_role == UserRole.ATHLETE:
        if current_user.role == UserRole.ATHLETE:
            return VerifyPortalResponse(
                authorized=True,
                portal_role="ATHLETE",
                user_role=current_user.role.value,
                default_route="/dashboard",
                can_continue_as_athlete=True,
            )
        else:
            return VerifyPortalResponse(
                authorized=False,
                portal_role="ATHLETE",
                user_role=current_user.role.value,
                headline="Athlete access unavailable",
                message="This account is assigned to a different role portal.",
                secondary_message="Please select your authorized portal to sign in.",
                default_route=user_default_route,
                can_continue_as_athlete=False,
            )

    # 2. COACH
    if target_role == UserRole.COACH:
        is_verified_coach = False
        if current_user.role == UserRole.COACH:
            coach_profile = (
                db.query(CoachProfile)
                .filter(CoachProfile.user_id == current_user.user_id)
                .first()
            )
            is_verified_coach = bool(
                coach_profile
                and coach_profile.verification_status == CoachVerificationStatus.VERIFIED.value
            )

        if is_verified_coach:
            return VerifyPortalResponse(
                authorized=True,
                portal_role="COACH",
                user_role=current_user.role.value,
                default_route="/coach/dashboard",
                can_continue_as_athlete=is_athlete,
            )
        else:
            return VerifyPortalResponse(
                authorized=False,
                portal_role="COACH",
                user_role=current_user.role.value,
                headline="Coach access unavailable",
                message="This account does not currently have active Coach access.",
                secondary_message="Professional roles require approval from an administrator.",
                default_route=user_default_route,
                can_continue_as_athlete=is_athlete,
                request_role_url="/request-professional-role/coach" if is_athlete else None,
            )

    # 3. PHYSIOTHERAPIST
    if target_role == UserRole.PHYSIOTHERAPIST:
        is_verified_physio = False
        if current_user.role == UserRole.PHYSIOTHERAPIST:
            physio_profile = (
                db.query(ProfessionalProfile)
                .filter(
                    ProfessionalProfile.user_id == current_user.user_id,
                    ProfessionalProfile.professional_role == "PHYSIOTHERAPIST",
                    ProfessionalProfile.verification_status == ProfessionalVerificationStatus.VERIFIED.value,
                )
                .first()
            )
            is_verified_physio = bool(physio_profile)

        if is_verified_physio:
            return VerifyPortalResponse(
                authorized=True,
                portal_role="PHYSIOTHERAPIST",
                user_role=current_user.role.value,
                default_route="/physiotherapist/dashboard",
                can_continue_as_athlete=is_athlete,
            )
        else:
            return VerifyPortalResponse(
                authorized=False,
                portal_role="PHYSIOTHERAPIST",
                user_role=current_user.role.value,
                headline="Physiotherapist access unavailable",
                message="Physiotherapist access is not active for this account.",
                secondary_message="Professional roles require approval from an administrator.",
                default_route=user_default_route,
                can_continue_as_athlete=is_athlete,
                request_role_url="/request-professional-role/physiotherapist" if is_athlete else None,
            )

    # 4. SPORTS_SCIENTIST
    if target_role == UserRole.SPORTS_SCIENTIST:
        is_verified_scientist = False
        if current_user.role == UserRole.SPORTS_SCIENTIST:
            scientist_profile = (
                db.query(ProfessionalProfile)
                .filter(
                    ProfessionalProfile.user_id == current_user.user_id,
                    ProfessionalProfile.professional_role == "SPORTS_SCIENTIST",
                    ProfessionalProfile.verification_status == ProfessionalVerificationStatus.VERIFIED.value,
                )
                .first()
            )
            is_verified_scientist = bool(scientist_profile)

        if is_verified_scientist:
            return VerifyPortalResponse(
                authorized=True,
                portal_role="SPORTS_SCIENTIST",
                user_role=current_user.role.value,
                default_route="/sports-scientist/dashboard",
                can_continue_as_athlete=is_athlete,
            )
        else:
            return VerifyPortalResponse(
                authorized=False,
                portal_role="SPORTS_SCIENTIST",
                user_role=current_user.role.value,
                headline="Sports Scientist access unavailable",
                message="Sports Scientist access is not active for this account.",
                secondary_message="Professional roles require approval from an administrator.",
                default_route=user_default_route,
                can_continue_as_athlete=is_athlete,
                request_role_url="/request-professional-role/sports-scientist" if is_athlete else None,
            )

    # 5. ADMINISTRATOR
    if target_role == UserRole.ADMINISTRATOR:
        if current_user.role == UserRole.ADMINISTRATOR:
            return VerifyPortalResponse(
                authorized=True,
                portal_role="ADMINISTRATOR",
                user_role=current_user.role.value,
                default_route="/admin/dashboard",
                can_continue_as_athlete=False,
            )
        else:
            return VerifyPortalResponse(
                authorized=False,
                portal_role="ADMINISTRATOR",
                user_role=current_user.role.value,
                headline="Administrator access unavailable",
                message="Administrator access is not available for this account.",
                secondary_message=None,
                default_route=user_default_route,
                can_continue_as_athlete=is_athlete,
                request_role_url=None,
            )
