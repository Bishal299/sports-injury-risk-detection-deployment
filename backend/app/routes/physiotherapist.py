from datetime import date, datetime, time, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.dependencies.auth import require_roles
from app.dependencies.professional_access import (
    get_verified_professional_profile as require_verified_professional_profile,
    require_active_professional_access,
    require_role_permission,
)
from app.models.analysis_result import AnalysisResult
from app.models.athlete import Athlete
from app.models.physiotherapist_note import PhysiotherapistNote
from app.models.professional_athlete_relationship import (
    ProfessionalAthleteRelationship,
    ProfessionalAthleteRelationshipRole,
    ProfessionalAthleteRelationshipStatus,
)
from app.models.professional_profile import (
    ProfessionalProfile,
    ProfessionalProfileRole,
)
from app.models.rehabilitation_plan import (
    RehabilitationPlan,
    RehabilitationPlanPhase,
    RehabilitationPlanStatus,
)
from app.models.rehabilitation_activity import (
    RehabilitationActivity,
    RehabilitationActivityPriority,
    RehabilitationActivityStatus,
)
from app.models.user import User, UserRole
from app.models.video import Video
from app.models.notification import NotificationType
from app.services.notifications import create_notification
from app.services.professional_analysis import (
    build_movement_comparison_payload,
    get_analysis_score,
    get_existing_analysis_report_path,
    normalize_risk_category,
    normalize_risk_category_label,
)
from app.schemas.coach_athlete import CoachAthleteAnalysisItem, CoachAthleteVideoItem
from app.services.reports.pdf_generator import generate_recovery_summary_pdf
from app.schemas.physiotherapist import (
    MovementComparisonResponse,
    PhysiotherapistAthleteDetailResponse,
    PhysiotherapistAthleteItem,
    PhysiotherapistDashboardResponse,
    PhysiotherapistDiscoveryItem,
    PhysiotherapistNoteCreate,
    PhysiotherapistNoteResponse,
    PhysiotherapistRelationshipResponse,
    RehabilitationActivityCreate,
    RehabilitationActivityResponse,
    RehabilitationActivityUpdate,
    RehabilitationPlanCreate,
    RehabilitationPlanResponse,
    RehabilitationPlanUpdate,
)
from app.schemas.professional_profile import ProfessionalProfileResponse, ProfessionalProfileUpdate


router = APIRouter(prefix="/physiotherapist", tags=["Physiotherapist"])

PHYSIO_ROLE = ProfessionalAthleteRelationshipRole.PHYSIOTHERAPIST.value
HIGH_RISK_CATEGORIES = {"HIGH", "CRITICAL"}
VALID_REHAB_PHASES = {phase.value for phase in RehabilitationPlanPhase}
VALID_REHAB_STATUSES = {status.value for status in RehabilitationPlanStatus}
VALID_ACTIVITY_STATUSES = {status.value for status in RehabilitationActivityStatus}
VALID_ACTIVITY_PRIORITIES = {priority.value for priority in RehabilitationActivityPriority}


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


def _sync_plan_progress(db: Session, plan: RehabilitationPlan):
    activities = (
        db.query(RehabilitationActivity)
        .filter(RehabilitationActivity.rehabilitation_plan_id == plan.rehabilitation_plan_id)
        .all()
    )
    available, progress = _calculate_activity_progress(activities)
    plan.progress = progress if available else 0
    return available, progress


def build_rehabilitation_plan_response(plan: RehabilitationPlan | None):
    if not plan:
        return None

    available, progress = _calculate_activity_progress(list(plan.activities or []))
    return RehabilitationPlanResponse(
        rehabilitation_plan_id=plan.rehabilitation_plan_id,
        athlete_id=plan.athlete_id,
        physiotherapist_user_id=plan.physiotherapist_user_id,
        injury_context=plan.injury_context,
        start_date=plan.start_date,
        target_date=plan.target_date,
        current_phase=plan.current_phase,
        progress=progress if available else plan.progress,
        goals=plan.goals,
        completed_activities=plan.completed_activities,
        pending_activities=plan.pending_activities,
        recent_assessment=plan.recent_assessment,
        status=plan.status,
        notes=plan.notes,
        progress_available=available,
        calculated_progress=progress,
        activities=list(plan.activities or []),
        created_at=plan.created_at,
        updated_at=plan.updated_at,
    )


def get_verified_physiotherapist_profile(
    current_user: User = Depends(require_roles(UserRole.PHYSIOTHERAPIST)),
    db: Session = Depends(get_db),
) -> ProfessionalProfile:
    profile = (
        require_verified_professional_profile(
            db=db,
            current_user=current_user,
            professional_role=ProfessionalProfileRole.PHYSIOTHERAPIST.value,
        )
    )
    return profile


def get_active_physio_relationship(
    athlete_id: UUID,
    physio_profile: ProfessionalProfile,
    db: Session,
    permission: str,
) -> ProfessionalAthleteRelationship:
    physio_user = db.query(User).filter(User.user_id == physio_profile.user_id).first()
    if not physio_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Verified professional role required",
        )
    return require_active_professional_access(
        db=db,
        current_user=physio_user,
        athlete_id=athlete_id,
        professional_role=PHYSIO_ROLE,
        permission=permission,
    )


def active_relationships_query(db: Session, physio_profile: ProfessionalProfile):
    return (
        db.query(ProfessionalAthleteRelationship)
        .options(joinedload(ProfessionalAthleteRelationship.athlete).joinedload(Athlete.user))
        .filter(
            ProfessionalAthleteRelationship.professional_user_id == physio_profile.user_id,
            ProfessionalAthleteRelationship.professional_role == PHYSIO_ROLE,
            ProfessionalAthleteRelationship.status == ProfessionalAthleteRelationshipStatus.ACTIVE.value,
        )
    )


