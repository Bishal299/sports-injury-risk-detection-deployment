import uuid

import pytest
from fastapi import HTTPException

from app.database import SessionLocal
from app.dependencies.professional_access import (
    has_active_professional_relationship,
    require_active_professional_relationship,
)
from app.models.athlete import Athlete
from app.models.professional_athlete_relationship import (
    ProfessionalAthleteRelationshipStatus,
)
from app.models.professional_profile import (
    ProfessionalProfile,
    ProfessionalVerificationStatus,
)
from app.models.user import User, UserRole
from app.routes.athletes import get_athlete_profile
from app.services.professional_athlete_relationships import (
    accept_request,
    check_active_relationship,
    create_request,
    list_athlete_relationships,
    list_professional_relationships,
    reject_request,
    revoke_relationship,
)
from app.utils.security import hash_password


ROLE_TO_USER_ROLE = {
    "COACH": UserRole.COACH,
    "PHYSIOTHERAPIST": UserRole.PHYSIOTHERAPIST,
    "SPORTS_SCIENTIST": UserRole.SPORTS_SCIENTIST,
}


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


def _create_athlete(db, prefix="athlete"):
    user = _create_user(db, role=UserRole.ATHLETE, prefix=prefix)
    athlete = Athlete(
        user_id=user.user_id,
        sport="Football",
        age=22,
        height=181,
        weight=76,
        training_load=60,
    )
    db.add(athlete)
    db.commit()
    db.refresh(athlete)
    return user, athlete


