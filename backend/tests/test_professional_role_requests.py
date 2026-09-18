import asyncio
import json
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from fastapi import HTTPException
from starlette.responses import Response

from app.database import SessionLocal
from app.dependencies.auth import require_roles
from app.models.coach_athlete_relationship import CoachAthleteRelationship
from app.models.coach_profile import CoachProfile
from app.models.athlete import Athlete
from app.models.analysis_result import AnalysisResult
from app.models.professional_athlete_relationship import ProfessionalAthleteRelationship
from app.models.professional_role_request import ProfessionalRoleRequest
from app.models.professional_profile import ProfessionalProfile
from app.models.user import User, UserRole
from app.models.video import Video
from app.routes.physiotherapist import get_verified_physiotherapist_profile
from app.routes.admin_professional_role_requests import (
    approve_professional_role_request,
    get_professional_role_request,
    list_professional_role_requests,
    reject_professional_role_request,
)
from app.routes.auth import login_user, register_user
from app.routes.athletes import (
    accept_coach_request,
    accept_physiotherapist_request,
    get_coach_requests,
    get_connected_coaches,
    get_my_coach_tasks,
    get_my_rehabilitation_plans,
    update_my_coach_task_status,
    update_my_rehabilitation_activity_status,
    reject_coach_request,
    revoke_coach_access,
)
from app.routes.coach import (
    assign_physiotherapist_to_athlete,
    cancel_athlete_task,
    create_athlete_task,
    discover_athletes,
    download_connected_athlete_pdf,
    get_connected_athlete_analysis,
    get_connected_athlete_detail,
    get_athlete_physiotherapist_assignments,
    get_connected_athlete_profile,
    get_connected_athletes,
    get_my_coach_profile,
    get_verified_coach_profile,
    list_assignable_physiotherapists,
    list_athlete_tasks,
    send_connection_request,
    update_athlete_task,
)
from app.routes.professional_role_requests import (
    submit_physiotherapist_application,
    submit_professional_role_request,
)
from app.routes.physiotherapist import (
    create_rehabilitation_activity,
    create_note as create_physiotherapist_note,
    create_rehabilitation_plan,
    delete_rehabilitation_activity,
    download_recovery_report,
    get_connected_athlete_analysis as get_physiotherapist_athlete_analysis,
    get_athlete_detail as get_physiotherapist_athlete_detail,
    get_dashboard as get_physiotherapist_dashboard,
    get_my_requests as get_physiotherapist_requests,
    list_notes as list_physiotherapist_notes,
    get_my_athletes as get_physiotherapist_athletes,
    accept_coach_assignment,
    reject_coach_assignment,
    send_connection_request as send_physiotherapist_connection_request,
    update_rehabilitation_activity,
    update_rehabilitation_plan,
)
from app.dependencies.professional_access import require_role_permission
from app.schemas.athlete import AthleteCoachTaskUpdate, AthleteRehabilitationActivityUpdate
from app.schemas.coach_athlete import CoachTaskCreate, CoachTaskUpdate
from app.schemas.physiotherapist import (
    PhysiotherapistNoteCreate,
    RehabilitationActivityCreate,
    RehabilitationActivityUpdate,
    RehabilitationPlanCreate,
)
from app.schemas.professional_role_request import (
    ProfessionalRoleRequestCreate,
    ProfessionalRoleRequestReject,
    ProfessionalRoleRequestStatus,
    RequestedProfessionalRole,
)
from app.schemas.user import UserCreate, UserLogin
from app.utils.security import hash_password


async def _read_streaming_response(response):
    chunks = []
    async for chunk in response.body_iterator:
        chunks.append(chunk if isinstance(chunk, bytes) else chunk.encode("utf-8"))
    return b"".join(chunks)


def _unique_email(prefix):
    return f"{prefix}-{uuid.uuid4()}@example.com"