def latest_completed_analyses(db: Session, athlete_id, limit=2):
    return (
        db.query(AnalysisResult)
        .options(joinedload(AnalysisResult.video))
        .filter(
            AnalysisResult.athlete_id == athlete_id,
            AnalysisResult.status == "completed",
        )
        .order_by(
            AnalysisResult.completed_at.desc().nullslast(),
            AnalysisResult.analysis_date.desc(),
            AnalysisResult.created_at.desc(),
        )
        .limit(limit)
        .all()
    )


def get_latest_plan(db: Session, physio_user_id, athlete_id):
    return (
        db.query(RehabilitationPlan)
        .filter(
            RehabilitationPlan.physiotherapist_user_id == physio_user_id,
            RehabilitationPlan.athlete_id == athlete_id,
        )
        .order_by(RehabilitationPlan.created_at.desc())
        .first()
    )


def build_discovery_item(athlete, latest_analysis, connection_status):
    latest_score = get_analysis_score(latest_analysis)
    return PhysiotherapistDiscoveryItem(
        athlete_id=athlete.athlete_id,
        name=athlete.user.name if athlete.user else "Athlete",
        sport=athlete.sport,
        age=athlete.age,
        availability="AVAILABLE",
        latest_risk_score=latest_score,
        risk_category=normalize_risk_category_label(
            latest_analysis.risk_category if latest_analysis else None,
            latest_score,
        ),
        connection_status=connection_status or "NONE",
        latest_activity_at=latest_analysis.completed_at if latest_analysis else None,
    )


def risk_trend(latest_score, previous_score):
    if latest_score is None or previous_score is None:
        return "Not Available"
    if latest_score > previous_score:
        return "Increasing"
    if latest_score < previous_score:
        return "Decreasing"
    return "Stable"


def _event_datetime(value):
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, time.min)
    return None


def _event_sort_value(value):
    event_time = _event_datetime(value)
    if not event_time:
        return 0
    if event_time.tzinfo is not None:
        event_time = event_time.astimezone(timezone.utc).replace(tzinfo=None)
    return event_time.timestamp()


def _activity_event_time(activity: RehabilitationActivity):
    return (
        activity.completed_at
        or activity.updated_at
        or activity.created_at
    )


def build_rehabilitation_monitoring(plan: RehabilitationPlan | None):
    if not plan:
        return {
            "has_plan": False,
            "progress_available": False,
            "calculated_progress": None,
            "current_phase": None,
            "completed_activity_count": 0,
            "pending_activity_count": 0,
            "activity_count": 0,
            "recent_rehabilitation_activity": None,
            "next_review_date": None,
        }

    activities = list(plan.activities or [])
    available, progress = _calculate_activity_progress(activities)
    completed = [
        activity
        for activity in activities
        if activity.status == RehabilitationActivityStatus.COMPLETED.value
    ]
    pending = [
        activity
        for activity in activities
        if activity.status != RehabilitationActivityStatus.COMPLETED.value
    ]
    recent_activity = max(
        activities,
        key=lambda activity: _activity_event_time(activity) or datetime.min,
        default=None,
    )

    return {
        "has_plan": True,
        "progress_available": available,
        "calculated_progress": progress,
        "current_phase": plan.current_phase,
        "completed_activity_count": len(completed),
        "pending_activity_count": len(pending),
        "activity_count": len(activities),
        "recent_rehabilitation_activity": {
            "activity_id": recent_activity.activity_id,
            "title": recent_activity.title,
            "status": recent_activity.status,
            "phase": recent_activity.phase,
            "date": _activity_event_time(recent_activity),
        } if recent_activity else None,
        "next_review_date": plan.target_date,
    }


def build_needs_attention(plan: RehabilitationPlan | None, latest_score, previous_score):
    alerts = []
    today = datetime.now(timezone.utc).date()

    if plan:
        activities = list(plan.activities or [])
        overdue_activities = [
            activity
            for activity in activities
            if activity.due_date
            and activity.due_date < today
            and activity.status not in {
                RehabilitationActivityStatus.COMPLETED.value,
                RehabilitationActivityStatus.SKIPPED.value,
            }
        ]
        if overdue_activities:
            alerts.append({
                "type": "OVERDUE_ACTIVITIES",
                "title": "Overdue rehabilitation activities",
                "detail": f"{len(overdue_activities)} activity pending past due date.",
                "severity": "HIGH",
                "date": min(activity.due_date for activity in overdue_activities),
            })

        if plan.target_date and plan.target_date < today and plan.status in {
            RehabilitationPlanStatus.ACTIVE.value,
            RehabilitationPlanStatus.PAUSED.value,
        }:
            alerts.append({
                "type": "MISSED_REVIEW",
                "title": "Review date missed",
                "detail": "The plan target/review date has passed.",
                "severity": "HIGH",
                "date": plan.target_date,
            })

        completed_activity_times = [
            activity.completed_at
            for activity in activities
            if activity.completed_at is not None
        ]
        if activities and not completed_activity_times:
            alerts.append({
                "type": "NO_COMPLETED_ACTIVITY",
                "title": "No completed rehabilitation activity",
                "detail": "Activities exist, but none have been completed yet.",
                "severity": "MODERATE",
                "date": plan.created_at,
            })

    if latest_score is not None and previous_score is not None:
        change = latest_score - previous_score
        if change >= 10:
            alerts.append({
                "type": "RISK_INCREASE",
                "title": "Meaningful risk increase",
                "detail": f"Risk score increased by {change:.1f} points.",
                "severity": normalize_risk_category(latest_score),
                "date": datetime.now(timezone.utc),
            })

    alerts.sort(key=lambda item: _event_sort_value(item.get("date")), reverse=True)
    return alerts


