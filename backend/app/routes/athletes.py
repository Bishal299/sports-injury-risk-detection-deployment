from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from uuid import UUID

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.notification import NotificationType
from app.models.athlete import Athlete
from app.models.coach_profile import CoachProfile
from app.models.professional_athlete_relationship import (
    ProfessionalAthleteRelationship,
    ProfessionalAthleteRelationshipRole,
    ProfessionalAthleteRelationshipStatus,
)
from app.models.coach_task import CoachTask, CoachTaskStatus
from app.models.rehabilitation_plan import RehabilitationPlan
from app.models.rehabilitation_activity import (
    RehabilitationActivity,
    RehabilitationActivityStatus,
)
from app.schemas.athlete import (
    AthleteCreate,
    AthleteCoachTaskRead,
    AthleteCoachTaskUpdate,
    AthleteRead,
    AthleteRehabilitationActivityRead,
    AthleteRehabilitationActivityUpdate,
    AthleteRehabilitationPlanRead,
    AthleteUpdate,
)
from app.schemas.coach_athlete import CoachRelationshipResponse
from app.schemas.physiotherapist import PhysiotherapistRelationshipResponse
from app.schemas.sports_scientist import SportsScientistRelationshipResponse
from app.services.notifications import create_notification


router = APIRouter(
    prefix="/athletes",
    tags=["Athletes"]
)

COACH_RELATIONSHIP_ROLE = ProfessionalAthleteRelationshipRole.COACH.value
PHYSIO_RELATIONSHIP_ROLE = ProfessionalAthleteRelationshipRole.PHYSIOTHERAPIST.value
SPORTS_SCIENTIST_RELATIONSHIP_ROLE = ProfessionalAthleteRelationshipRole.SPORTS_SCIENTIST.value
ATHLETE_ACTIVITY_STATUSES = {
    RehabilitationActivityStatus.IN_PROGRESS.value,
    RehabilitationActivityStatus.COMPLETED.value,
}
ATHLETE_COACH_TASK_STATUSES = {
    CoachTaskStatus.IN_PROGRESS.value,
    CoachTaskStatus.COMPLETED.value,
}


def _calculate_activity_progress(activities: list[RehabilitationActivity]):
    total = len(activities)
    if total == 0:
        return False, None
    completed = sum(
        1
        for activity in activities
        if activity.status == RehabilitationActivityStatus.COMPLETED.value
    )
    return True, round((completed / total) * 100, 2)


def _build_athlete_coach_task(task: CoachTask) -> AthleteCoachTaskRead:
    return AthleteCoachTaskRead(
        task_id=task.task_id,
        coach_id=task.coach_id,
        athlete_id=task.athlete_id,
        analysis_id=task.analysis_id,
        video_id=task.video_id,
        title=task.title,
        description=task.description,
        due_date=task.due_date,
        priority=task.priority,
        status=task.status,
        completed_at=task.completed_at,
        athlete_notes=task.athlete_notes,
        coach_name=task.coach.user.name if task.coach and task.coach.user else None,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


@router.post(
    "/profile",
    response_model=AthleteRead,
    status_code=status.HTTP_201_CREATED
)
def create_athlete_profile(
    athlete_data: AthleteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check whether this user already has an athlete profile
    existing_profile = (
        db.query(Athlete)
        .filter(Athlete.user_id == current_user.user_id)
        .first()
    )

    if existing_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Athlete profile already exists"
        )

    # Create athlete profile
    athlete = Athlete(
        user_id=current_user.user_id,
        sport=athlete_data.sport,
        position=athlete_data.position,
        age=athlete_data.age,
        height=athlete_data.height,
        weight=athlete_data.weight,
        training_load=athlete_data.training_load,
        flexibility=athlete_data.flexibility,
        strength=athlete_data.strength,
        balance=athlete_data.balance,
        endurance=athlete_data.endurance,
        coach_notes=athlete_data.coach_notes
    )

    db.add(athlete)
    db.commit()
    db.refresh(athlete)

    return athlete


@router.get(
    "/profile",
    response_model=AthleteRead
)
def get_athlete_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    athlete = (
        db.query(Athlete)
        .filter(Athlete.user_id == current_user.user_id)
        .first()
    )

    if not athlete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Athlete profile not found"
        )

    return athlete