def _create_user(db, role=UserRole.ATHLETE, prefix="user"):
    user = User(
        name=f"{prefix.title()} Test",
        email=_unique_email(prefix),
        password=hash_password("Password123!"),
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _create_verified_coach(db, prefix="coach"):
    user = _create_user(db, role=UserRole.COACH, prefix=prefix)
    profile = CoachProfile(
        user_id=user.user_id,
        primary_sport="Football",
        years_of_experience=6,
        coaching_specialization="Movement quality",
        verification_status="VERIFIED",
        profile_completion=80,
    )
    professional_profile = ProfessionalProfile(
        user_id=user.user_id,
        professional_role="COACH",
        verification_status="VERIFIED",
        primary_sport="Football",
        years_of_experience=6,
        specialization="Movement quality",
        profile_completion=80,
    )
    db.add(profile)
    db.add(professional_profile)
    db.commit()
    db.refresh(profile)
    return user, profile


def _create_verified_physiotherapist(db, prefix="physio"):
    user = _create_user(db, role=UserRole.PHYSIOTHERAPIST, prefix=prefix)
    profile = ProfessionalProfile(
        user_id=user.user_id,
        professional_role="PHYSIOTHERAPIST",
        verification_status="VERIFIED",
        primary_sport="Football",
        years_of_experience=5,
        specialization="Return to sport",
        organization="Recovery Clinic",
        profile_completion=90,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return user, profile


def _create_athlete(db, prefix="athlete"):
    user = _create_user(db, role=UserRole.ATHLETE, prefix=prefix)
    athlete = Athlete(
        user_id=user.user_id,
        sport="Football",
        age=21,
        height=180,
        weight=75,
        training_load=65,
    )
    db.add(athlete)
    db.commit()
    db.refresh(athlete)
    return user, athlete


def _delete_users(db, users):
    db.rollback()
    for user in users:
        if user:
            existing = db.query(User).filter(User.user_id == user.user_id).first()
            if existing:
                db.delete(existing)
    db.commit()


def test_register_cannot_self_grant_professional_role():
    db = SessionLocal()

    try:
        with pytest.raises(HTTPException) as exc:
            register_user(
                UserCreate(
                    name="Self Coach",
                    email=_unique_email("self-coach"),
                    password="Password123!",
                    role=UserRole.COACH,
                ),
                db=db,
            )

        assert exc.value.status_code == 400

    finally:
        db.close()


def test_normal_user_submits_coach_request_pending_and_cannot_access_coach_api():
    db = SessionLocal()
    user = None

    try:
        user = _create_user(db, prefix="coach-request")

        role_request = submit_professional_role_request(
            ProfessionalRoleRequestCreate(
                requested_role=RequestedProfessionalRole.COACH,
                primary_sport="Football",
                years_of_experience=4,
                organization="Local Club",
                specialization="Speed and agility",
                professional_bio="Youth performance coach.",
            ),
            current_user=user,
            db=db,
        )

        assert role_request.status == "PENDING"
        assert role_request.requested_role == "COACH"

        professional_profile = (
            db.query(ProfessionalProfile)
            .filter(
                ProfessionalProfile.user_id == user.user_id,
                ProfessionalProfile.professional_role == "COACH",
            )
            .first()
        )
        assert professional_profile is not None
        assert professional_profile.verification_status == "PENDING"
        assert professional_profile.primary_sport == "Football"

        with pytest.raises(HTTPException) as duplicate:
            submit_professional_role_request(
                ProfessionalRoleRequestCreate(
                    requested_role=RequestedProfessionalRole.COACH,
                    primary_sport="Football",
                ),
                current_user=user,
                db=db,
            )
        assert duplicate.value.status_code == 409

        with pytest.raises(HTTPException) as forbidden:
            require_roles(UserRole.COACH)(current_user=user)
        assert forbidden.value.status_code == 403

    finally:
        _delete_users(db, [user])
        db.close()


def test_admin_approves_coach_request_and_same_account_gets_coach_role_after_login():
    db = SessionLocal()
    user = None
    admin = None

    try:
        user = _create_user(db, prefix="coach-approval")
        admin = _create_user(db, role=UserRole.ADMINISTRATOR, prefix="admin")

        role_request = submit_professional_role_request(
            ProfessionalRoleRequestCreate(
                requested_role=RequestedProfessionalRole.COACH,
                primary_sport="Basketball",
                years_of_experience=7,
                organization="Performance Center",
                specialization="Landing mechanics",
                certifications="Strength and conditioning",
                professional_bio="Works with court sport athletes.",
            ),
            current_user=user,
            db=db,
        )

        approved = approve_professional_role_request(
            role_request.request_id,
            admin_user=admin,
            db=db,
        )
        assert approved.status == "APPROVED"

        db.refresh(user)
        assert user.role == UserRole.COACH

        coach_profile = (
            db.query(CoachProfile)
            .filter(CoachProfile.user_id == user.user_id)
            .first()
        )
        assert coach_profile is not None
        assert coach_profile.verification_status == "VERIFIED"
        assert coach_profile.primary_sport == "Basketball"

        professional_profile = (
            db.query(ProfessionalProfile)
            .filter(
                ProfessionalProfile.user_id == user.user_id,
                ProfessionalProfile.professional_role == "COACH",
            )
            .first()
        )
        assert professional_profile is not None
        assert professional_profile.verification_status == "VERIFIED"
        assert professional_profile.primary_sport == "Basketball"
        assert professional_profile.specialization == "Landing mechanics"

        login = login_user(
            UserLogin(email=user.email, password="Password123!"),
            response=Response(),
            db=db,
        )
        assert "access_token" in login

        verified_profile = get_verified_coach_profile(
            current_user=user,
            db=db,
        )
        coach_profile_response = get_my_coach_profile(
            coach_profile=verified_profile,
        )
        assert coach_profile_response.verification_status == "VERIFIED"

    finally:
        _delete_users(db, [user, admin])
        db.close()


def test_admin_can_list_filter_and_inspect_professional_requests():
    db = SessionLocal()
    coach_user = None
    physio_user = None
    admin = None

    try:
        coach_user = _create_user(db, prefix="admin-list-coach")
        physio_user = _create_user(db, prefix="admin-list-physio")
        admin = _create_user(db, role=UserRole.ADMINISTRATOR, prefix="admin")

        coach_request = submit_professional_role_request(
            ProfessionalRoleRequestCreate(
                requested_role=RequestedProfessionalRole.COACH,
                primary_sport="Football",
                years_of_experience=4,
                organization="List Club",
                specialization="Speed",
            ),
            current_user=coach_user,
            db=db,
        )
        physio_request = submit_professional_role_request(
            ProfessionalRoleRequestCreate(
                requested_role=RequestedProfessionalRole.PHYSIOTHERAPIST,
                primary_sport="Basketball",
                years_of_experience=8,
                organization="Recovery Center",
                specialization="Rehabilitation",
            ),
            current_user=physio_user,
            db=db,
        )

        all_pending = list_professional_role_requests(
            request_status=None,
            requested_role=None,
            search=None,
            admin_user=admin,
            db=db,
        )
        assert {item.request_id for item in all_pending} >= {
            coach_request.request_id,
            physio_request.request_id,
        }

        coach_only = list_professional_role_requests(
            request_status=None,
            requested_role=RequestedProfessionalRole.COACH,
            search=None,
            admin_user=admin,
            db=db,
        )
        assert any(item.request_id == coach_request.request_id for item in coach_only)
        assert all(item.requested_role == "COACH" for item in coach_only)

        pending_physio = list_professional_role_requests(
            request_status=ProfessionalRoleRequestStatus.PENDING,
            requested_role=RequestedProfessionalRole.PHYSIOTHERAPIST,
            search="Recovery",
            admin_user=admin,
            db=db,
        )
        assert [item.request_id for item in pending_physio] == [physio_request.request_id]

        inspected = get_professional_role_request(
            coach_request.request_id,
            admin_user=admin,
            db=db,
        )
        assert inspected.request_id == coach_request.request_id
        assert inspected.applicant_email == coach_user.email
        assert inspected.organization == "List Club"

    finally:
        _delete_users(db, [coach_user, physio_user, admin])
        db.close()


def test_admin_rejects_professional_request_and_user_role_does_not_change():
    db = SessionLocal()
    user = None
    admin = None

    try:
        user = _create_user(db, prefix="coach-rejection")
        admin = _create_user(db, role=UserRole.ADMINISTRATOR, prefix="admin")

        role_request = submit_professional_role_request(
            ProfessionalRoleRequestCreate(
                requested_role=RequestedProfessionalRole.COACH,
                primary_sport="Running",
            ),
            current_user=user,
            db=db,
        )

        rejected = reject_professional_role_request(
            role_request.request_id,
            ProfessionalRoleRequestReject(
                rejection_reason="Certification details are incomplete."
            ),
            admin_user=admin,
            db=db,
        )
        assert rejected.status == "REJECTED"
        assert rejected.rejection_reason == "Certification details are incomplete."

        db.refresh(user)
        assert user.role == UserRole.ATHLETE

        stored_request = (
            db.query(ProfessionalRoleRequest)
            .filter(ProfessionalRoleRequest.request_id == role_request.request_id)
            .first()
        )
        assert stored_request.status == "REJECTED"

        professional_profile = (
            db.query(ProfessionalProfile)
            .filter(
                ProfessionalProfile.user_id == user.user_id,
                ProfessionalProfile.professional_role == "COACH",
            )
            .first()
        )
        assert professional_profile is not None
        assert professional_profile.verification_status == "REJECTED"

        with pytest.raises(HTTPException) as forbidden:
            require_roles(UserRole.COACH)(current_user=user)
        assert forbidden.value.status_code == 403

    finally:
        _delete_users(db, [user, admin])
        db.close()


def test_non_admin_cannot_manage_professional_requests():
    db = SessionLocal()
    applicant = None
    non_admin = None

    try:
        applicant = _create_user(db, prefix="admin-deny-applicant")
        non_admin = _create_user(db, prefix="admin-deny-user")

        role_request = submit_professional_role_request(
            ProfessionalRoleRequestCreate(
                requested_role=RequestedProfessionalRole.COACH,
                primary_sport="Football",
            ),
            current_user=applicant,
            db=db,
        )

        with pytest.raises(HTTPException) as list_forbidden:
            list_professional_role_requests(
                request_status=None,
                requested_role=None,
                search=None,
                admin_user=non_admin,
                db=db,
            )
        assert list_forbidden.value.status_code == 403

        with pytest.raises(HTTPException) as inspect_forbidden:
            get_professional_role_request(
                role_request.request_id,
                admin_user=non_admin,
                db=db,
            )
        assert inspect_forbidden.value.status_code == 403

        with pytest.raises(HTTPException) as approve_forbidden:
            approve_professional_role_request(
                role_request.request_id,
                admin_user=non_admin,
                db=db,
            )
        assert approve_forbidden.value.status_code == 403

        with pytest.raises(HTTPException) as reject_forbidden:
            reject_professional_role_request(
                role_request.request_id,
                ProfessionalRoleRequestReject(rejection_reason="No"),
                admin_user=non_admin,
                db=db,
            )
        assert reject_forbidden.value.status_code == 403

        db.refresh(applicant)
        assert applicant.role == UserRole.ATHLETE

    finally:
        _delete_users(db, [applicant, non_admin])
        db.close()


def test_same_user_can_have_pending_requests_for_different_professional_roles_but_not_same_role():
    db = SessionLocal()
    user = None

    try:
        user = _create_user(db, prefix="multi-role-request")

        coach_request = submit_professional_role_request(
            ProfessionalRoleRequestCreate(
                requested_role=RequestedProfessionalRole.COACH,
                primary_sport="Football",
            ),
            current_user=user,
            db=db,
        )
        physio_request = submit_professional_role_request(
            ProfessionalRoleRequestCreate(
                requested_role=RequestedProfessionalRole.PHYSIOTHERAPIST,
                primary_sport="Football",
                specialization="Return to play",
            ),
            current_user=user,
            db=db,
        )

        assert coach_request.status == "PENDING"
        assert physio_request.status == "PENDING"

        profiles = (
            db.query(ProfessionalProfile)
            .filter(ProfessionalProfile.user_id == user.user_id)
            .all()
        )
        assert {profile.professional_role for profile in profiles} >= {
            "COACH",
            "PHYSIOTHERAPIST",
        }

        with pytest.raises(HTTPException) as duplicate:
            submit_professional_role_request(
                ProfessionalRoleRequestCreate(
                    requested_role=RequestedProfessionalRole.PHYSIOTHERAPIST,
                    primary_sport="Football",
                ),
                current_user=user,
                db=db,
            )
        assert duplicate.value.status_code == 409

        db.refresh(user)
        assert user.role == UserRole.ATHLETE

        with pytest.raises(HTTPException) as forbidden:
            require_roles(UserRole.PHYSIOTHERAPIST)(current_user=user)
        assert forbidden.value.status_code == 403

    finally:
        _delete_users(db, [user])
        db.close()


def test_physiotherapist_application_persists_role_specific_fields_and_document_links():
    db = SessionLocal()
    user = None

    try:
        user = _create_user(db, prefix="physio-form")

        role_request = submit_physiotherapist_application(
            requested_role=RequestedProfessionalRole.PHYSIOTHERAPIST,
            full_name="Priya Physio",
            phone="555-0100",
            other_sports=None,
            highest_qualification="MPT",
            qualification_other=None,
            specialization="Sports Physiotherapy",
            specialization_other=None,
            registration_number="PT-12345",
            registration_authority="State Physiotherapy Council",
            license_expiry_date="2030-01-31",
            years_of_experience=8,
            sports_physiotherapy_experience=5,
            organization="Recovery Clinic",
            primary_sport="Football",
            sports_worked_with="Football, Cricket",
            areas_of_expertise="Injury Rehabilitation, Return-to-Sport",
            certifications="1. Sports Rehab Certificate (Issuing Organization: Sports Council, Year Obtained: 2025)",
            professional_bio="Sports physiotherapist focused on return-to-sport.",
            platform_statement="I want to support monitored recovery programs.",
            athlete_support_statement="I can provide rehab progress and movement correction support.",
            supporting_document_url=None,
            license_document_url="https://example.com/license.pdf",
            qualification_document_url="https://example.com/qualification.pdf",
            certification_documents_url="https://example.com/certificates.pdf",
            supporting_document=None,
            license_document=None,
            qualification_document=None,
            certification_documents=None,
            current_user=user,
            db=db,
        )

        assert role_request.status == "PENDING"
        assert role_request.requested_role == "PHYSIOTHERAPIST"
        assert role_request.primary_sport == "Football"
        assert role_request.organization == "Recovery Clinic"
        assert role_request.specialization == "Sports Physiotherapy"
        assert "Highest Qualification: MPT" in role_request.professional_bio
        assert "Professional Registration / License Number: PT-12345" in role_request.professional_bio
        assert "Why join this platform" in role_request.professional_bio
        assert "Sports Rehab Certificate" in role_request.certifications

        documents = json.loads(role_request.supporting_document_url)
        assert {document["label"] for document in documents} == {
            "Professional Registration / License Document",
            "Qualification Certificate",
            "Relevant Certification Documents",
        }

        db.refresh(user)
        assert user.name == "Priya Physio"
        assert user.phone == "555-0100"
        assert user.role == UserRole.ATHLETE

        professional_profile = (
            db.query(ProfessionalProfile)
            .filter(
                ProfessionalProfile.user_id == user.user_id,
                ProfessionalProfile.professional_role == "PHYSIOTHERAPIST",
            )
            .first()
        )
        assert professional_profile is not None
        assert professional_profile.verification_status == "PENDING"
        assert professional_profile.specialization == "Sports Physiotherapy"

    finally:
        _delete_users(db, [user])
        db.close()


def test_admin_approves_physiotherapist_request_without_creating_separate_account():
    db = SessionLocal()
    user = None
    admin = None

    try:
        user = _create_user(db, prefix="physio-approval")
        original_user_id = user.user_id
        original_email = user.email
        original_password = user.password
        admin = _create_user(db, role=UserRole.ADMINISTRATOR, prefix="admin")

        role_request = submit_professional_role_request(
            ProfessionalRoleRequestCreate(
                requested_role=RequestedProfessionalRole.PHYSIOTHERAPIST,
                primary_sport="Football",
                years_of_experience=5,
                organization="Sports Clinic",
                specialization="Rehabilitation",
                professional_bio="Physiotherapist focused on return to sport.",
            ),
            current_user=user,
            db=db,
        )

        approved = approve_professional_role_request(
            role_request.request_id,
            admin_user=admin,
            db=db,
        )
        assert approved.status == "APPROVED"

        db.refresh(user)
        assert user.user_id == original_user_id
        assert user.email == original_email
        assert user.password == original_password
        assert user.role == UserRole.PHYSIOTHERAPIST

        professional_profile = (
            db.query(ProfessionalProfile)
            .filter(
                ProfessionalProfile.user_id == user.user_id,
                ProfessionalProfile.professional_role == "PHYSIOTHERAPIST",
            )
            .first()
        )
        assert professional_profile is not None
        assert professional_profile.verification_status == "VERIFIED"
        assert professional_profile.organization == "Sports Clinic"
        assert professional_profile.specialization == "Rehabilitation"

        assert db.query(User).filter(User.email == original_email).count() == 1

        login = login_user(
            UserLogin(email=original_email, password="Password123!"),
            response=Response(),
            db=db,
        )
        assert "access_token" in login

    finally:
        _delete_users(db, [user, admin])
        db.close()


def test_coach_role_with_pending_profile_is_denied_from_verified_coach_routes():
    db = SessionLocal()
    user = None

    try:
        user = _create_user(db, role=UserRole.COACH, prefix="pending-coach")
        db.add(
            CoachProfile(
                user_id=user.user_id,
                verification_status="PENDING",
                primary_sport="Football",
            )
        )
        db.commit()

        with pytest.raises(HTTPException) as forbidden:
            get_verified_coach_profile(
                current_user=user,
                db=db,
            )

        assert forbidden.value.status_code == 403

    finally:
        _delete_users(db, [user])
        db.close()


def test_connection_workflow_accept_active_private_access_and_revoke_denies():
    db = SessionLocal()
    coach_user = None
    other_coach_user = None
    athlete_user = None
    unrelated_athlete_user = None

    try:
        coach_user, coach_profile = _create_verified_coach(db, "coach-a")
        other_coach_user, other_profile = _create_verified_coach(db, "coach-b")
        athlete_user, athlete = _create_athlete(db, "connection-athlete")
        unrelated_athlete_user, _ = _create_athlete(db, "connection-unrelated-athlete")

        video = Video(
            athlete_id=athlete.athlete_id,
            activity="Landing",
            processing_status="analyzed",
        )
        db.add(video)
        db.commit()
        db.refresh(video)

        analysis = AnalysisResult(
            video_id=video.video_id,
            athlete_id=athlete.athlete_id,
            status="completed",
            progress=100,
            stage="Done",
            composite_risk_score=62,
            risk_category="HIGH",
        )
        db.add(analysis)
        db.commit()

        discovery = discover_athletes(
            search=athlete_user.name,
            sport=None,
            risk_category=None,
            availability=None,
            connection_status=None,
            sort="name",
            limit=25,
            offset=0,
            coach_profile=coach_profile,
            db=db,
        )
        match = next(item for item in discovery if item.athlete_id == athlete.athlete_id)
        assert match.name == athlete_user.name
        assert match.latest_risk_score == 62
        assert match.risk_category == "HIGH"
        assert match.connection_status == "NONE"
        assert not hasattr(match, "training_load")

        relationship = send_connection_request(
            athlete.athlete_id,
            coach_profile=coach_profile,
            current_user=coach_user,
            db=db,
        )
        assert relationship.status == "PENDING"
        assert relationship.professional_role == "COACH"
        assert relationship.professional_user_id == coach_user.user_id
        assert (
            db.query(ProfessionalAthleteRelationship)
            .filter(ProfessionalAthleteRelationship.relationship_id == relationship.relationship_id)
            .count()
            == 1
        )
        assert (
            db.query(CoachAthleteRelationship)
            .filter(CoachAthleteRelationship.relationship_id == relationship.relationship_id)
            .count()
            == 0
        )

        athlete_requests = get_coach_requests(
            current_user=athlete_user,
            db=db,
        )
        assert any(item.relationship_id == relationship.relationship_id for item in athlete_requests)

        with pytest.raises(HTTPException) as forbidden_before_accept:
            get_connected_athlete_profile(
                athlete.athlete_id,
                coach_profile=coach_profile,
                db=db,
            )
        assert forbidden_before_accept.value.status_code == 403

        accepted = accept_coach_request(
            relationship.relationship_id,
            current_user=athlete_user,
            db=db,
        )
        assert accepted.status == "ACTIVE"
        assert accepted.accepted_at is not None

        connected = get_connected_athletes(
            coach_profile=coach_profile,
            db=db,
        )
        assert any(item.relationship_id == relationship.relationship_id for item in connected)

        private_profile = get_connected_athlete_profile(
            athlete.athlete_id,
            coach_profile=coach_profile,
            db=db,
        )
        assert private_profile.email == athlete_user.email
        assert private_profile.training_load == 65

        detail = get_connected_athlete_detail(
            athlete.athlete_id,
            coach_profile=coach_profile,
            db=db,
        )
        assert detail.profile.email == athlete_user.email
        assert detail.profile.latest_risk_score == 62
        assert detail.performance_overview["biomechanical"] is None
        assert len(detail.videos) == 1
        assert detail.videos[0].latest_analysis_id == analysis.analysis_id
        assert len(detail.analyses) == 1
        assert detail.latest_analysis.analysis_id == analysis.analysis_id

        analysis_detail = get_connected_athlete_analysis(
            athlete.athlete_id,
            analysis.analysis_id,
            coach_profile=coach_profile,
            db=db,
        )
        assert analysis_detail.composite_risk_score == 62
        assert analysis_detail.risk_category == "HIGH"

        task = create_athlete_task(
            athlete.athlete_id,
            CoachTaskCreate(
                title="Acceleration mechanics",
                description="Complete sprint mechanics session.",
                priority="HIGH",
                status="ASSIGNED",
            ),
            coach_profile=coach_profile,
            db=db,
        )
        assert task.title == "Acceleration mechanics"
        assert task.status == "ASSIGNED"
        assert task.coach_id == coach_profile.coach_id

        coach_tasks = list_athlete_tasks(
            athlete.athlete_id,
            coach_profile=coach_profile,
            db=db,
        )
        assert [item.task_id for item in coach_tasks] == [task.task_id]

        updated_task = update_athlete_task(
            task.task_id,
            CoachTaskUpdate(priority="MEDIUM", status="IN_PROGRESS"),
            coach_profile=coach_profile,
            db=db,
        )
        assert updated_task.priority == "MEDIUM"
        assert updated_task.status == "IN_PROGRESS"

        athlete_tasks = get_my_coach_tasks(
            current_user=athlete_user,
            db=db,
        )
        assert len(athlete_tasks) == 1
        assert athlete_tasks[0].task_id == task.task_id
        assert athlete_tasks[0].coach_name == coach_user.name

        with pytest.raises(HTTPException) as invalid_athlete_status:
            update_my_coach_task_status(
                task.task_id,
                AthleteCoachTaskUpdate(status="CANCELLED"),
                current_user=athlete_user,
                db=db,
            )
        assert invalid_athlete_status.value.status_code == 400

        started = update_my_coach_task_status(
            task.task_id,
            AthleteCoachTaskUpdate(
                status="IN_PROGRESS",
                athlete_notes="Started warmup.",
            ),
            current_user=athlete_user,
            db=db,
        )
        assert started.status == "IN_PROGRESS"
        assert started.athlete_notes == "Started warmup."

        completed = update_my_coach_task_status(
            task.task_id,
            AthleteCoachTaskUpdate(
                status="COMPLETED",
                athlete_notes="Completed with no issues.",
            ),
            current_user=athlete_user,
            db=db,
        )
        assert completed.status == "COMPLETED"
        assert completed.completed_at is not None

        with pytest.raises(HTTPException) as unrelated_athlete_task_hidden:
            update_my_coach_task_status(
                task.task_id,
                AthleteCoachTaskUpdate(status="COMPLETED"),
                current_user=unrelated_athlete_user,
                db=db,
            )
        assert unrelated_athlete_task_hidden.value.status_code == 404

        with pytest.raises(HTTPException) as unrelated_coach_task_hidden:
            update_athlete_task(
                task.task_id,
                CoachTaskUpdate(status="OVERDUE"),
                coach_profile=other_profile,
                db=db,
            )
        assert unrelated_coach_task_hidden.value.status_code in {403, 404}

        cancelled = cancel_athlete_task(
            task.task_id,
            coach_profile=coach_profile,
            db=db,
        )
        assert cancelled.status == "CANCELLED"

        with pytest.raises(HTTPException) as unrelated_forbidden:
            get_connected_athlete_profile(
                athlete.athlete_id,
                coach_profile=other_profile,
                db=db,
            )
        assert unrelated_forbidden.value.status_code == 403

        with pytest.raises(HTTPException) as unrelated_detail_forbidden:
            get_connected_athlete_detail(
                athlete.athlete_id,
                coach_profile=other_profile,
                db=db,
            )
        assert unrelated_detail_forbidden.value.status_code == 403

        revoked = revoke_coach_access(
            relationship.relationship_id,
            current_user=athlete_user,
            db=db,
        )
        assert revoked.status == "REVOKED"

        with pytest.raises(HTTPException) as revoked_forbidden:
            get_connected_athlete_profile(
                athlete.athlete_id,
                coach_profile=coach_profile,
                db=db,
            )
        assert revoked_forbidden.value.status_code == 403

    finally:
        _delete_users(db, [coach_user, other_coach_user, athlete_user, unrelated_athlete_user])
        db.close()


def test_rejected_connection_does_not_allow_private_access():
    db = SessionLocal()
    coach_user = None
    athlete_user = None

    try:
        coach_user, coach_profile = _create_verified_coach(db, "reject-coach")
        athlete_user, athlete = _create_athlete(db, "reject-athlete")

        relationship = send_connection_request(
            athlete.athlete_id,
            coach_profile=coach_profile,
            current_user=coach_user,
            db=db,
        )

        rejected = reject_coach_request(
            relationship.relationship_id,
            current_user=athlete_user,
            db=db,
        )
        assert rejected.status == "REJECTED"

        connected_coaches = get_connected_coaches(
            current_user=athlete_user,
            db=db,
        )
        assert all(item.relationship_id != relationship.relationship_id for item in connected_coaches)

        with pytest.raises(HTTPException) as forbidden:
            get_connected_athlete_profile(
                athlete.athlete_id,
                coach_profile=coach_profile,
                db=db,
            )
        assert forbidden.value.status_code == 403

    finally:
        _delete_users(db, [coach_user, athlete_user])
        db.close()


def test_physiotherapist_flow_rehabilitation_notes_reports_and_unrelated_access_denied():
    db = SessionLocal()
    physio_user = None
    other_physio_user = None
    coach_user = None
    athlete_user = None
    unrelated_athlete_user = None

    try:
        physio_user, physio_profile = _create_verified_physiotherapist(db, "physio-a")
        other_physio_user, other_profile = _create_verified_physiotherapist(db, "physio-b")
        coach_user, coach_profile = _create_verified_coach(db, "rehab-denied-coach")
        athlete_user, athlete = _create_athlete(db, "physio-athlete")
        unrelated_athlete_user, _ = _create_athlete(db, "physio-unrelated-athlete")

        video = Video(
            athlete_id=athlete.athlete_id,
            activity="Landing",
            processing_status="analyzed",
        )
        db.add(video)
        db.commit()
        db.refresh(video)
        analysis_time = datetime.now(timezone.utc)

        first_analysis = AnalysisResult(
            video_id=video.video_id,
            athlete_id=athlete.athlete_id,
            status="completed",
            progress=100,
            stage="Done",
            completed_at=analysis_time,
            analysis_date=analysis_time,
            composite_risk_score=70,
            risk_category="HIGH",
            knee_valgus=14,
            hip_stability=65,
            trunk_lean=11,
            movement_quality=62,
            symmetry_score=72,
        )
        latest_analysis = AnalysisResult(
            video_id=video.video_id,
            athlete_id=athlete.athlete_id,
            status="completed",
            progress=100,
            stage="Done",
            completed_at=analysis_time + timedelta(minutes=10),
            analysis_date=analysis_time + timedelta(minutes=10),
            composite_risk_score=52,
            risk_category="MODERATE",
            knee_valgus=9,
            hip_stability=74,
            trunk_lean=7,
            movement_quality=75,
            symmetry_score=80,
        )
        db.add(first_analysis)
        db.add(latest_analysis)
        db.commit()

        relationship = send_physiotherapist_connection_request(
            athlete.athlete_id,
            profile=physio_profile,
            db=db,
        )
        assert relationship.professional_role == "PHYSIOTHERAPIST"
        assert relationship.status == "PENDING"

        accepted = accept_physiotherapist_request(
            relationship.relationship_id,
            current_user=athlete_user,
            db=db,
        )
        assert accepted.status == "ACTIVE"

        my_athletes = get_physiotherapist_athletes(
            profile=physio_profile,
            db=db,
        )
        assert any(item.athlete_id == athlete.athlete_id for item in my_athletes)
        my_athlete = next(item for item in my_athletes if item.athlete_id == athlete.athlete_id)
        assert my_athlete.latest_analysis_id == latest_analysis.analysis_id
        assert my_athlete.latest_video_id == video.video_id

        physio_analysis = get_physiotherapist_athlete_analysis(
            athlete.athlete_id,
            latest_analysis.analysis_id,
            profile=physio_profile,
            db=db,
        )
        assert physio_analysis.analysis_id == latest_analysis.analysis_id
        assert physio_analysis.video_id == video.video_id
        assert physio_analysis.time_series_data == latest_analysis.time_series_data
        assert physio_analysis.risk_category == "MODERATE"

        with pytest.raises(HTTPException) as unrelated_analysis_forbidden:
            get_physiotherapist_athlete_analysis(
                athlete.athlete_id,
                latest_analysis.analysis_id,
                profile=other_profile,
                db=db,
            )
        assert unrelated_analysis_forbidden.value.status_code == 403

        plan = create_rehabilitation_plan(
            athlete.athlete_id,
            RehabilitationPlanCreate(
                injury_context="ACL return-to-sport monitoring",
                target_date=datetime.now(timezone.utc).date() - timedelta(days=1),
                current_phase="MOVEMENT_CORRECTION",
                progress=35,
                goals=["Improve landing control"],
                completed_activities=["Initial assessment"],
                pending_activities=["Balance progression"],
                recent_assessment="Movement quality improving.",
                status="ACTIVE",
            ),
            profile=physio_profile,
            db=db,
        )
        assert plan.progress == 35
        assert plan.progress_available is False
        assert plan.calculated_progress is None
        assert plan.current_phase == "MOVEMENT_CORRECTION"

        activity = create_rehabilitation_activity(
            plan.rehabilitation_plan_id,
            RehabilitationActivityCreate(
                title="Landing control drill",
                description="Complete controlled double-leg landing repetitions.",
                phase="MOVEMENT_CORRECTION",
                priority="HIGH",
                status="PENDING",
            ),
            profile=physio_profile,
            db=db,
        )
        assert activity.title == "Landing control drill"
        assert activity.status == "PENDING"

        updated_activity = update_rehabilitation_activity(
            activity.activity_id,
            RehabilitationActivityUpdate(
                title="Landing control drill",
                status="IN_PROGRESS",
            ),
            profile=physio_profile,
            db=db,
        )
        assert updated_activity.status == "IN_PROGRESS"

        with pytest.raises(HTTPException) as unrelated_activity_forbidden:
            create_rehabilitation_activity(
                plan.rehabilitation_plan_id,
                RehabilitationActivityCreate(title="Unauthorized activity"),
                profile=other_profile,
                db=db,
            )
        assert unrelated_activity_forbidden.value.status_code in {403, 404}

        with pytest.raises(HTTPException) as coach_activity_forbidden:
            update_rehabilitation_activity(
                activity.activity_id,
                RehabilitationActivityUpdate(status="COMPLETED"),
                profile=ProfessionalProfile(
                    user_id=coach_user.user_id,
                    professional_role="COACH",
                    verification_status="VERIFIED",
                ),
                db=db,
            )
        assert coach_activity_forbidden.value.status_code in {403, 404}

        athlete_visible_plans = get_my_rehabilitation_plans(
            current_user=athlete_user,
            db=db,
        )
        assert len(athlete_visible_plans) == 1
        assert athlete_visible_plans[0].rehabilitation_plan_id == plan.rehabilitation_plan_id
        assert athlete_visible_plans[0].title == "ACL return-to-sport monitoring"
        assert athlete_visible_plans[0].physiotherapist_name == physio_user.name
        assert athlete_visible_plans[0].progress_available is True
        assert athlete_visible_plans[0].calculated_progress == 0
        assert athlete_visible_plans[0].activities[0].activity_id == activity.activity_id

        with pytest.raises(HTTPException) as athlete_skipped_forbidden:
            update_my_rehabilitation_activity_status(
                activity.activity_id,
                AthleteRehabilitationActivityUpdate(status="SKIPPED"),
                current_user=athlete_user,
                db=db,
            )
        assert athlete_skipped_forbidden.value.status_code == 400

        athlete_started = update_my_rehabilitation_activity_status(
            activity.activity_id,
            AthleteRehabilitationActivityUpdate(
                status="IN_PROGRESS",
                athlete_notes="Started first set.",
            ),
            current_user=athlete_user,
            db=db,
        )
        assert athlete_started.status == "IN_PROGRESS"
        assert athlete_started.athlete_notes == "Started first set."

        athlete_completed = update_my_rehabilitation_activity_status(
            activity.activity_id,
            AthleteRehabilitationActivityUpdate(
                status="COMPLETED",
                athlete_notes="Completed without pain.",
            ),
            current_user=athlete_user,
            db=db,
        )
        assert athlete_completed.status == "COMPLETED"
        assert athlete_completed.completed_at is not None

        overdue_activity = create_rehabilitation_activity(
            plan.rehabilitation_plan_id,
            RehabilitationActivityCreate(
                title="Overdue balance drill",
                phase="BALANCE_STABILITY",
                due_date=datetime.now(timezone.utc).date() - timedelta(days=1),
                priority="HIGH",
                status="PENDING",
            ),
            profile=physio_profile,
            db=db,
        )
        assert overdue_activity.status == "PENDING"

        completed_visible_plans = get_my_rehabilitation_plans(
            current_user=athlete_user,
            db=db,
        )
        assert completed_visible_plans[0].calculated_progress == 50

        with pytest.raises(HTTPException) as unrelated_athlete_hidden:
            update_my_rehabilitation_activity_status(
                activity.activity_id,
                AthleteRehabilitationActivityUpdate(status="COMPLETED"),
                current_user=unrelated_athlete_user,
                db=db,
            )
        assert unrelated_athlete_hidden.value.status_code == 404

        note = create_physiotherapist_note(
            athlete.athlete_id,
            PhysiotherapistNoteCreate(
                title="Session note",
                note="Continue movement correction work.",
            ),
            profile=physio_profile,
            db=db,
        )
        assert note.note == "Continue movement correction work."

        detail = get_physiotherapist_athlete_detail(
            athlete.athlete_id,
            profile=physio_profile,
            db=db,
        )
        assert detail.profile["email"] == athlete_user.email
        assert detail.risk_monitoring["risk_category"] in {"HIGH", "MODERATE"}
        assert detail.rehabilitation_plan.rehabilitation_plan_id == plan.rehabilitation_plan_id
        assert detail.notes[0].note_id == note.note_id
        assert "knee_valgus" in detail.movement_comparison.comparison
        assert detail.movement_comparison.comparison_status == "Compared"
        assert detail.risk_monitoring["previous_risk"] == 70
        assert detail.rehabilitation_monitoring["completed_activity_count"] == 1
        assert detail.rehabilitation_monitoring["pending_activity_count"] == 1
        assert detail.rehabilitation_monitoring["calculated_progress"] == 50
        assert detail.rehabilitation_monitoring["current_phase"] == "MOVEMENT_CORRECTION"
        assert detail.rehabilitation_monitoring["recent_rehabilitation_activity"]["title"] in {
            "Landing control drill",
            "Overdue balance drill",
        }
        assert any(item["type"] == "OVERDUE_ACTIVITIES" for item in detail.needs_attention)
        assert any(item["type"] == "MISSED_REVIEW" for item in detail.needs_attention)
        assert any(event["type"] == "activity_completed" for event in detail.timeline)
        assert any(event["type"] == "movement_analysis" for event in detail.timeline)
        assert any(event["type"] == "next_review" for event in detail.timeline)

        with pytest.raises(HTTPException) as csv_not_supported:
            download_recovery_report(
                athlete.athlete_id,
                "csv",
                profile=physio_profile,
                db=db,
            )
        assert csv_not_supported.value.status_code == 400

        pdf_report = download_recovery_report(
            athlete.athlete_id,
            "pdf",
            profile=physio_profile,
            db=db,
        )
        assert pdf_report.status_code == 200
        pdf_content = asyncio.run(_read_streaming_response(pdf_report))
        assert pdf_content.startswith(b"%PDF")

        with pytest.raises(HTTPException) as unrelated_forbidden:
            get_physiotherapist_athlete_detail(
                athlete.athlete_id,
                profile=other_profile,
                db=db,
        )
        assert unrelated_forbidden.value.status_code == 403

        with pytest.raises(HTTPException) as unrelated_plan_forbidden:
            create_rehabilitation_plan(
                athlete.athlete_id,
                RehabilitationPlanCreate(
                    injury_context="Unauthorized plan",
                    current_phase="ASSESSMENT",
                    status="ACTIVE",
                ),
                profile=other_profile,
                db=db,
            )
        assert unrelated_plan_forbidden.value.status_code == 403

        with pytest.raises(HTTPException) as unrelated_report_forbidden:
            download_recovery_report(
                athlete.athlete_id,
                "pdf",
                profile=other_profile,
                db=db,
            )
        assert unrelated_report_forbidden.value.status_code == 403

        with pytest.raises(HTTPException) as coach_report_forbidden:
            download_recovery_report(
                athlete.athlete_id,
                "pdf",
                profile=ProfessionalProfile(
                    user_id=coach_user.user_id,
                    professional_role="COACH",
                    verification_status="VERIFIED",
                ),
                db=db,
            )
        assert coach_report_forbidden.value.status_code == 403

        with pytest.raises(HTTPException) as coach_plan_forbidden:
            update_rehabilitation_plan(
                plan.rehabilitation_plan_id,
                plan_data=type("Update", (), {
                    "model_dump": lambda self, exclude_unset=True: {"status": "COMPLETED"}
                })(),
                profile=ProfessionalProfile(
                    user_id=coach_user.user_id,
                    professional_role="COACH",
                    verification_status="VERIFIED",
                ),
                db=db,
            )
        assert coach_plan_forbidden.value.status_code in {403, 404}

        deletable_activity = create_rehabilitation_activity(
            plan.rehabilitation_plan_id,
            RehabilitationActivityCreate(title="Temporary activity"),
            profile=physio_profile,
            db=db,
        )
        delete_rehabilitation_activity(
            deletable_activity.activity_id,
            profile=physio_profile,
            db=db,
        )

    finally:
        _delete_users(db, [physio_user, other_physio_user, coach_user, athlete_user, unrelated_athlete_user])
        db.close()


def test_coach_assigns_verified_physiotherapist_and_physio_accepts_or_rejects():
    db = SessionLocal()
    coach_user = None
    other_coach_user = None
    physio_user = None
    rejecting_physio_user = None
    unverified_physio_user = None
    athlete_user = None
    unrelated_athlete_user = None

    try:
        coach_user, coach_profile = _create_verified_coach(db, "assign-coach")
        other_coach_user, other_coach_profile = _create_verified_coach(db, "assign-other-coach")
        physio_user, physio_profile = _create_verified_physiotherapist(db, "assign-physio")
        rejecting_physio_user, rejecting_physio_profile = _create_verified_physiotherapist(db, "rejecting-physio")
        athlete_user, athlete = _create_athlete(db, "assign-athlete")
        unrelated_athlete_user, unrelated_athlete = _create_athlete(db, "assign-unrelated-athlete")

        unverified_physio_user = _create_user(
            db,
            role=UserRole.PHYSIOTHERAPIST,
            prefix="unverified-assign-physio",
        )
        db.add(
            ProfessionalProfile(
                user_id=unverified_physio_user.user_id,
                professional_role="PHYSIOTHERAPIST",
                verification_status="PENDING",
                primary_sport="Football",
            )
        )
        db.commit()

        coach_relationship = send_connection_request(
            athlete.athlete_id,
            coach_profile=coach_profile,
            current_user=coach_user,
            db=db,
        )
        accept_coach_request(
            coach_relationship.relationship_id,
            current_user=athlete_user,
            db=db,
        )

        available = list_assignable_physiotherapists(
            athlete.athlete_id,
            search="Assign",
            coach_profile=coach_profile,
            db=db,
        )
        assert any(item.user_id == physio_user.user_id for item in available)

        with pytest.raises(HTTPException) as unrelated_forbidden:
            assign_physiotherapist_to_athlete(
                unrelated_athlete.athlete_id,
                physio_user.user_id,
                coach_profile=coach_profile,
                db=db,
            )
        assert unrelated_forbidden.value.status_code == 403

        with pytest.raises(HTTPException) as other_coach_forbidden:
            assign_physiotherapist_to_athlete(
                athlete.athlete_id,
                physio_user.user_id,
                coach_profile=other_coach_profile,
                db=db,
            )
        assert other_coach_forbidden.value.status_code == 403

        with pytest.raises(HTTPException) as unverified_forbidden:
            assign_physiotherapist_to_athlete(
                athlete.athlete_id,
                unverified_physio_user.user_id,
                coach_profile=coach_profile,
                db=db,
            )
        assert unverified_forbidden.value.status_code in {403, 404}

        with pytest.raises(HTTPException) as non_physio_forbidden:
            assign_physiotherapist_to_athlete(
                athlete.athlete_id,
                coach_user.user_id,
                coach_profile=coach_profile,
                db=db,
            )
        assert non_physio_forbidden.value.status_code == 404

        assignment = assign_physiotherapist_to_athlete(
            athlete.athlete_id,
            physio_user.user_id,
            coach_profile=coach_profile,
            db=db,
        )
        assert assignment.professional_role == "PHYSIOTHERAPIST"
        assert assignment.status == "PENDING"
        assert assignment.requested_by == coach_user.user_id

        with pytest.raises(HTTPException) as duplicate_pending:
            assign_physiotherapist_to_athlete(
                athlete.athlete_id,
                physio_user.user_id,
                coach_profile=coach_profile,
                db=db,
            )
        assert duplicate_pending.value.status_code == 409

        pending_assignments = get_athlete_physiotherapist_assignments(
            athlete.athlete_id,
            coach_profile=coach_profile,
            db=db,
        )
        assert any(item.relationship_id == assignment.relationship_id for item in pending_assignments)

        physio_requests = get_physiotherapist_requests(
            profile=physio_profile,
            db=db,
        )
        incoming = [item for item in physio_requests if item.relationship_id == assignment.relationship_id]
        assert incoming
        assert incoming[0].requested_by == coach_user.user_id
        assert incoming[0].requested_by_name == coach_user.name
        assert incoming[0].requested_by_role == "Coach"

        with pytest.raises(HTTPException) as access_before_accept:
            get_physiotherapist_athlete_detail(
                athlete.athlete_id,
                profile=physio_profile,
                db=db,
            )
        assert access_before_accept.value.status_code == 403

        accepted = accept_coach_assignment(
            assignment.relationship_id,
            profile=physio_profile,
            db=db,
        )
        assert accepted.status == "ACTIVE"
        assert accepted.accepted_at is not None

        detail = get_physiotherapist_athlete_detail(
            athlete.athlete_id,
            profile=physio_profile,
            db=db,
        )
        assert detail.profile["athlete_id"] == athlete.athlete_id

        with pytest.raises(HTTPException) as duplicate_active:
            assign_physiotherapist_to_athlete(
                athlete.athlete_id,
                physio_user.user_id,
                coach_profile=coach_profile,
                db=db,
            )
        assert duplicate_active.value.status_code == 409

        rejecting_assignment = assign_physiotherapist_to_athlete(
            athlete.athlete_id,
            rejecting_physio_user.user_id,
            coach_profile=coach_profile,
            db=db,
        )
        rejected = reject_coach_assignment(
            rejecting_assignment.relationship_id,
            profile=rejecting_physio_profile,
            db=db,
        )
        assert rejected.status == "REJECTED"
        assert rejected.accepted_at is None

        self_sent = send_physiotherapist_connection_request(
            unrelated_athlete.athlete_id,
            profile=physio_profile,
            db=db,
        )
        with pytest.raises(HTTPException) as self_accept_forbidden:
            accept_coach_assignment(
                self_sent.relationship_id,
                profile=physio_profile,
                db=db,
            )
        assert self_accept_forbidden.value.status_code == 403
        db.refresh(self_sent)
        assert self_sent.status == "PENDING"

    finally:
        _delete_users(
            db,
            [
                coach_user,
                other_coach_user,
                physio_user,
                rejecting_physio_user,
                unverified_physio_user,
                athlete_user,
                unrelated_athlete_user,
            ],
        )
        db.close()


def test_professional_security_denies_unverified_and_wrong_role_access():
    db = SessionLocal()
    users = []

    try:
        athlete_user, _ = _create_athlete(db, "security-athlete-user")
        users.append(athlete_user)

        with pytest.raises(HTTPException) as athlete_coach_forbidden:
            get_verified_coach_profile(current_user=athlete_user, db=db)
        assert athlete_coach_forbidden.value.status_code == 403

        with pytest.raises(HTTPException) as athlete_physio_forbidden:
            get_verified_physiotherapist_profile(current_user=athlete_user, db=db)
        assert athlete_physio_forbidden.value.status_code == 403

        pending_physio = _create_user(
            db,
            role=UserRole.PHYSIOTHERAPIST,
            prefix="pending-physio-security",
        )
        users.append(pending_physio)
        db.add(
            ProfessionalProfile(
                user_id=pending_physio.user_id,
                professional_role="PHYSIOTHERAPIST",
                verification_status="PENDING",
            )
        )
        db.commit()
        with pytest.raises(HTTPException) as pending_forbidden:
            get_verified_physiotherapist_profile(current_user=pending_physio, db=db)
        assert pending_forbidden.value.status_code == 403

        rejected_physio = _create_user(
            db,
            role=UserRole.PHYSIOTHERAPIST,
            prefix="rejected-physio-security",
        )
        users.append(rejected_physio)
        db.add(
            ProfessionalProfile(
                user_id=rejected_physio.user_id,
                professional_role="PHYSIOTHERAPIST",
                verification_status="REJECTED",
            )
        )
        db.commit()
        with pytest.raises(HTTPException) as rejected_forbidden:
            get_verified_physiotherapist_profile(current_user=rejected_physio, db=db)
        assert rejected_forbidden.value.status_code == 403

        with pytest.raises(HTTPException) as coach_no_physio_permission:
            require_role_permission("COACH", "rehabilitation")
        assert coach_no_physio_permission.value.status_code == 403

        with pytest.raises(HTTPException) as physio_no_coach_permission:
            require_role_permission("PHYSIOTHERAPIST", "performance_information")
        assert physio_no_coach_permission.value.status_code == 403

    finally:
        _delete_users(db, users)
        db.close()


def test_professional_private_endpoints_block_direct_id_and_cross_role_access():
    db = SessionLocal()
    coach_user = None
    physio_user = None
    athlete_user_a = None
    athlete_user_b = None

    try:
        coach_user, coach_profile = _create_verified_coach(db, "security-coach")
        physio_user, physio_profile = _create_verified_physiotherapist(db, "security-physio")
        athlete_user_a, athlete_a = _create_athlete(db, "security-athlete-a")
        athlete_user_b, athlete_b = _create_athlete(db, "security-athlete-b")

        video_a = Video(
            athlete_id=athlete_a.athlete_id,
            activity="Landing",
            processing_status="analyzed",
        )
        video_b = Video(
            athlete_id=athlete_b.athlete_id,
            activity="Cutting",
            processing_status="analyzed",
        )
        db.add(video_a)
        db.add(video_b)
        db.commit()
        db.refresh(video_a)
        db.refresh(video_b)

        analysis_a = AnalysisResult(
            video_id=video_a.video_id,
            athlete_id=athlete_a.athlete_id,
            status="completed",
            progress=100,
            stage="Done",
            composite_risk_score=42,
            risk_category="MODERATE",
        )
        analysis_b = AnalysisResult(
            video_id=video_b.video_id,
            athlete_id=athlete_b.athlete_id,
            status="completed",
            progress=100,
            stage="Done",
            composite_risk_score=82,
            risk_category="CRITICAL",
        )
        db.add(analysis_a)
        db.add(analysis_b)
        db.commit()

        coach_relationship = send_connection_request(
            athlete_a.athlete_id,
            coach_profile=coach_profile,
            current_user=coach_user,
            db=db,
        )
        accept_coach_request(
            coach_relationship.relationship_id,
            current_user=athlete_user_a,
            db=db,
        )

        physio_relationship = send_physiotherapist_connection_request(
            athlete_a.athlete_id,
            profile=physio_profile,
            db=db,
        )
        accept_physiotherapist_request(
            physio_relationship.relationship_id,
            current_user=athlete_user_a,
            db=db,
        )

        plan = create_rehabilitation_plan(
            athlete_a.athlete_id,
            RehabilitationPlanCreate(
                injury_context="Return-to-play tracking",
                current_phase="ASSESSMENT",
                progress=10,
                status="ACTIVE",
            ),
            profile=physio_profile,
            db=db,
        )
        create_physiotherapist_note(
            athlete_a.athlete_id,
            PhysiotherapistNoteCreate(title="Private", note="Physio-only note."),
            profile=physio_profile,
            db=db,
        )

        private_profile = get_connected_athlete_profile(
            athlete_a.athlete_id,
            coach_profile=coach_profile,
            db=db,
        )
        assert private_profile.email == athlete_user_a.email

        with pytest.raises(HTTPException) as coach_unrelated_profile_forbidden:
            get_connected_athlete_profile(
                athlete_b.athlete_id,
                coach_profile=coach_profile,
                db=db,
            )
        assert coach_unrelated_profile_forbidden.value.status_code == 403

        with pytest.raises(HTTPException) as coach_unrelated_analysis_forbidden:
            get_connected_athlete_analysis(
                athlete_b.athlete_id,
                analysis_b.analysis_id,
                coach_profile=coach_profile,
                db=db,
            )
        assert coach_unrelated_analysis_forbidden.value.status_code == 403

        with pytest.raises(HTTPException) as coach_unrelated_report_forbidden:
            download_recovery_report(
                athlete_b.athlete_id,
                "pdf",
                profile=physio_profile,
                db=db,
            )
        assert coach_unrelated_report_forbidden.value.status_code == 403

        with pytest.raises(HTTPException) as coach_physio_note_forbidden:
            list_physiotherapist_notes(
                athlete_a.athlete_id,
                profile=coach_profile,
                db=db,
            )
        assert coach_physio_note_forbidden.value.status_code == 403

        physio_as_coach_profile = CoachProfile(
            user_id=physio_user.user_id,
            verification_status="VERIFIED",
            primary_sport="Football",
        )
        with pytest.raises(HTTPException) as physio_coach_profile_forbidden:
            get_connected_athlete_profile(
                athlete_a.athlete_id,
                coach_profile=physio_as_coach_profile,
                db=db,
            )
        assert physio_coach_profile_forbidden.value.status_code == 403

        dashboard = get_physiotherapist_dashboard(profile=physio_profile, db=db)
        assert dashboard.stats["total_athletes"] == 1

        with pytest.raises(HTTPException) as unrelated_rehab_update_hidden:
            update_rehabilitation_plan(
                plan.rehabilitation_plan_id,
                plan_data=type("Update", (), {"model_dump": lambda self, exclude_unset=True: {"progress": 20}})(),
                profile=ProfessionalProfile(
                    user_id=coach_user.user_id,
                    professional_role="COACH",
                    verification_status="VERIFIED",
                ),
                db=db,
            )
        assert unrelated_rehab_update_hidden.value.status_code in {403, 404}

    finally:
        _delete_users(db, [coach_user, physio_user, athlete_user_a, athlete_user_b])
        db.close()


def test_professional_views_reuse_existing_analysis_reports_and_compatible_comparisons():
    from app.services.professional_analysis import normalize_risk_category

    db = SessionLocal()
    coach_user = None
    physio_user = None
    athlete_user = None
    other_athlete_user = None
    created_files = []

    try:
        assert normalize_risk_category(24.9) == "LOW"
        assert normalize_risk_category(25) == "MODERATE"
        assert normalize_risk_category(50) == "HIGH"
        assert normalize_risk_category(75) == "CRITICAL"

        coach_user, coach_profile = _create_verified_coach(db, "integration-coach")
        physio_user, physio_profile = _create_verified_physiotherapist(db, "integration-physio")
        athlete_user, athlete = _create_athlete(db, "integration-athlete")
        other_athlete_user, other_athlete = _create_athlete(db, "integration-other-athlete")

        video = Video(
            athlete_id=athlete.athlete_id,
            activity="Jump Landing",
            processing_status="analyzed",
        )
        other_video = Video(
            athlete_id=other_athlete.athlete_id,
            activity="Sprint",
            processing_status="analyzed",
        )
        db.add(video)
        db.add(other_video)
        db.commit()
        db.refresh(video)
        db.refresh(other_video)
        base_time = datetime.now(timezone.utc)

        initial = AnalysisResult(
            video_id=video.video_id,
            athlete_id=athlete.athlete_id,
            status="completed",
            progress=100,
            stage="Done",
            completed_at=base_time,
            analysis_date=base_time,
            algorithm_version="1.0-phase1-filtered",
            composite_risk_score=74,
            risk_category="HIGH",
            knee_valgus=12,
            hip_stability=60,
            trunk_lean=10,
            movement_quality=58,
            symmetry_score=70,
        )
        latest = AnalysisResult(
            video_id=video.video_id,
            athlete_id=athlete.athlete_id,
            status="completed",
            progress=100,
            stage="Done",
            completed_at=base_time + timedelta(minutes=10),
            analysis_date=base_time + timedelta(minutes=10),
            algorithm_version="1.0-phase1-filtered",
            composite_risk_score=49,
            risk_category="MODERATE",
            knee_valgus=8,
            hip_stability=72,
            trunk_lean=7,
            movement_quality=73,
            symmetry_score=82,
        )
        incompatible = AnalysisResult(
            video_id=other_video.video_id,
            athlete_id=other_athlete.athlete_id,
            status="completed",
            progress=100,
            stage="Done",
            completed_at=base_time,
            analysis_date=base_time,
            algorithm_version="legacy",
            composite_risk_score=80,
            risk_category="CRITICAL",
            knee_valgus=20,
        )
        incompatible_latest = AnalysisResult(
            video_id=other_video.video_id,
            athlete_id=other_athlete.athlete_id,
            status="completed",
            progress=100,
            stage="Done",
            completed_at=base_time + timedelta(minutes=10),
            analysis_date=base_time + timedelta(minutes=10),
            algorithm_version="2.0-next",
            composite_risk_score=70,
            risk_category="HIGH",
            knee_valgus=16,
        )
        db.add(initial)
        db.add(latest)
        db.add(incompatible)
        db.add(incompatible_latest)
        db.commit()

        report_dir = os.path.join("uploads", "analysis", "reports")
        os.makedirs(report_dir, exist_ok=True)
        pdf_path = os.path.join(report_dir, f"{video.video_id}_report.pdf")
        with open(pdf_path, "wb") as report_file:
            report_file.write(b"%PDF-1.4\n% existing generated analysis report\n")
        created_files.append(pdf_path)

        coach_relationship = send_connection_request(
            athlete.athlete_id,
            coach_profile=coach_profile,
            current_user=coach_user,
            db=db,
        )
        accept_coach_request(
            coach_relationship.relationship_id,
            current_user=athlete_user,
            db=db,
        )
        physio_relationship = send_physiotherapist_connection_request(
            athlete.athlete_id,
            profile=physio_profile,
            db=db,
        )
        accept_physiotherapist_request(
            physio_relationship.relationship_id,
            current_user=athlete_user,
            db=db,
        )
        other_physio_relationship = send_physiotherapist_connection_request(
            other_athlete.athlete_id,
            profile=physio_profile,
            db=db,
        )
        accept_physiotherapist_request(
            other_physio_relationship.relationship_id,
            current_user=other_athlete_user,
            db=db,
        )

        coach_detail = get_connected_athlete_detail(
            athlete.athlete_id,
            coach_profile=coach_profile,
            db=db,
        )
        assert coach_detail.risk_overview["current_risk"] == 49
        assert coach_detail.risk_overview["risk_category"] == "MODERATE"
        assert coach_detail.risk_overview["risk_trend"] == "Decreasing"
        assert coach_detail.movement_comparison["comparison_status"] == "Compared"
        assert coach_detail.movement_comparison["comparison"]["knee_valgus"]["initial"] == 12
        assert coach_detail.movement_comparison["comparison"]["knee_valgus"]["latest"] == 8

        coach_pdf = download_connected_athlete_pdf(
            athlete.athlete_id,
            video.video_id,
            coach_profile=coach_profile,
            db=db,
        )
        assert os.path.normpath(coach_pdf.path) == os.path.normpath(pdf_path)

        with pytest.raises(HTTPException) as wrong_athlete_report:
            download_connected_athlete_pdf(
                other_athlete.athlete_id,
                video.video_id,
                coach_profile=coach_profile,
                db=db,
            )
        assert wrong_athlete_report.value.status_code == 403

        physio_detail = get_physiotherapist_athlete_detail(
            athlete.athlete_id,
            profile=physio_profile,
            db=db,
        )
        assert physio_detail.risk_monitoring["current_risk"] == 49
        assert physio_detail.risk_monitoring["risk_trend"] == "Decreasing"
        assert physio_detail.movement_comparison.comparison_status == "Compared"

        incompatible_version_detail = get_physiotherapist_athlete_detail(
            other_athlete.athlete_id,
            profile=physio_profile,
            db=db,
        )
        assert incompatible_version_detail.movement_comparison.comparison_status == "Incompatible Analysis Versions"
        assert incompatible_version_detail.movement_comparison.comparison == {}

    finally:
        for path in created_files:
            if os.path.exists(path):
                os.remove(path)
        _delete_users(db, [coach_user, physio_user, athlete_user, other_athlete_user])
        db.close()