def plan_needs_attention(plan):
    if not plan:
        return True
    return plan.status == RehabilitationPlanStatus.PAUSED.value or (
        plan.target_date is not None and plan.target_date < datetime.now(timezone.utc).date()
    )


def build_athlete_item(db: Session, relationship: ProfessionalAthleteRelationship):
    athlete = relationship.athlete
    analyses = latest_completed_analyses(db, athlete.athlete_id, limit=2)
    latest = analyses[0] if analyses else None
    previous = analyses[1] if len(analyses) > 1 else None
    latest_score = get_analysis_score(latest)
    previous_score = get_analysis_score(previous)
    plan = get_latest_plan(db, relationship.professional_user_id, athlete.athlete_id)

    return PhysiotherapistAthleteItem(
        relationship_id=relationship.relationship_id,
        athlete_id=athlete.athlete_id,
        name=athlete.user.name if athlete.user else "Athlete",
        sport=athlete.sport,
        current_risk_score=latest_score,
        risk_category=normalize_risk_category_label(latest.risk_category if latest else None, latest_score),
        previous_risk_score=previous_score,
        risk_trend=risk_trend(latest_score, previous_score),
        latest_analysis_at=latest.completed_at if latest else None,
        latest_analysis_id=latest.analysis_id if latest else None,
        latest_video_id=latest.video_id if latest else None,
        recovery_progress=plan.progress if plan else None,
        rehabilitation_status=plan.status if plan else "NOT_STARTED",
        current_phase=plan.current_phase if plan else None,
        needs_attention=plan_needs_attention(plan)
        or normalize_risk_category_label(latest.risk_category if latest else None, latest_score) in HIGH_RISK_CATEGORIES,
    )


def analysis_to_dict(analysis):
    if not analysis:
        return None
    score = get_analysis_score(analysis)
    return {
        "analysis_id": analysis.analysis_id,
        "video_id": analysis.video_id,
        "video_activity": analysis.video.activity if analysis.video else None,
        "analysis_date": analysis.analysis_date,
        "completed_at": analysis.completed_at,
        "status": analysis.status,
        "algorithm_version": analysis.algorithm_version,
        "historical_score": analysis.historical_score,
        "biomechanical_score": analysis.biomechanical_score,
        "asymmetry_score": analysis.asymmetry_score,
        "training_load_score": analysis.training_load_score,
        "composite_risk_score": analysis.composite_risk_score,
        "overall_risk_score": analysis.overall_risk_score,
        "risk_category": normalize_risk_category_label(analysis.risk_category, score),
        "knee_valgus": analysis.knee_valgus,
        "hip_stability": analysis.hip_stability,
        "trunk_lean": analysis.trunk_lean,
        "stride_length": analysis.stride_length,
        "joint_alignment": analysis.joint_alignment,
        "symmetry_score": analysis.symmetry_score,
        "fatigue_score": analysis.fatigue_score,
        "movement_quality": analysis.movement_quality,
        "summary_metrics": analysis.summary_metrics,
        "time_series_data": analysis.time_series_data,
        "recommendations": analysis.recommendations,
        "risk_assessment": analysis.summary_metrics.get("risk_assessment")
        if isinstance(analysis.summary_metrics, dict)
        else None,
        "skeleton_video_url": analysis.skeleton_video_url,
        "pdf_report_url": analysis.pdf_report_url,
        "csv_report_url": None,
        "pdf_report_available": get_existing_analysis_report_path(analysis.video_id, "pdf") is not None,
        "csv_report_available": False,
    }


def video_to_dict(db: Session, video):
    latest = (
        db.query(AnalysisResult)
        .filter(AnalysisResult.video_id == video.video_id)
        .order_by(
            AnalysisResult.completed_at.desc().nullslast(),
            AnalysisResult.analysis_date.desc(),
            AnalysisResult.created_at.desc(),
        )
        .first()
    )
    latest_score = get_analysis_score(latest)
    return {
        "video_id": video.video_id,
        "activity": video.activity,
        "video_url": video.video_url,
        "uploaded_at": video.uploaded_at,
        "processing_status": video.processing_status,
        "duration": video.duration,
        "fps": video.fps,
        "resolution": video.resolution,
        "latest_analysis_id": latest.analysis_id if latest else None,
        "latest_risk_score": latest_score,
        "risk_category": normalize_risk_category_label(latest.risk_category if latest else None, latest_score),
        "analysis_status": latest.status if latest else video.processing_status or "pending",
    }


def build_risk_history(analyses: list[AnalysisResult]):
    items = []
    for analysis in analyses:
        score = get_analysis_score(analysis)
        if score is None and not analysis.risk_category:
            continue
        items.append({
            "date": analysis.completed_at or analysis.analysis_date,
            "risk_score": score,
            "risk_category": normalize_risk_category_label(analysis.risk_category, score),
            "analysis_id": analysis.analysis_id,
        })
    return items


def build_movement_comparison(analyses):
    payload = build_movement_comparison_payload(analyses)
    initial = payload["initial_assessment"]
    latest = payload["latest_assessment"]

    return MovementComparisonResponse(
        initial_assessment=analysis_to_dict(initial) if initial else None,
        latest_assessment=analysis_to_dict(latest) if latest else None,
        comparison=payload["comparison"],
        comparison_status=payload["comparison_status"],
    )