@router.put(
    "/profile",
    response_model=AthleteRead
)
def update_athlete_profile(
    athlete_data: AthleteUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    athlete = (
        db.query(Athlete)
        .filter(Athlete.user_id == current_user.user_id)
        .first()
    )

    if not athlete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Athlete profile not found"
        )

    if athlete_data.sport is not None:
        athlete.sport = athlete_data.sport

    if athlete_data.position is not None:
        athlete.position = athlete_data.position

    if athlete_data.age is not None:
        athlete.age = athlete_data.age

    if athlete_data.height is not None:
        athlete.height = athlete_data.height

    if athlete_data.weight is not None:
        athlete.weight = athlete_data.weight

    if athlete_data.training_load is not None:
        athlete.training_load = athlete_data.training_load

    if athlete_data.flexibility is not None:
        athlete.flexibility = athlete_data.flexibility

    if athlete_data.strength is not None:
        athlete.strength = athlete_data.strength

    if athlete_data.balance is not None:
        athlete.balance = athlete_data.balance

    if athlete_data.endurance is not None:
        athlete.endurance = athlete_data.endurance

    if athlete_data.coach_notes is not None:
        athlete.coach_notes = athlete_data.coach_notes

    db.commit()
    db.refresh(athlete)

    return athlete


def _get_current_athlete(current_user: User, db: Session) -> Athlete:
    athlete = (
        db.query(Athlete)
        .filter(Athlete.user_id == current_user.user_id)
        .first()
    )

    if not athlete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Athlete profile not found"
        )

    return athlete


def _get_athlete_relationship(
    relationship_id: UUID,
    athlete: Athlete,
    db: Session,
    professional_role: str = COACH_RELATIONSHIP_ROLE,
) -> ProfessionalAthleteRelationship:
    relationship = (
        db.query(ProfessionalAthleteRelationship)
        .filter(
            ProfessionalAthleteRelationship.relationship_id == relationship_id,
            ProfessionalAthleteRelationship.athlete_id == athlete.athlete_id,
            ProfessionalAthleteRelationship.professional_role == professional_role,
        )
        .first()
    )

    if not relationship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coach relationship not found"
        )

    return relationship


def _list_professional_relationships(
    athlete: Athlete,
    db: Session,
    professional_role: str,
    relationship_status: str,
):
    return (
        db.query(ProfessionalAthleteRelationship)
        .options(
            joinedload(ProfessionalAthleteRelationship.professional_user).joinedload(
                User.professional_profiles
            ),
            joinedload(ProfessionalAthleteRelationship.athlete).joinedload(Athlete.user),
        )
        .filter(
            ProfessionalAthleteRelationship.athlete_id == athlete.athlete_id,
            ProfessionalAthleteRelationship.professional_role == professional_role,
            ProfessionalAthleteRelationship.status == relationship_status,
        )
        .order_by(ProfessionalAthleteRelationship.requested_at.desc())
        .all()
    )


@router.get(
    "/coach-requests",
    response_model=list[CoachRelationshipResponse],
)
def get_coach_requests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    athlete = _get_current_athlete(current_user, db)

    return _list_professional_relationships(
        athlete,
        db,
        COACH_RELATIONSHIP_ROLE,
        ProfessionalAthleteRelationshipStatus.PENDING.value,
    )