def _create_verified_professional(db, professional_role, prefix):
    user = _create_user(
        db,
        role=ROLE_TO_USER_ROLE[professional_role],
        prefix=prefix,
    )
    profile = ProfessionalProfile(
        user_id=user.user_id,
        professional_role=professional_role,
        verification_status=ProfessionalVerificationStatus.VERIFIED.value,
        primary_sport="Football",
        specialization=f"{professional_role} specialization",
        profile_completion=80,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return user, profile


def _delete_users(db, users):
    db.rollback()
    for user in users:
        if user:
            existing = db.query(User).filter(User.user_id == user.user_id).first()
            if existing:
                db.delete(existing)
    db.commit()


def test_generalized_professional_relationship_supports_all_roles_accept_reject_and_revoke():
    db = SessionLocal()
    users = []

    try:
        athlete_user, athlete = _create_athlete(db, "relationship-athlete")
        users.append(athlete_user)

        coach_user, _ = _create_verified_professional(db, "COACH", "relationship-coach")
        physio_user, _ = _create_verified_professional(db, "PHYSIOTHERAPIST", "relationship-physio")
        scientist_user, _ = _create_verified_professional(db, "SPORTS_SCIENTIST", "relationship-scientist")
        users.extend([coach_user, physio_user, scientist_user])

        coach_relationship = create_request(
            db=db,
            professional_user_id=coach_user.user_id,
            athlete_id=athlete.athlete_id,
            professional_role="COACH",
        )
        physio_relationship = create_request(
            db=db,
            professional_user_id=physio_user.user_id,
            athlete_id=athlete.athlete_id,
            professional_role="PHYSIOTHERAPIST",
        )
        scientist_relationship = create_request(
            db=db,
            professional_user_id=scientist_user.user_id,
            athlete_id=athlete.athlete_id,
            professional_role="SPORTS_SCIENTIST",
        )

        assert coach_relationship.status == "PENDING"
        assert physio_relationship.status == "PENDING"
        assert scientist_relationship.status == "PENDING"

        accepted = accept_request(
            db=db,
            relationship_id=coach_relationship.relationship_id,
            athlete_user_id=athlete_user.user_id,
        )
        assert accepted.status == ProfessionalAthleteRelationshipStatus.ACTIVE.value
        assert accepted.accepted_at is not None
        assert check_active_relationship(
            db=db,
            professional_user_id=coach_user.user_id,
            athlete_id=athlete.athlete_id,
            professional_role="COACH",
        )
        assert has_active_professional_relationship(
            db=db,
            professional_user_id=coach_user.user_id,
            athlete_id=athlete.athlete_id,
            professional_role="COACH",
        )

        rejected = reject_request(
            db=db,
            relationship_id=physio_relationship.relationship_id,
            athlete_user_id=athlete_user.user_id,
        )
        assert rejected.status == ProfessionalAthleteRelationshipStatus.REJECTED.value
        assert not check_active_relationship(
            db=db,
            professional_user_id=physio_user.user_id,
            athlete_id=athlete.athlete_id,
            professional_role="PHYSIOTHERAPIST",
        )

        scientist_active = accept_request(
            db=db,
            relationship_id=scientist_relationship.relationship_id,
            athlete_user_id=athlete_user.user_id,
        )
        revoked = revoke_relationship(
            db=db,
            relationship_id=scientist_active.relationship_id,
            athlete_user_id=athlete_user.user_id,
        )
        assert revoked.status == ProfessionalAthleteRelationshipStatus.REVOKED.value
        assert not check_active_relationship(
            db=db,
            professional_user_id=scientist_user.user_id,
            athlete_id=athlete.athlete_id,
            professional_role="SPORTS_SCIENTIST",
        )

    finally:
        _delete_users(db, users)
        db.close()


def test_one_professional_can_have_many_athletes_and_one_athlete_can_have_many_professionals():
    db = SessionLocal()
    users = []

    try:
        coach_user, _ = _create_verified_professional(db, "COACH", "many-coach")
        physio_user, _ = _create_verified_professional(db, "PHYSIOTHERAPIST", "many-physio")
        athlete_user_a, athlete_a = _create_athlete(db, "many-athlete-a")
        athlete_user_b, athlete_b = _create_athlete(db, "many-athlete-b")
        users.extend([coach_user, physio_user, athlete_user_a, athlete_user_b])

        rel_a = create_request(db, coach_user.user_id, athlete_a.athlete_id, "COACH")
        rel_b = create_request(db, coach_user.user_id, athlete_b.athlete_id, "COACH")
        rel_physio = create_request(db, physio_user.user_id, athlete_a.athlete_id, "PHYSIOTHERAPIST")

        accept_request(db, rel_a.relationship_id, athlete_user_a.user_id)
        accept_request(db, rel_b.relationship_id, athlete_user_b.user_id)
        accept_request(db, rel_physio.relationship_id, athlete_user_a.user_id)

        coach_relationships = list_professional_relationships(
            db=db,
            professional_user_id=coach_user.user_id,
            relationship_status="ACTIVE",
        )
        athlete_relationships = list_athlete_relationships(
            db=db,
            athlete_id=athlete_a.athlete_id,
            relationship_status="ACTIVE",
        )

        assert {rel.athlete_id for rel in coach_relationships} >= {
            athlete_a.athlete_id,
            athlete_b.athlete_id,
        }
        assert {rel.professional_user_id for rel in athlete_relationships} >= {
            coach_user.user_id,
            physio_user.user_id,
        }

    finally:
        _delete_users(db, users)
        db.close()


def test_duplicate_pending_or_active_relationship_for_same_professional_athlete_role_is_prevented():
    db = SessionLocal()
    users = []

    try:
        coach_user, _ = _create_verified_professional(db, "COACH", "duplicate-coach")
        athlete_user, athlete = _create_athlete(db, "duplicate-athlete")
        users.extend([coach_user, athlete_user])

        relationship = create_request(db, coach_user.user_id, athlete.athlete_id, "COACH")

        with pytest.raises(HTTPException) as duplicate_pending:
            create_request(db, coach_user.user_id, athlete.athlete_id, "COACH")
        assert duplicate_pending.value.status_code == 409

        accept_request(db, relationship.relationship_id, athlete_user.user_id)

        with pytest.raises(HTTPException) as duplicate_active:
            create_request(db, coach_user.user_id, athlete.athlete_id, "COACH")
        assert duplicate_active.value.status_code == 409

    finally:
        _delete_users(db, users)
        db.close()


def test_unrelated_professional_cannot_pass_active_relationship_authorization():
    db = SessionLocal()
    users = []

    try:
        coach_user, _ = _create_verified_professional(db, "COACH", "private-coach")
        other_coach_user, _ = _create_verified_professional(db, "COACH", "private-other-coach")
        athlete_user, athlete = _create_athlete(db, "private-athlete")
        users.extend([coach_user, other_coach_user, athlete_user])

        relationship = create_request(db, coach_user.user_id, athlete.athlete_id, "COACH")
        accept_request(db, relationship.relationship_id, athlete_user.user_id)

        require_active_professional_relationship(
            db=db,
            current_user=coach_user,
            athlete_id=athlete.athlete_id,
            professional_role="COACH",
        )

        with pytest.raises(HTTPException) as forbidden:
            require_active_professional_relationship(
                db=db,
                current_user=other_coach_user,
                athlete_id=athlete.athlete_id,
                professional_role="COACH",
            )
        assert forbidden.value.status_code == 403

    finally:
        _delete_users(db, users)
        db.close()


def test_existing_athlete_profile_functionality_still_reads_owned_profile():
    db = SessionLocal()
    athlete_user = None

    try:
        athlete_user, athlete = _create_athlete(db, "existing-athlete")

        profile = get_athlete_profile(
            current_user=athlete_user,
            db=db,
        )

        assert profile.athlete_id == athlete.athlete_id
        assert profile.user_id == athlete_user.user_id
        assert profile.sport == "Football"

    finally:
        _delete_users(db, [athlete_user])
        db.close()