def build_timeline(plan, analyses, notes):
    events = []
    if plan:
        events.append({
            "type": "rehabilitation_plan_created",
            "title": "Rehabilitation plan created",
            "date": plan.created_at,
        })
        if plan.updated_at and plan.created_at and plan.updated_at > plan.created_at:
            events.append({
                "type": "review_update",
                "title": "Review/update",
                "date": plan.updated_at,
            })
        if plan.target_date:
            events.append({
                "type": "next_review",
                "title": "Next review",
                "date": plan.target_date,
            })
        for activity in list(plan.activities or []):
            if activity.completed_at:
                events.append({
                    "type": "activity_completed",
                    "title": f"Activity completed: {activity.title}",
                    "date": activity.completed_at,
                })
    for index, analysis in enumerate(reversed(analyses)):
        events.append({
            "type": "movement_analysis",
            "title": "Analysis performed" if index else "Initial assessment",
            "date": analysis.completed_at or analysis.analysis_date,
        })
    for note in notes[:5]:
        events.append({
            "type": "physiotherapist_note",
            "title": note.title or "Progress assessment",
            "date": note.created_at,
        })
    events.sort(key=lambda item: _event_sort_value(item.get("date")), reverse=True)
    return events


@router.get("/profile", response_model=ProfessionalProfileResponse)
def get_my_profile(
    profile: ProfessionalProfile = Depends(get_verified_physiotherapist_profile),
):
    return profile


@router.put("/profile", response_model=ProfessionalProfileResponse)
def update_my_profile(
    profile_data: ProfessionalProfileUpdate,
    profile: ProfessionalProfile = Depends(get_verified_physiotherapist_profile),
    db: Session = Depends(get_db),
):
    update_data = profile_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/dashboard", response_model=PhysiotherapistDashboardResponse)
def get_dashboard(
    profile: ProfessionalProfile = Depends(get_verified_physiotherapist_profile),
    db: Session = Depends(get_db),
):
    relationships = active_relationships_query(db, profile).all()
    items = [build_athlete_item(db, relationship) for relationship in relationships if relationship.athlete]
    recovering = sum(1 for item in items if item.rehabilitation_status in {"ACTIVE", "PAUSED"})
    high_risk = sum(1 for item in items if item.risk_category in HIGH_RISK_CATEGORIES)
    needs_attention = sum(1 for item in items if item.needs_attention)
    items.sort(key=lambda item: item.latest_analysis_at or datetime.min, reverse=True)

    return PhysiotherapistDashboardResponse(
        physiotherapist_user_id=profile.user_id,
        verification_status=profile.verification_status,
        stats={
            "total_athletes": len(items),
            "recovering": recovering,
            "high_risk": high_risk,
            "needs_attention": needs_attention,
        },
        athletes=items[:5],
        attention=[
            {
                "athlete_id": item.athlete_id,
                "athlete_name": item.name,
                "risk_category": item.risk_category,
                "rehabilitation_status": item.rehabilitation_status,
                "latest_analysis_at": item.latest_analysis_at,
            }
            for item in items
            if item.needs_attention
        ][:6],
    )


@router.get("/athletes/discover", response_model=list[PhysiotherapistDiscoveryItem])
def discover_athletes(
    search: str | None = Query(default=None),
    sport: str | None = Query(default=None),
    risk_category: str | None = Query(default=None),
    connection_status: str | None = Query(default=None),
    sort: str = Query(default="name"),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    profile: ProfessionalProfile = Depends(get_verified_physiotherapist_profile),
    db: Session = Depends(get_db),
):
    query = (
        db.query(Athlete)
        .join(User, Athlete.user_id == User.user_id)
        .filter(User.role == UserRole.ATHLETE)
        .options(joinedload(Athlete.user))
    )
    if search:
        query = query.filter(User.name.ilike(f"%{search}%"))
    if sport:
        query = query.filter(Athlete.sport.ilike(f"%{sport}%"))

    items = []
    for athlete in query.all():
        active_professional_relationship = (
            db.query(ProfessionalAthleteRelationship)
            .filter(
                ProfessionalAthleteRelationship.athlete_id == athlete.athlete_id,
                ProfessionalAthleteRelationship.status == ProfessionalAthleteRelationshipStatus.ACTIVE.value,
            )
            .first()
        )
        if active_professional_relationship:
            continue

        relationship = (
            db.query(ProfessionalAthleteRelationship)
            .filter(
                ProfessionalAthleteRelationship.professional_user_id == profile.user_id,
                ProfessionalAthleteRelationship.athlete_id == athlete.athlete_id,
                ProfessionalAthleteRelationship.professional_role == PHYSIO_ROLE,
            )
            .order_by(ProfessionalAthleteRelationship.created_at.desc())
            .first()
        )
        latest = latest_completed_analyses(db, athlete.athlete_id, limit=1)
        item = build_discovery_item(athlete, latest[0] if latest else None, relationship.status if relationship else "NONE")
        if connection_status and item.connection_status != connection_status.upper():
            continue
        if risk_category and item.risk_category != risk_category.upper():
            continue
        items.append(item)

    if sort == "risk_desc":
        items.sort(key=lambda item: item.latest_risk_score if item.latest_risk_score is not None else -1, reverse=True)
    elif sort == "risk_asc":
        items.sort(key=lambda item: item.latest_risk_score if item.latest_risk_score is not None else 101)
    elif sort == "recent":
        items.sort(key=lambda item: item.latest_activity_at or datetime.min, reverse=True)
    else:
        items.sort(key=lambda item: item.name.lower())

    return items[offset:offset + limit]