@router.get(
    "/connected-coaches",
    response_model=list[CoachRelationshipResponse],
)
def get_connected_coaches(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    athlete = _get_current_athlete(current_user, db)

    return _list_professional_relationships(
        athlete,
        db,
        COACH_RELATIONSHIP_ROLE,
        ProfessionalAthleteRelationshipStatus.ACTIVE.value,
    )


@router.get(
    "/coach-tasks",
    response_model=list[AthleteCoachTaskRead],
)
def get_my_coach_tasks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    athlete = _get_current_athlete(current_user, db)

    active_coach_user_ids = [
        relationship.professional_user_id
        for relationship in (
            db.query(ProfessionalAthleteRelationship)
            .filter(
                ProfessionalAthleteRelationship.athlete_id == athlete.athlete_id,
                ProfessionalAthleteRelationship.professional_role == COACH_RELATIONSHIP_ROLE,
                ProfessionalAthleteRelationship.status == ProfessionalAthleteRelationshipStatus.ACTIVE.value,
            )
            .all()
        )
    ]

    if not active_coach_user_ids:
        return []

    tasks = (
        db.query(CoachTask)
        .options(
            joinedload(CoachTask.coach).joinedload(CoachProfile.user),
            joinedload(CoachTask.athlete),
        )
        .join(CoachProfile, CoachProfile.coach_id == CoachTask.coach_id)
        .filter(
            CoachTask.athlete_id == athlete.athlete_id,
            CoachProfile.user_id.in_(active_coach_user_ids),
        )
        .order_by(CoachTask.created_at.desc())
        .all()
    )
    return [_build_athlete_coach_task(task) for task in tasks]


@router.patch(
    "/coach-tasks/{task_id}",
    response_model=AthleteCoachTaskRead,
)
def update_my_coach_task_status(
    task_id: UUID,
    task_data: AthleteCoachTaskUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    athlete = _get_current_athlete(current_user, db)

    if task_data.status not in ATHLETE_COACH_TASK_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Athlete can only mark Coach tasks in progress or completed",
        )

    active_coach_user_ids = [
        relationship.professional_user_id
        for relationship in (
            db.query(ProfessionalAthleteRelationship)
            .filter(
                ProfessionalAthleteRelationship.athlete_id == athlete.athlete_id,
                ProfessionalAthleteRelationship.professional_role == COACH_RELATIONSHIP_ROLE,
                ProfessionalAthleteRelationship.status == ProfessionalAthleteRelationshipStatus.ACTIVE.value,
            )
            .all()
        )
    ]

    task = (
        db.query(CoachTask)
        .options(
            joinedload(CoachTask.coach).joinedload(CoachProfile.user),
            joinedload(CoachTask.athlete),
        )
        .join(CoachProfile, CoachProfile.coach_id == CoachTask.coach_id)
        .filter(
            CoachTask.task_id == task_id,
            CoachTask.athlete_id == athlete.athlete_id,
            CoachProfile.user_id.in_(active_coach_user_ids or []),
        )
        .first()
    )
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coach task not found",
        )

    if task.status == CoachTaskStatus.CANCELLED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cancelled Coach tasks cannot be updated by the athlete",
        )

    task.status = task_data.status
    task.athlete_notes = task_data.athlete_notes
    task.completed_at = (
        datetime.now(timezone.utc)
        if task_data.status == CoachTaskStatus.COMPLETED.value
        else None
    )

    db.commit()
    db.refresh(task)
    return _build_athlete_coach_task(task)


@router.post(
    "/coach-requests/{relationship_id}/accept",
    response_model=CoachRelationshipResponse,
)
def accept_coach_request(
    relationship_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    athlete = _get_current_athlete(current_user, db)
    relationship = _get_athlete_relationship(relationship_id, athlete, db)

    if relationship.status != ProfessionalAthleteRelationshipStatus.PENDING.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending coach requests can be accepted"
        )

    now = datetime.now(timezone.utc)
    relationship.status = ProfessionalAthleteRelationshipStatus.ACTIVE.value
    relationship.responded_at = now
    relationship.accepted_at = now
    create_notification(
        db,
        recipient_user_id=relationship.professional_user_id,
        notification_type=NotificationType.CONNECTION_ACCEPTED,
        title="Connection request accepted",
        message=f"{current_user.name} accepted your Coach connection request.",
        actor_user_id=current_user.user_id,
        entity_type="professional_athlete_relationship",
        entity_id=relationship.relationship_id,
        action_url="/coach/athletes",
    )

    db.commit()
    db.refresh(relationship)

    return relationship


@router.get(
    "/physiotherapist-requests",
    response_model=list[PhysiotherapistRelationshipResponse],
)
def get_physiotherapist_requests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    athlete = _get_current_athlete(current_user, db)
    return _list_professional_relationships(
        athlete,
        db,
        PHYSIO_RELATIONSHIP_ROLE,
        ProfessionalAthleteRelationshipStatus.PENDING.value,
    )


