import json
import os
import shutil
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.professional_role_request import (
    ProfessionalRequestedRole,
    ProfessionalRoleRequest,
    ProfessionalRoleRequestStatus,
)
from app.models.professional_profile import (
    ProfessionalProfile,
    ProfessionalVerificationStatus,
)
from app.models.user import User
from app.models.notification import NotificationType
from app.schemas.professional_role_request import (
    ProfessionalRoleRequestCreate,
    ProfessionalRoleRequestResponse,
    RequestedProfessionalRole,
)
from app.services.notifications import notify_admins


router = APIRouter(
    prefix="/professional-role-requests",
    tags=["Professional Role Requests"]
)

DOCUMENT_UPLOAD_DIR = "uploads/professional_documents"


def _ensure_no_pending_request_for_role(
    requested_role: str,
    current_user: User,
    db: Session,
):
    pending_request = (
        db.query(ProfessionalRoleRequest)
        .filter(
            ProfessionalRoleRequest.user_id == current_user.user_id,
            ProfessionalRoleRequest.requested_role == requested_role,
            ProfessionalRoleRequest.status == ProfessionalRoleRequestStatus.PENDING.value,
        )
        .first()
    )

    if pending_request:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already have a pending request for this professional role"
        )


def _upsert_pending_professional_profile(
    role_request: ProfessionalRoleRequest,
    db: Session,
):
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

    professional_profile.verification_status = ProfessionalVerificationStatus.PENDING.value
    professional_profile.primary_sport = role_request.primary_sport
    professional_profile.years_of_experience = role_request.years_of_experience
    professional_profile.specialization = role_request.specialization
    professional_profile.organization = role_request.organization
    professional_profile.certifications = role_request.certifications
    professional_profile.professional_bio = role_request.professional_bio

    return professional_profile


def _required_text(value: Optional[str]) -> bool:
    return bool(value and value.strip())


def _validate_role_request(request_data: ProfessionalRoleRequestCreate):
    if request_data.requested_role != RequestedProfessionalRole.SPORTS_SCIENTIST:
        return

    missing_fields = []
    if not _required_text(request_data.specialization):
        missing_fields.append("area of specialization")
    if request_data.years_of_experience is None:
        missing_fields.append("years of experience")
    if not _required_text(request_data.organization):
        missing_fields.append("current organization / institution")
    if not _required_text(request_data.professional_bio):
        missing_fields.append("professional bio / experience summary")
    if not _required_text(request_data.primary_sport):
        missing_fields.append("interested sports")
    if not _required_text(request_data.certifications):
        missing_fields.append("analytical expertise")

    if missing_fields:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Missing required Sports Scientist fields: {', '.join(missing_fields)}"
        )


def _create_request(
    request_data: ProfessionalRoleRequestCreate,
    current_user: User,
    db: Session,
) -> ProfessionalRoleRequest:
    _validate_role_request(request_data)
    _ensure_no_pending_request_for_role(
        request_data.requested_role.value,
        current_user,
        db,
    )

    role_request = ProfessionalRoleRequest(
        user_id=current_user.user_id,
        requested_role=request_data.requested_role.value,
        primary_sport=request_data.primary_sport,
        organization=request_data.organization,
        specialization=request_data.specialization,
        years_of_experience=request_data.years_of_experience,
        certifications=request_data.certifications,
        professional_bio=request_data.professional_bio,
        supporting_document_url=request_data.supporting_document_url,
        status=ProfessionalRoleRequestStatus.PENDING.value,
    )

    db.add(role_request)
    _upsert_pending_professional_profile(role_request, db)
    db.flush()
    notify_admins(
        db,
        notification_type=NotificationType.PROFESSIONAL_ROLE_REQUEST,
        title="New professional application",
        message=f"{current_user.name} submitted a {request_data.requested_role.value.replace('_', ' ').title()} application.",
        actor_user_id=current_user.user_id,
        entity_type="professional_role_request",
        entity_id=role_request.request_id,
        action_url="/admin/professional-requests",
    )
    db.commit()
    db.refresh(role_request)

    return role_request