@router.post(
    "/athletes/{athlete_id}/connection-requests",
    response_model=PhysiotherapistRelationshipResponse,
    status_code=status.HTTP_201_CREATED,
)
def send_connection_request(
    athlete_id: UUID,
    profile: ProfessionalProfile = Depends(get_verified_physiotherapist_profile),
    db: Session = Depends(get_db),
):
    athlete = db.query(Athlete).filter(Athlete.athlete_id == athlete_id).first()
    if not athlete:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Athlete not found")

    existing = (
        db.query(ProfessionalAthleteRelationship)
        .filter(
            ProfessionalAthleteRelationship.professional_user_id == profile.user_id,
            ProfessionalAthleteRelationship.athlete_id == athlete_id,
            ProfessionalAthleteRelationship.professional_role == PHYSIO_ROLE,
            ProfessionalAthleteRelationship.status.in_([
                ProfessionalAthleteRelationshipStatus.PENDING.value,
                ProfessionalAthleteRelationshipStatus.ACTIVE.value,
            ]),
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A pending or active relationship already exists",
        )

    relationship = ProfessionalAthleteRelationship(
        professional_user_id=profile.user_id,
        athlete_id=athlete_id,
        professional_role=PHYSIO_ROLE,
        status=ProfessionalAthleteRelationshipStatus.PENDING.value,
        requested_by=profile.user_id,
    )
    db.add(relationship)
    db.flush()
    create_notification(
        db,
        recipient_user_id=athlete.user_id,
        notification_type=NotificationType.CONNECTION_REQUEST,
        title="Physiotherapist connection request",
        message="A Physiotherapist requested access to your rehabilitation profile.",
        actor_user_id=profile.user_id,
        entity_type="professional_athlete_relationship",
        entity_id=relationship.relationship_id,
        action_url="/dashboard",
    )
    db.commit()
    db.refresh(relationship)
    return relationship


@router.get("/requests", response_model=list[PhysiotherapistRelationshipResponse])
def get_my_requests(
    profile: ProfessionalProfile = Depends(get_verified_physiotherapist_profile),
    db: Session = Depends(get_db),
):
    return (
        db.query(ProfessionalAthleteRelationship)
        .options(
            joinedload(ProfessionalAthleteRelationship.athlete).joinedload(Athlete.user),
            joinedload(ProfessionalAthleteRelationship.professional_user).joinedload(
                User.professional_profiles
            ),
            joinedload(ProfessionalAthleteRelationship.requester),
        )
        .filter(
            ProfessionalAthleteRelationship.professional_user_id == profile.user_id,
            ProfessionalAthleteRelationship.professional_role == PHYSIO_ROLE,
        )
        .order_by(ProfessionalAthleteRelationship.created_at.desc())
        .all()
    )


def _get_incoming_coach_assignment(
    relationship_id: UUID,
    profile: ProfessionalProfile,
    db: Session,
) -> ProfessionalAthleteRelationship:
    relationship = (
        db.query(ProfessionalAthleteRelationship)
        .options(
            joinedload(ProfessionalAthleteRelationship.athlete).joinedload(Athlete.user),
            joinedload(ProfessionalAthleteRelationship.professional_user).joinedload(
                User.professional_profiles
            ),
            joinedload(ProfessionalAthleteRelationship.requester),
        )
        .filter(
            ProfessionalAthleteRelationship.relationship_id == relationship_id,
            ProfessionalAthleteRelationship.professional_user_id == profile.user_id,
            ProfessionalAthleteRelationship.professional_role == PHYSIO_ROLE,
        )
        .first()
    )
    if not relationship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Physiotherapist request not found",
        )

    if relationship.status != ProfessionalAthleteRelationshipStatus.PENDING.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending physiotherapist assignments can be updated",
        )

    if relationship.requested_by == profile.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Athlete approval is required for requests you initiated",
        )

    if relationship.requester and relationship.requester.role != UserRole.COACH:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Coach-assigned physiotherapist requests can be updated here",
        )

    return relationship


@router.post("/requests/{relationship_id}/accept", response_model=PhysiotherapistRelationshipResponse)
def accept_coach_assignment(
    relationship_id: UUID,
    profile: ProfessionalProfile = Depends(get_verified_physiotherapist_profile),
    db: Session = Depends(get_db),
):
    relationship = _get_incoming_coach_assignment(relationship_id, profile, db)

    now = datetime.now(timezone.utc)
    relationship.status = ProfessionalAthleteRelationshipStatus.ACTIVE.value
    relationship.responded_at = now
    relationship.accepted_at = now

    db.commit()
    db.refresh(relationship)
    return relationship


@router.post("/requests/{relationship_id}/reject", response_model=PhysiotherapistRelationshipResponse)
def reject_coach_assignment(
    relationship_id: UUID,
    profile: ProfessionalProfile = Depends(get_verified_physiotherapist_profile),
    db: Session = Depends(get_db),
):
    relationship = _get_incoming_coach_assignment(relationship_id, profile, db)

    relationship.status = ProfessionalAthleteRelationshipStatus.REJECTED.value
    relationship.responded_at = datetime.now(timezone.utc)
    relationship.accepted_at = None

    db.commit()
    db.refresh(relationship)
    return relationship


@router.get("/athletes", response_model=list[PhysiotherapistAthleteItem])
def get_my_athletes(
    search: str | None = None,
    risk_category: str | None = None,
    recovery_status: str | None = None,
    sort: str = "recent",
    limit: int = 50,
    offset: int = 0,
    profile: ProfessionalProfile = Depends(get_verified_physiotherapist_profile),
    db: Session = Depends(get_db),
):
    relationships = active_relationships_query(db, profile).all()
    items = [build_athlete_item(db, relationship) for relationship in relationships if relationship.athlete]
    if search:
        value = search.lower()
        items = [item for item in items if value in item.name.lower()]
    if risk_category and risk_category.upper() != "ALL":
        items = [item for item in items if item.risk_category == risk_category.upper()]
    if recovery_status and recovery_status.upper() != "ALL":
        items = [item for item in items if item.rehabilitation_status == recovery_status.upper()]
    if sort == "risk_desc":
        items.sort(key=lambda item: item.current_risk_score if item.current_risk_score is not None else -1, reverse=True)
    elif sort == "risk_asc":
        items.sort(key=lambda item: item.current_risk_score if item.current_risk_score is not None else 101)
    elif sort == "name":
        items.sort(key=lambda item: item.name.lower())
    else:
        items.sort(key=lambda item: item.latest_analysis_at or datetime.min, reverse=True)
    return items[offset:offset + limit]