@router.get(
    "/connected-physiotherapists",
    response_model=list[PhysiotherapistRelationshipResponse],
)
def get_connected_physiotherapists(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    athlete = _get_current_athlete(current_user, db)
    return _list_professional_relationships(
        athlete,
        db,
        PHYSIO_RELATIONSHIP_ROLE,
        ProfessionalAthleteRelationshipStatus.ACTIVE.value,
    )


@router.get(
    "/sports-scientist-requests",
    response_model=list[SportsScientistRelationshipResponse],
)
def get_sports_scientist_requests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    athlete = _get_current_athlete(current_user, db)
    return _list_professional_relationships(
        athlete,
        db,
        SPORTS_SCIENTIST_RELATIONSHIP_ROLE,
        ProfessionalAthleteRelationshipStatus.PENDING.value,
    )


@router.get(
    "/connected-sports-scientists",
    response_model=list[SportsScientistRelationshipResponse],
)
def get_connected_sports_scientists(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    athlete = _get_current_athlete(current_user, db)
    return _list_professional_relationships(
        athlete,
        db,
        SPORTS_SCIENTIST_RELATIONSHIP_ROLE,
        ProfessionalAthleteRelationshipStatus.ACTIVE.value,
    )


@router.get(
    "/rehabilitation-plans",
    response_model=list[AthleteRehabilitationPlanRead],
)
def get_my_rehabilitation_plans(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    athlete = _get_current_athlete(current_user, db)

    active_physio_relationships = (
        db.query(ProfessionalAthleteRelationship)
        .options(joinedload(ProfessionalAthleteRelationship.professional_user))
        .filter(
            ProfessionalAthleteRelationship.athlete_id == athlete.athlete_id,
            ProfessionalAthleteRelationship.professional_role == PHYSIO_RELATIONSHIP_ROLE,
            ProfessionalAthleteRelationship.status == ProfessionalAthleteRelationshipStatus.ACTIVE.value,
        )
        .all()
    )
    active_physio_user_ids = [
        relationship.professional_user_id
        for relationship in active_physio_relationships
    ]
    physio_name_by_user_id = {
        relationship.professional_user_id: relationship.professional_user.name
        for relationship in active_physio_relationships
        if relationship.professional_user
    }

    if not active_physio_user_ids:
        return []

    plans = (
        db.query(RehabilitationPlan)
        .filter(
            RehabilitationPlan.athlete_id == athlete.athlete_id,
            RehabilitationPlan.physiotherapist_user_id.in_(active_physio_user_ids),
        )
        .order_by(RehabilitationPlan.updated_at.desc())
        .all()
    )

    return [
        (
            lambda available, progress: AthleteRehabilitationPlanRead(
                rehabilitation_plan_id=plan.rehabilitation_plan_id,
                athlete_id=plan.athlete_id,
                physiotherapist_user_id=plan.physiotherapist_user_id,
                physiotherapist_name=physio_name_by_user_id.get(plan.physiotherapist_user_id),
                title=plan.injury_context,
                description=plan.recent_assessment,
                current_phase=plan.current_phase,
                start_date=plan.start_date,
                target_date=plan.target_date,
                goals=plan.goals,
                status=plan.status,
                notes=plan.notes,
                progress_available=available,
                calculated_progress=progress,
                activities=list(plan.activities or []),
                created_at=plan.created_at,
                updated_at=plan.updated_at,
            )
        )(*_calculate_activity_progress(list(plan.activities or [])))
        for plan in plans
    ]


@router.patch(
    "/rehabilitation-activities/{activity_id}",
    response_model=AthleteRehabilitationActivityRead,
)
def update_my_rehabilitation_activity_status(
    activity_id: UUID,
    activity_data: AthleteRehabilitationActivityUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    athlete = _get_current_athlete(current_user, db)

    if activity_data.status not in ATHLETE_ACTIVITY_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Athlete can only mark activities in progress or completed",
        )

    active_physio_user_ids = [
        relationship.professional_user_id
        for relationship in (
            db.query(ProfessionalAthleteRelationship)
            .filter(
                ProfessionalAthleteRelationship.athlete_id == athlete.athlete_id,
                ProfessionalAthleteRelationship.professional_role == PHYSIO_RELATIONSHIP_ROLE,
                ProfessionalAthleteRelationship.status == ProfessionalAthleteRelationshipStatus.ACTIVE.value,
            )
            .all()
        )
    ]

    activity = (
        db.query(RehabilitationActivity)
        .join(
            RehabilitationPlan,
            RehabilitationPlan.rehabilitation_plan_id == RehabilitationActivity.rehabilitation_plan_id,
        )
        .filter(
            RehabilitationActivity.activity_id == activity_id,
            RehabilitationPlan.athlete_id == athlete.athlete_id,
            RehabilitationPlan.physiotherapist_user_id.in_(active_physio_user_ids or []),
        )
        .first()
    )
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rehabilitation activity not found",
        )

    activity.status = activity_data.status
    activity.athlete_notes = activity_data.athlete_notes
    activity.completed_at = (
        datetime.now(timezone.utc)
        if activity_data.status == RehabilitationActivityStatus.COMPLETED.value
        else None
    )

    plan = db.query(RehabilitationPlan).filter(
        RehabilitationPlan.rehabilitation_plan_id == activity.rehabilitation_plan_id
    ).first()
    if plan:
        activities = (
            db.query(RehabilitationActivity)
            .filter(RehabilitationActivity.rehabilitation_plan_id == plan.rehabilitation_plan_id)
            .all()
        )
        available, progress = _calculate_activity_progress(activities)
        plan.progress = progress if available else 0

    db.commit()
    db.refresh(activity)
    return activity


@router.post(
    "/physiotherapist-requests/{relationship_id}/accept",
    response_model=PhysiotherapistRelationshipResponse,
)
def accept_physiotherapist_request(
    relationship_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    athlete = _get_current_athlete(current_user, db)
    relationship = _get_athlete_relationship(relationship_id, athlete, db, PHYSIO_RELATIONSHIP_ROLE)

    if relationship.status != ProfessionalAthleteRelationshipStatus.PENDING.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending physiotherapist requests can be accepted"
        )

    now = datetime.now(timezone.utc)
    relationship.status = ProfessionalAthleteRelationshipStatus.ACTIVE.value
    relationship.responded_at = now
    relationship.accepted_at = now
    create_notification(
        db,
        recipient_user_id=relationship.professional_user_id,
        notification_type=NotificationType.CONNECTION_ACCEPTED,
        title="Connection request accepted",
        message=f"{current_user.name} accepted your Physiotherapist connection request.",
        actor_user_id=current_user.user_id,
        entity_type="professional_athlete_relationship",
        entity_id=relationship.relationship_id,
        action_url="/physiotherapist/athletes",
    )

    db.commit()
    db.refresh(relationship)

    return relationship


@router.post(
    "/physiotherapist-requests/{relationship_id}/reject",
    response_model=PhysiotherapistRelationshipResponse,
)
def reject_physiotherapist_request(
    relationship_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    athlete = _get_current_athlete(current_user, db)
    relationship = _get_athlete_relationship(relationship_id, athlete, db, PHYSIO_RELATIONSHIP_ROLE)

    if relationship.status != ProfessionalAthleteRelationshipStatus.PENDING.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending physiotherapist requests can be rejected"
        )

    relationship.status = ProfessionalAthleteRelationshipStatus.REJECTED.value
    relationship.responded_at = datetime.now(timezone.utc)
    relationship.accepted_at = None
    create_notification(
        db,
        recipient_user_id=relationship.professional_user_id,
        notification_type=NotificationType.CONNECTION_REJECTED,
        title="Connection request rejected",
        message=f"{current_user.name} rejected your Physiotherapist connection request.",
        actor_user_id=current_user.user_id,
        entity_type="professional_athlete_relationship",
        entity_id=relationship.relationship_id,
        action_url="/physiotherapist/requests",
    )

    db.commit()
    db.refresh(relationship)

    return relationship


@router.post(
    "/physiotherapists/{relationship_id}/revoke",
    response_model=PhysiotherapistRelationshipResponse,
)
def revoke_physiotherapist_access(
    relationship_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    athlete = _get_current_athlete(current_user, db)
    relationship = _get_athlete_relationship(relationship_id, athlete, db, PHYSIO_RELATIONSHIP_ROLE)

    if relationship.status != ProfessionalAthleteRelationshipStatus.ACTIVE.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only active physiotherapist relationships can be revoked"
        )

    relationship.status = ProfessionalAthleteRelationshipStatus.REVOKED.value
    relationship.responded_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(relationship)

    return relationship


@router.post(
    "/sports-scientist-requests/{relationship_id}/accept",
    response_model=SportsScientistRelationshipResponse,
)
def accept_sports_scientist_request(
    relationship_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    athlete = _get_current_athlete(current_user, db)
    relationship = _get_athlete_relationship(
        relationship_id,
        athlete,
        db,
        SPORTS_SCIENTIST_RELATIONSHIP_ROLE,
    )

    if relationship.status != ProfessionalAthleteRelationshipStatus.PENDING.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending Sports Scientist requests can be accepted",
        )

    now = datetime.now(timezone.utc)
    relationship.status = ProfessionalAthleteRelationshipStatus.ACTIVE.value
    relationship.responded_at = now
    relationship.accepted_at = now
    create_notification(
        db,
        recipient_user_id=relationship.professional_user_id,
        notification_type=NotificationType.CONNECTION_ACCEPTED,
        title="Connection request accepted",
        message=f"{current_user.name} accepted your Sports Scientist connection request.",
        actor_user_id=current_user.user_id,
        entity_type="professional_athlete_relationship",
        entity_id=relationship.relationship_id,
        action_url="/sports-scientist/athletes",
    )

    db.commit()
    db.refresh(relationship)

    return relationship


@router.post(
    "/sports-scientist-requests/{relationship_id}/reject",
    response_model=SportsScientistRelationshipResponse,
)
def reject_sports_scientist_request(
    relationship_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    athlete = _get_current_athlete(current_user, db)
    relationship = _get_athlete_relationship(
        relationship_id,
        athlete,
        db,
        SPORTS_SCIENTIST_RELATIONSHIP_ROLE,
    )

    if relationship.status != ProfessionalAthleteRelationshipStatus.PENDING.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending Sports Scientist requests can be rejected",
        )

    relationship.status = ProfessionalAthleteRelationshipStatus.REJECTED.value
    relationship.responded_at = datetime.now(timezone.utc)
    relationship.accepted_at = None
    create_notification(
        db,
        recipient_user_id=relationship.professional_user_id,
        notification_type=NotificationType.CONNECTION_REJECTED,
        title="Connection request rejected",
        message=f"{current_user.name} rejected your Sports Scientist connection request.",
        actor_user_id=current_user.user_id,
        entity_type="professional_athlete_relationship",
        entity_id=relationship.relationship_id,
        action_url="/sports-scientist/athletes",
    )

    db.commit()
    db.refresh(relationship)

    return relationship


@router.post(
    "/sports-scientists/{relationship_id}/revoke",
    response_model=SportsScientistRelationshipResponse,
)
def revoke_sports_scientist_access(
    relationship_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    athlete = _get_current_athlete(current_user, db)
    relationship = _get_athlete_relationship(
        relationship_id,
        athlete,
        db,
        SPORTS_SCIENTIST_RELATIONSHIP_ROLE,
    )

    if relationship.status != ProfessionalAthleteRelationshipStatus.ACTIVE.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only active Sports Scientist relationships can be revoked",
        )

    relationship.status = ProfessionalAthleteRelationshipStatus.REVOKED.value
    relationship.responded_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(relationship)

    return relationship


@router.post(
    "/coach-requests/{relationship_id}/reject",
    response_model=CoachRelationshipResponse,
)
def reject_coach_request(
    relationship_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    athlete = _get_current_athlete(current_user, db)
    relationship = _get_athlete_relationship(relationship_id, athlete, db)

    if relationship.status != ProfessionalAthleteRelationshipStatus.PENDING.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending coach requests can be rejected"
        )

    relationship.status = ProfessionalAthleteRelationshipStatus.REJECTED.value
    relationship.responded_at = datetime.now(timezone.utc)
    relationship.accepted_at = None
    create_notification(
        db,
        recipient_user_id=relationship.professional_user_id,
        notification_type=NotificationType.CONNECTION_REJECTED,
        title="Connection request rejected",
        message=f"{current_user.name} rejected your Coach connection request.",
        actor_user_id=current_user.user_id,
        entity_type="professional_athlete_relationship",
        entity_id=relationship.relationship_id,
        action_url="/coach/requests",
    )

    db.commit()
    db.refresh(relationship)

    return relationship


@router.post(
    "/coaches/{relationship_id}/revoke",
    response_model=CoachRelationshipResponse,
)
def revoke_coach_access(
    relationship_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    athlete = _get_current_athlete(current_user, db)
    relationship = _get_athlete_relationship(relationship_id, athlete, db)

    if relationship.status != ProfessionalAthleteRelationshipStatus.ACTIVE.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only active coach relationships can be revoked"
        )

    relationship.status = ProfessionalAthleteRelationshipStatus.REVOKED.value
    relationship.responded_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(relationship)

    return relationship