def _save_supporting_document(document: UploadFile) -> str:
    os.makedirs(DOCUMENT_UPLOAD_DIR, exist_ok=True)

    _, extension = os.path.splitext(document.filename or "")
    safe_extension = extension.lower() if extension else ".bin"
    filename = f"{uuid.uuid4()}{safe_extension}"
    file_path = os.path.join(DOCUMENT_UPLOAD_DIR, filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(document.file, buffer)

    return f"/{file_path.replace(os.sep, '/')}"


@router.post(
    "",
    response_model=ProfessionalRoleRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
def submit_professional_role_request(
    request_data: ProfessionalRoleRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _create_request(request_data, current_user, db)


@router.post(
    "/sports-scientist",
    response_model=ProfessionalRoleRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
def submit_sports_scientist_application(
    requested_role: RequestedProfessionalRole = Form(RequestedProfessionalRole.SPORTS_SCIENTIST),
    full_name: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    specialization: Optional[str] = Form(None),
    years_of_experience: Optional[int] = Form(None),
    organization: Optional[str] = Form(None),
    professional_bio: Optional[str] = Form(None),
    primary_sport: Optional[str] = Form(None),
    interested_sports: Optional[str] = Form(None),
    analytical_expertise: Optional[str] = Form(None),
    supporting_document_url: Optional[str] = Form(None),
    supporting_document: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if requested_role != RequestedProfessionalRole.SPORTS_SCIENTIST:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This endpoint only accepts Sports Scientist applications"
        )

    document_references = []
    stored_document = None
    if supporting_document:
        stored_document = _save_supporting_document(supporting_document)
    elif supporting_document_url:
        stored_document = supporting_document_url

    if stored_document:
        document_references.append({
            "label": "Supporting Document",
            "url": stored_document,
        })

    if full_name:
        current_user.name = full_name
    if phone:
        current_user.phone = phone

    certification_lines = [
        f"Interested Sports: {interested_sports}" if interested_sports else None,
        f"Analytical Expertise: {analytical_expertise}" if analytical_expertise else None,
    ]

    request_data = ProfessionalRoleRequestCreate(
        requested_role=RequestedProfessionalRole.SPORTS_SCIENTIST,
        primary_sport=primary_sport,
        organization=organization,
        specialization=specialization,
        years_of_experience=years_of_experience,
        certifications="\n".join(line for line in certification_lines if line) or None,
        professional_bio=professional_bio,
        supporting_document_url=json.dumps(document_references) if document_references else None,
    )

    role_request = _create_request(request_data, current_user, db)
    db.refresh(current_user)

    return role_request


@router.post(
    "/coach",
    response_model=ProfessionalRoleRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
def submit_coach_application(
    requested_role: RequestedProfessionalRole = Form(RequestedProfessionalRole.COACH),
    full_name: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    primary_sport: Optional[str] = Form(None),
    other_sports: Optional[str] = Form(None),
    years_of_experience: Optional[int] = Form(None),
    coaching_specialization: Optional[str] = Form(None),
    organization: Optional[str] = Form(None),
    certifications: Optional[str] = Form(None),
    professional_bio: Optional[str] = Form(None),
    supporting_document: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if requested_role != RequestedProfessionalRole.COACH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This endpoint only accepts Coach applications"
        )

    document_url = None
    if supporting_document:
        document_url = _save_supporting_document(supporting_document)

    if full_name:
        current_user.name = full_name
    if phone:
        current_user.phone = phone

    specialization = coaching_specialization
    if other_sports:
        specialization = (
            f"{coaching_specialization}\nOther sports: {other_sports}"
            if coaching_specialization
            else f"Other sports: {other_sports}"
        )

    request_data = ProfessionalRoleRequestCreate(
        requested_role=RequestedProfessionalRole.COACH,
        primary_sport=primary_sport,
        organization=organization,
        specialization=specialization,
        years_of_experience=years_of_experience,
        certifications=certifications,
        professional_bio=professional_bio,
        supporting_document_url=document_url,
    )

    role_request = _create_request(request_data, current_user, db)
    db.refresh(current_user)

    return role_request


@router.post(
    "/physiotherapist",
    response_model=ProfessionalRoleRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
def submit_physiotherapist_application(
    requested_role: RequestedProfessionalRole = Form(RequestedProfessionalRole.PHYSIOTHERAPIST),
    full_name: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    primary_sport: Optional[str] = Form(None),
    other_sports: Optional[str] = Form(None),
    years_of_experience: Optional[int] = Form(None),
    sports_physiotherapy_experience: Optional[int] = Form(None),
    highest_qualification: Optional[str] = Form(None),
    qualification_other: Optional[str] = Form(None),
    specialization: Optional[str] = Form(None),
    specialization_other: Optional[str] = Form(None),
    registration_number: Optional[str] = Form(None),
    registration_authority: Optional[str] = Form(None),
    license_expiry_date: Optional[str] = Form(None),
    sports_worked_with: Optional[str] = Form(None),
    areas_of_expertise: Optional[str] = Form(None),
    organization: Optional[str] = Form(None),
    certifications: Optional[str] = Form(None),
    professional_bio: Optional[str] = Form(None),
    platform_statement: Optional[str] = Form(None),
    athlete_support_statement: Optional[str] = Form(None),
    supporting_document_url: Optional[str] = Form(None),
    license_document_url: Optional[str] = Form(None),
    qualification_document_url: Optional[str] = Form(None),
    certification_documents_url: Optional[str] = Form(None),
    supporting_document: Optional[UploadFile] = File(None),
    license_document: Optional[UploadFile] = File(None),
    qualification_document: Optional[UploadFile] = File(None),
    certification_documents: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if requested_role != RequestedProfessionalRole.PHYSIOTHERAPIST:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This endpoint only accepts Physiotherapist applications"
        )

    document_references = []
    for label, url_value, upload in [
        ("Professional Registration / License Document", license_document_url, license_document),
        ("Qualification Certificate", qualification_document_url, qualification_document),
        ("Relevant Certification Documents", certification_documents_url, certification_documents),
        ("Supporting Document", supporting_document_url, supporting_document),
    ]:
        stored_reference = None
        if upload:
            stored_reference = _save_supporting_document(upload)
        elif url_value:
            stored_reference = url_value

        if stored_reference:
            document_references.append({
                "label": label,
                "url": stored_reference,
            })

    document_reference = None
    if document_references:
        document_reference = json.dumps(document_references)

    if full_name:
        current_user.name = full_name
    if phone:
        current_user.phone = phone

    qualification_value = highest_qualification
    if highest_qualification == "Other" and qualification_other:
        qualification_value = f"Other: {qualification_other}"

    specialization_value = specialization
    if specialization == "Other" and specialization_other:
        specialization_value = f"Other: {specialization_other}"

    specialization_lines = [
        specialization_value,
    ]

    qualification_lines = [
        f"Highest Qualification: {qualification_value}" if qualification_value else None,
        f"Physiotherapy Specialization: {specialization_value}" if specialization_value else None,
        f"Professional Registration / License Number: {registration_number}" if registration_number else None,
        f"Registration Authority / Council: {registration_authority}" if registration_authority else None,
        f"License Expiry Date: {license_expiry_date}" if license_expiry_date else None,
        f"Years of Sports Physiotherapy Experience: {sports_physiotherapy_experience}" if sports_physiotherapy_experience is not None else None,
        f"Sports Worked With: {sports_worked_with}" if sports_worked_with else None,
        f"Other Sports / Areas: {other_sports}" if other_sports else None,
        f"Areas of Expertise: {areas_of_expertise}" if areas_of_expertise else None,
    ]
    combined_specialization = "\n".join(line for line in specialization_lines if line)

    bio_lines = [
        professional_bio,
        "\n".join(line for line in qualification_lines if line),
        f"Why join this platform: {platform_statement}" if platform_statement else None,
        f"Athlete support provided: {athlete_support_statement}" if athlete_support_statement else None,
    ]
    combined_bio = "\n\n".join(line for line in bio_lines if line)

    request_data = ProfessionalRoleRequestCreate(
        requested_role=RequestedProfessionalRole.PHYSIOTHERAPIST,
        primary_sport=primary_sport,
        organization=organization,
        specialization=combined_specialization,
        years_of_experience=years_of_experience,
        certifications=certifications,
        professional_bio=combined_bio,
        supporting_document_url=document_reference,
    )

    role_request = _create_request(request_data, current_user, db)
    db.refresh(current_user)

    return role_request


@router.get(
    "/me",
    response_model=list[ProfessionalRoleRequestResponse],
)
def get_my_professional_role_requests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(ProfessionalRoleRequest)
        .filter(ProfessionalRoleRequest.user_id == current_user.user_id)
        .order_by(ProfessionalRoleRequest.submitted_at.desc())
        .all()
    )


@router.get(
    "/me/status",
    response_model=ProfessionalRoleRequestResponse | None,
)
def get_my_latest_professional_role_request_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(ProfessionalRoleRequest)
        .filter(ProfessionalRoleRequest.user_id == current_user.user_id)
        .order_by(ProfessionalRoleRequest.submitted_at.desc())
        .first()
    )