@router.get("/athletes/{athlete_id}", response_model=PhysiotherapistAthleteDetailResponse)
def get_athlete_detail(
    athlete_id: UUID,
    profile: ProfessionalProfile = Depends(get_verified_physiotherapist_profile),
    db: Session = Depends(get_db),
):
    get_active_physio_relationship(
        athlete_id, profile, db, permission="athlete_profile"
    )
    for permission in (
        "risk_results",
        "videos",
        "analyses",
        "rehabilitation",
        "recovery",
        "movement_analytics",
        "physiotherapist_notes",
    ):
        require_role_permission(PHYSIO_ROLE, permission)
    athlete = db.query(Athlete).options(joinedload(Athlete.user)).filter(Athlete.athlete_id == athlete_id).first()
    if not athlete:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Athlete not found")

    analyses = (
        db.query(AnalysisResult)
        .options(joinedload(AnalysisResult.video))
        .filter(AnalysisResult.athlete_id == athlete_id)
        .order_by(
            AnalysisResult.completed_at.desc().nullslast(),
            AnalysisResult.analysis_date.desc(),
            AnalysisResult.created_at.desc(),
        )
        .all()
    )
    completed = [analysis for analysis in analyses if analysis.status == "completed"]
    latest = completed[0] if completed else None
    previous = completed[1] if len(completed) > 1 else None
    latest_score = get_analysis_score(latest)
    previous_score = get_analysis_score(previous)
    videos = db.query(Video).filter(Video.athlete_id == athlete_id).order_by(Video.uploaded_at.desc()).all()
    plan = get_latest_plan(db, profile.user_id, athlete_id)
    notes = (
        db.query(PhysiotherapistNote)
        .filter(
            PhysiotherapistNote.physiotherapist_user_id == profile.user_id,
            PhysiotherapistNote.athlete_id == athlete_id,
        )
        .order_by(PhysiotherapistNote.created_at.desc())
        .all()
    )

    return PhysiotherapistAthleteDetailResponse(
        profile={
            "athlete_id": athlete.athlete_id,
            "user_id": athlete.user_id,
            "name": athlete.user.name if athlete.user else "Athlete",
            "email": athlete.user.email if athlete.user else "",
            "sport": athlete.sport,
            "position": athlete.position,
            "age": athlete.age,
            "height": athlete.height,
            "weight": athlete.weight,
        },
        risk_monitoring={
            "current_risk": latest_score,
            "risk_category": normalize_risk_category_label(latest.risk_category if latest else None, latest_score),
            "previous_risk": previous_score,
            "risk_trend": risk_trend(latest_score, previous_score),
        },
        rehabilitation_plan=build_rehabilitation_plan_response(plan),
        rehabilitation_monitoring=build_rehabilitation_monitoring(plan),
        needs_attention=build_needs_attention(plan, latest_score, previous_score),
        movement_comparison=build_movement_comparison(completed),
        latest_analysis=analysis_to_dict(latest),
        videos=[video_to_dict(db, video) for video in videos],
        analyses=[analysis_to_dict(analysis) for analysis in analyses],
        notes=notes,
        timeline=build_timeline(plan, completed, notes),
    )


def validate_rehab_payload(data):
    if data.current_phase and data.current_phase not in VALID_REHAB_PHASES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid rehabilitation phase")
    if data.status and data.status not in VALID_REHAB_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid rehabilitation status")


def validate_activity_payload(data):
    if data.phase and data.phase not in VALID_REHAB_PHASES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid rehabilitation phase")
    if data.priority and data.priority not in VALID_ACTIVITY_PRIORITIES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid activity priority")
    if data.status and data.status not in VALID_ACTIVITY_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid activity status")


def get_owned_rehabilitation_plan(
    plan_id: UUID,
    profile: ProfessionalProfile,
    db: Session,
) -> RehabilitationPlan:
    plan = (
        db.query(RehabilitationPlan)
        .filter(
            RehabilitationPlan.rehabilitation_plan_id == plan_id,
            RehabilitationPlan.physiotherapist_user_id == profile.user_id,
        )
        .first()
    )
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rehabilitation plan not found")

    get_active_physio_relationship(
        plan.athlete_id, profile, db, permission="rehabilitation"
    )
    return plan


@router.post("/athletes/{athlete_id}/rehabilitation-plans", response_model=RehabilitationPlanResponse)
def create_rehabilitation_plan(
    athlete_id: UUID,
    plan_data: RehabilitationPlanCreate,
    profile: ProfessionalProfile = Depends(get_verified_physiotherapist_profile),
    db: Session = Depends(get_db),
):
    get_active_physio_relationship(
        athlete_id, profile, db, permission="rehabilitation"
    )
    validate_rehab_payload(plan_data)
    plan = RehabilitationPlan(
        athlete_id=athlete_id,
        physiotherapist_user_id=profile.user_id,
        **plan_data.model_dump(),
    )
    db.add(plan)
    db.flush()
    athlete = db.query(Athlete).filter(Athlete.athlete_id == athlete_id).first()
    if athlete and athlete.user_id:
        create_notification(
            db,
            recipient_user_id=athlete.user_id,
            notification_type=NotificationType.REHAB_PLAN_CREATED,
            title="New rehabilitation plan",
            message="Your Physiotherapist created a rehabilitation plan.",
            actor_user_id=profile.user_id,
            entity_type="rehabilitation_plan",
            entity_id=plan.rehabilitation_plan_id,
            action_url="/my-rehabilitation",
        )
    db.commit()
    db.refresh(plan)
    return build_rehabilitation_plan_response(plan)


@router.put("/rehabilitation-plans/{plan_id}", response_model=RehabilitationPlanResponse)
def update_rehabilitation_plan(
    plan_id: UUID,
    plan_data: RehabilitationPlanUpdate,
    profile: ProfessionalProfile = Depends(get_verified_physiotherapist_profile),
    db: Session = Depends(get_db),
):
    plan = get_owned_rehabilitation_plan(plan_id, profile, db)

    update_data = plan_data.model_dump(exclude_unset=True)
    if "current_phase" in update_data and update_data["current_phase"] not in VALID_REHAB_PHASES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid rehabilitation phase")
    if "status" in update_data and update_data["status"] not in VALID_REHAB_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid rehabilitation status")
    for field, value in update_data.items():
        setattr(plan, field, value)
    create_notification(
        db,
        recipient_user_id=plan.athlete.user_id if plan.athlete else None,
        notification_type=NotificationType.REHAB_PLAN_UPDATED,
        title="Rehabilitation plan updated",
        message="Your Physiotherapist updated your rehabilitation plan.",
        actor_user_id=profile.user_id,
        entity_type="rehabilitation_plan_update",
        entity_id=plan.rehabilitation_plan_id,
        action_url="/my-rehabilitation",
        dedupe=False,
    ) if plan.athlete and plan.athlete.user_id else None
    db.commit()
    db.refresh(plan)
    return build_rehabilitation_plan_response(plan)


@router.post(
    "/rehabilitation-plans/{plan_id}/activities",
    response_model=RehabilitationActivityResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_rehabilitation_activity(
    plan_id: UUID,
    activity_data: RehabilitationActivityCreate,
    profile: ProfessionalProfile = Depends(get_verified_physiotherapist_profile),
    db: Session = Depends(get_db),
):
    plan = get_owned_rehabilitation_plan(plan_id, profile, db)
    validate_activity_payload(activity_data)

    activity = RehabilitationActivity(
        rehabilitation_plan_id=plan.rehabilitation_plan_id,
        **activity_data.model_dump(),
    )
    if activity.status == RehabilitationActivityStatus.COMPLETED.value:
        activity.completed_at = datetime.now(timezone.utc)

    db.add(activity)
    db.flush()
    db.refresh(plan)
    _sync_plan_progress(db, plan)
    db.commit()
    db.refresh(activity)
    return activity


@router.put(
    "/rehabilitation-activities/{activity_id}",
    response_model=RehabilitationActivityResponse,
)
def update_rehabilitation_activity(
    activity_id: UUID,
    activity_data: RehabilitationActivityUpdate,
    profile: ProfessionalProfile = Depends(get_verified_physiotherapist_profile),
    db: Session = Depends(get_db),
):
    activity = (
        db.query(RehabilitationActivity)
        .filter(RehabilitationActivity.activity_id == activity_id)
        .first()
    )
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rehabilitation activity not found")

    plan = get_owned_rehabilitation_plan(activity.rehabilitation_plan_id, profile, db)
    update_data = activity_data.model_dump(exclude_unset=True)
    if "phase" in update_data and update_data["phase"] not in VALID_REHAB_PHASES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid rehabilitation phase")
    if "priority" in update_data and update_data["priority"] not in VALID_ACTIVITY_PRIORITIES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid activity priority")
    if "status" in update_data and update_data["status"] not in VALID_ACTIVITY_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid activity status")

    for field, value in update_data.items():
        setattr(activity, field, value)
    if "status" in update_data:
        activity.completed_at = (
            datetime.now(timezone.utc)
            if update_data["status"] == RehabilitationActivityStatus.COMPLETED.value
            else None
        )

    _sync_plan_progress(db, plan)
    db.commit()
    db.refresh(activity)
    return activity


@router.delete("/rehabilitation-activities/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rehabilitation_activity(
    activity_id: UUID,
    profile: ProfessionalProfile = Depends(get_verified_physiotherapist_profile),
    db: Session = Depends(get_db),
):
    activity = (
        db.query(RehabilitationActivity)
        .filter(RehabilitationActivity.activity_id == activity_id)
        .first()
    )
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rehabilitation activity not found")

    plan = get_owned_rehabilitation_plan(activity.rehabilitation_plan_id, profile, db)
    db.delete(activity)
    db.flush()
    db.refresh(plan)
    _sync_plan_progress(db, plan)
    db.commit()


@router.get("/athletes/{athlete_id}/notes", response_model=list[PhysiotherapistNoteResponse])
def list_notes(
    athlete_id: UUID,
    profile: ProfessionalProfile = Depends(get_verified_physiotherapist_profile),
    db: Session = Depends(get_db),
):
    get_active_physio_relationship(
        athlete_id, profile, db, permission="physiotherapist_notes"
    )
    return (
        db.query(PhysiotherapistNote)
        .filter(
            PhysiotherapistNote.physiotherapist_user_id == profile.user_id,
            PhysiotherapistNote.athlete_id == athlete_id,
        )
        .order_by(PhysiotherapistNote.created_at.desc())
        .all()
    )


@router.post("/athletes/{athlete_id}/notes", response_model=PhysiotherapistNoteResponse)
def create_note(
    athlete_id: UUID,
    note_data: PhysiotherapistNoteCreate,
    profile: ProfessionalProfile = Depends(get_verified_physiotherapist_profile),
    db: Session = Depends(get_db),
):
    get_active_physio_relationship(
        athlete_id, profile, db, permission="physiotherapist_notes"
    )
    note = PhysiotherapistNote(
        athlete_id=athlete_id,
        physiotherapist_user_id=profile.user_id,
        **note_data.model_dump(),
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


@router.get(
    "/athletes/{athlete_id}/analyses/{analysis_id}",
    response_model=CoachAthleteAnalysisItem,
)
def get_connected_athlete_analysis(
    athlete_id: UUID,
    analysis_id: UUID,
    profile: ProfessionalProfile = Depends(get_verified_physiotherapist_profile),
    db: Session = Depends(get_db),
):
    get_active_physio_relationship(
        athlete_id, profile, db, permission="analyses"
    )

    analysis = (
        db.query(AnalysisResult)
        .options(joinedload(AnalysisResult.video))
        .filter(
            AnalysisResult.analysis_id == analysis_id,
            AnalysisResult.athlete_id == athlete_id,
        )
        .first()
    )
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")

    return CoachAthleteAnalysisItem(**analysis_to_dict(analysis))


@router.get(
    "/athletes/{athlete_id}/videos",
    response_model=list[CoachAthleteVideoItem],
)
def get_connected_athlete_videos(
    athlete_id: UUID,
    profile: ProfessionalProfile = Depends(get_verified_physiotherapist_profile),
    db: Session = Depends(get_db),
):
    get_active_physio_relationship(
        athlete_id, profile, db, permission="videos"
    )

    videos = (
        db.query(Video)
        .filter(Video.athlete_id == athlete_id)
        .order_by(Video.uploaded_at.desc())
        .all()
    )
    return [CoachAthleteVideoItem(**video_to_dict(db, video)) for video in videos]


@router.get(
    "/athletes/{athlete_id}/videos/{video_id}/analysis",
    response_model=CoachAthleteAnalysisItem,
)
def get_connected_athlete_video_analysis(
    athlete_id: UUID,
    video_id: UUID,
    analysis_id: UUID | None = Query(default=None),
    profile: ProfessionalProfile = Depends(get_verified_physiotherapist_profile),
    db: Session = Depends(get_db),
):
    get_active_physio_relationship(
        athlete_id, profile, db, permission="analyses"
    )

    video = (
        db.query(Video)
        .filter(Video.video_id == video_id, Video.athlete_id == athlete_id)
        .first()
    )
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")

    query = (
        db.query(AnalysisResult)
        .options(joinedload(AnalysisResult.video))
        .filter(
            AnalysisResult.video_id == video_id,
            AnalysisResult.athlete_id == athlete_id,
        )
    )
    if analysis_id:
        query = query.filter(AnalysisResult.analysis_id == analysis_id)

    analysis = (
        query.order_by(
            AnalysisResult.completed_at.desc().nullslast(),
            AnalysisResult.analysis_date.desc(),
            AnalysisResult.created_at.desc(),
        )
        .first()
    )
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")

    return CoachAthleteAnalysisItem(**analysis_to_dict(analysis))


@router.get("/athletes/{athlete_id}/videos/{video_id}/pdf")
def download_connected_athlete_analysis_pdf(
    athlete_id: UUID,
    video_id: UUID,
    profile: ProfessionalProfile = Depends(get_verified_physiotherapist_profile),
    db: Session = Depends(get_db),
):
    get_active_physio_relationship(
        athlete_id, profile, db, permission="recovery_reports"
    )
    video = (
        db.query(Video)
        .filter(Video.video_id == video_id, Video.athlete_id == athlete_id)
        .first()
    )
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    report_path = get_existing_analysis_report_path(video_id, "pdf")
    if not report_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF report file not found.",
        )

    return FileResponse(
        path=report_path,
        media_type="application/pdf",
        filename=f"movement_analysis_report_{video_id}.pdf",
    )


@router.get("/athletes/{athlete_id}/recovery-report/{file_type}")
def download_recovery_report(
    athlete_id: UUID,
    file_type: str,
    profile: ProfessionalProfile = Depends(get_verified_physiotherapist_profile),
    db: Session = Depends(get_db),
):
    if file_type != "pdf":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported report type")
    get_active_physio_relationship(
        athlete_id, profile, db, permission="recovery_reports"
    )
    detail = get_athlete_detail(athlete_id=athlete_id, profile=profile, db=db)
    physio_user = db.query(User).filter(User.user_id == profile.user_id).first()
    physiotherapist_info = {
        "name": physio_user.name if physio_user else None,
        "email": physio_user.email if physio_user else None,
        "organization": profile.organization,
        "specialization": profile.specialization,
    }
    completed_analyses = (
        db.query(AnalysisResult)
        .options(joinedload(AnalysisResult.video))
        .filter(
            AnalysisResult.athlete_id == athlete_id,
            AnalysisResult.status == "completed",
        )
        .order_by(
            AnalysisResult.completed_at.desc().nullslast(),
            AnalysisResult.analysis_date.desc(),
            AnalysisResult.created_at.desc(),
        )
        .all()
    )
    movement_payload = detail.movement_comparison.model_dump()
    initial_analysis = movement_payload.get("initial_assessment")
    latest_analysis = movement_payload.get("latest_assessment")
    risk_history = build_risk_history(completed_analyses)

    content = generate_recovery_summary_pdf(
        athlete_profile=detail.profile,
        risk_monitoring=detail.risk_monitoring,
        rehabilitation_plan=detail.rehabilitation_plan,
        movement_comparison=movement_payload,
        notes=detail.notes,
        physiotherapist_info=physiotherapist_info,
        rehabilitation_monitoring=detail.rehabilitation_monitoring,
        initial_analysis=initial_analysis,
        latest_analysis=latest_analysis,
        risk_history=risk_history,
        timeline=detail.timeline,
    )
    return StreamingResponse(
        iter([content]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=recovery_report_{athlete_id}.pdf"},
    )
