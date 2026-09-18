from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
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
from app.models.coach_profile import CoachProfile, CoachVerificationStatus
from app.models.coach_task import CoachTask, CoachTaskPriority, CoachTaskStatus
from app.models.professional_athlete_relationship import (
    ProfessionalAthleteRelationship,
    ProfessionalAthleteRelationshipRole,
    ProfessionalAthleteRelationshipStatus,
)
from app.models.professional_profile import (
    ProfessionalProfile,
    ProfessionalProfileRole,
    ProfessionalVerificationStatus,
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
from app.schemas.coach_athlete import (
    AthleteDiscoveryItem,
    CoachAthleteAnalysisItem,
    CoachAthleteDetailResponse,
    CoachAthleteVideoItem,
    CoachAssignablePhysiotherapist,
    CoachConnectedAthleteItem,
    CoachDashboardAlert,
    CoachDashboardResponse,
    CoachPrivateAthleteProfile,
    CoachRelationshipResponse,
    CoachTaskCreate,
    CoachTaskResponse,
    CoachTaskUpdate,
)
from app.schemas.physiotherapist import PhysiotherapistRelationshipResponse
from app.schemas.coach_profile import CoachProfileResponse, CoachProfileUpdate


router = APIRouter(
    prefix="/coach",
    tags=["Coach"]
)

COACH_RELATIONSHIP_ROLE = ProfessionalAthleteRelationshipRole.COACH.value
PHYSIO_RELATIONSHIP_ROLE = ProfessionalAthleteRelationshipRole.PHYSIOTHERAPIST.value
VALID_COACH_TASK_STATUSES = {status.value for status in CoachTaskStatus}
VALID_COACH_TASK_PRIORITIES = {priority.value for priority in CoachTaskPriority}


def get_verified_coach_profile(
    current_user: User = Depends(require_roles(UserRole.COACH)),
    db: Session = Depends(get_db),
) -> CoachProfile:
    if current_user.role != UserRole.COACH:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Verified Coach professional profile required",
        )

    coach_profile = (
        db.query(CoachProfile)
        .filter(CoachProfile.user_id == current_user.user_id)
        .first()
    )

    if not coach_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coach profile not found"
        )

    if coach_profile.verification_status != CoachVerificationStatus.VERIFIED.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Coach profile is not verified"
        )

    require_verified_professional_profile(
        db=db,
        current_user=current_user,
        professional_role=ProfessionalProfileRole.COACH.value,
    )

    return coach_profile


def get_active_coach_athlete_relationship(
    athlete_id: UUID,
    coach_profile: CoachProfile,
    db: Session,
    permission: str,
) -> ProfessionalAthleteRelationship:
    coach_user = db.query(User).filter(User.user_id == coach_profile.user_id).first()
    if not coach_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Verified professional role required",
        )
    return require_active_professional_access(
        db=db,
        current_user=coach_user,
        athlete_id=athlete_id,
        professional_role=COACH_RELATIONSHIP_ROLE,
        permission=permission,
    )


def get_latest_completed_analysis(db: Session, athlete_id):
    return (
        db.query(AnalysisResult)
        .filter(
            AnalysisResult.athlete_id == athlete_id,
            AnalysisResult.status == "completed",
        )
        .order_by(
            AnalysisResult.completed_at.desc().nullslast(),
            AnalysisResult.analysis_date.desc(),
            AnalysisResult.created_at.desc(),
        )
        .first()
    )


def build_discovery_item(athlete, latest_analysis, connection_status):
    latest_score = None

    if latest_analysis:
        latest_score = (
            latest_analysis.composite_risk_score
            if latest_analysis.composite_risk_score is not None
            else latest_analysis.overall_risk_score
        )

    return AthleteDiscoveryItem(
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
        latest_activity_at=latest_analysis.completed_at
        if latest_analysis
        else None,
    )


def get_report_path(video_id: UUID, file_type: str):
    return get_existing_analysis_report_path(video_id, file_type)


def get_active_relationships_query(db: Session, coach_profile: CoachProfile):
    return (
        db.query(ProfessionalAthleteRelationship)
        .options(
            joinedload(ProfessionalAthleteRelationship.athlete).joinedload(Athlete.user),
            joinedload(ProfessionalAthleteRelationship.professional_user).joinedload(
                User.professional_profiles
            ),
        )
        .filter(
            ProfessionalAthleteRelationship.professional_user_id == coach_profile.user_id,
            ProfessionalAthleteRelationship.professional_role == COACH_RELATIONSHIP_ROLE,
            ProfessionalAthleteRelationship.status == ProfessionalAthleteRelationshipStatus.ACTIVE.value,
        )
    )


def build_connected_athlete_item(db: Session, relationship: ProfessionalAthleteRelationship):
    athlete = relationship.athlete
    latest_analysis = get_latest_completed_analysis(db, athlete.athlete_id)
    latest_score = get_analysis_score(latest_analysis)
    video_count = (
        db.query(Video)
        .filter(Video.athlete_id == athlete.athlete_id)
        .count()
    )
    analysis_count = (
        db.query(AnalysisResult)
        .filter(AnalysisResult.athlete_id == athlete.athlete_id)
        .count()
    )

    return CoachConnectedAthleteItem(
        relationship_id=relationship.relationship_id,
        athlete_id=athlete.athlete_id,
        name=athlete.user.name if athlete.user else "Athlete",
        sport=athlete.sport,
        status=relationship.status,
        latest_risk_score=latest_score,
        risk_category=normalize_risk_category_label(
            latest_analysis.risk_category if latest_analysis else None,
            latest_score,
        ),
        last_analysis_at=latest_analysis.completed_at if latest_analysis else None,
        latest_activity_at=latest_analysis.completed_at
        if latest_analysis
        else relationship.accepted_at or relationship.created_at,
        video_count=video_count,
        analysis_count=analysis_count,
    )


def build_analysis_item(analysis: AnalysisResult):
    latest_score = get_analysis_score(analysis)

    return CoachAthleteAnalysisItem(
        analysis_id=analysis.analysis_id,
        video_id=analysis.video_id,
        video_activity=analysis.video.activity if analysis.video else None,
        analysis_date=analysis.analysis_date,
        completed_at=analysis.completed_at,
        status=analysis.status,
        algorithm_version=analysis.algorithm_version,
        historical_score=analysis.historical_score,
        biomechanical_score=analysis.biomechanical_score,
        asymmetry_score=analysis.asymmetry_score,
        training_load_score=analysis.training_load_score,
        composite_risk_score=analysis.composite_risk_score,
        overall_risk_score=analysis.overall_risk_score,
        risk_category=normalize_risk_category_label(analysis.risk_category, latest_score),
        knee_valgus=analysis.knee_valgus,
        hip_stability=analysis.hip_stability,
        trunk_lean=analysis.trunk_lean,
        stride_length=analysis.stride_length,
        joint_alignment=analysis.joint_alignment,
        symmetry_score=analysis.symmetry_score,
        fatigue_score=analysis.fatigue_score,
        movement_quality=analysis.movement_quality,
        summary_metrics=analysis.summary_metrics,
        time_series_data=analysis.time_series_data,
        recommendations=analysis.recommendations,
        risk_assessment=analysis.summary_metrics.get("risk_assessment")
        if isinstance(analysis.summary_metrics, dict)
        else None,
        skeleton_video_url=analysis.skeleton_video_url,
        pdf_report_url=analysis.pdf_report_url,
        csv_report_url=None,
        pdf_report_available=get_report_path(analysis.video_id, "pdf") is not None,
        csv_report_available=False,
    )


def build_video_item(db: Session, video: Video):
    latest_analysis = (
        db.query(AnalysisResult)
        .filter(AnalysisResult.video_id == video.video_id)
        .order_by(
            AnalysisResult.completed_at.desc().nullslast(),
            AnalysisResult.analysis_date.desc(),
            AnalysisResult.created_at.desc(),
        )
        .first()
    )
    latest_score = get_analysis_score(latest_analysis)

    return CoachAthleteVideoItem(
        video_id=video.video_id,
        activity=video.activity,
        video_url=video.video_url,
        uploaded_at=video.uploaded_at,
        processing_status=video.processing_status,
        duration=video.duration,
        fps=video.fps,
        resolution=video.resolution,
        latest_analysis_id=latest_analysis.analysis_id if latest_analysis else None,
        latest_risk_score=latest_score,
        risk_category=normalize_risk_category_label(
            latest_analysis.risk_category if latest_analysis else None,
            latest_score,
        ),
        analysis_status=latest_analysis.status
        if latest_analysis
        else video.processing_status or "pending",
    )


def build_private_profile(athlete: Athlete, latest_analysis: AnalysisResult | None):
    latest_score = get_analysis_score(latest_analysis)

    return CoachPrivateAthleteProfile(
        athlete_id=athlete.athlete_id,
        user_id=athlete.user_id,
        name=athlete.user.name if athlete.user else "Athlete",
        email=athlete.user.email if athlete.user else "",
        sport=athlete.sport,
        position=athlete.position,
        age=athlete.age,
        height=athlete.height,
        weight=athlete.weight,
        training_load=athlete.training_load,
        flexibility=athlete.flexibility,
        strength=athlete.strength,
        balance=athlete.balance,
        endurance=athlete.endurance,
        latest_risk_score=latest_score,
        risk_category=normalize_risk_category_label(
            latest_analysis.risk_category if latest_analysis else None,
            latest_score,
        ),
    )


def build_coach_movement_comparison(analyses: list[AnalysisResult]):
    payload = build_movement_comparison_payload(analyses)
    initial = payload["initial_assessment"]
    latest = payload["latest_assessment"]
    return {
        "initial": build_analysis_item(initial) if initial else None,
        "latest": build_analysis_item(latest) if latest else None,
        "comparison": payload["comparison"],
        "comparison_status": payload["comparison_status"],
    }


def build_recent_activity(analyses: list[AnalysisResult], videos: list[Video]):
    events = []
    for analysis in analyses[:5]:
        events.append({
            "type": "analysis",
            "title": "Analysis completed" if analysis.status == "completed" else "Analysis updated",
            "activity": analysis.video.activity if analysis.video else None,
            "status": analysis.status,
            "risk_category": normalize_risk_category_label(
                analysis.risk_category,
                get_analysis_score(analysis),
            ),
            "created_at": analysis.completed_at or analysis.analysis_date or analysis.created_at,
        })
    for video in videos[:5]:
        events.append({
            "type": "video",
            "title": "Video uploaded",
            "activity": video.activity,
            "status": video.processing_status or "Not Available",
            "created_at": video.uploaded_at,
        })
    events.sort(key=lambda item: item["created_at"] or datetime.min, reverse=True)
    return events[:8]


def build_coach_task_response(task: CoachTask) -> CoachTaskResponse:
    return CoachTaskResponse(
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
        athlete_name=task.athlete.user.name if task.athlete and task.athlete.user else None,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


def validate_coach_task_payload(data):
    if data.priority and data.priority not in VALID_COACH_TASK_PRIORITIES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid task priority",
        )
    if data.status and data.status not in VALID_COACH_TASK_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid task status",
        )


def validate_coach_task_analysis_context(
    athlete_id: UUID,
    payload: dict,
    db: Session,
) -> dict:
    analysis_id = payload.get("analysis_id")
    video_id = payload.get("video_id")

    if analysis_id:
        analysis = (
            db.query(AnalysisResult)
            .filter(
                AnalysisResult.analysis_id == analysis_id,
                AnalysisResult.athlete_id == athlete_id,
            )
            .first()
        )
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis not found for this athlete",
            )
        if video_id and video_id != analysis.video_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Video does not match the selected analysis",
            )
        payload["video_id"] = analysis.video_id
        return payload

    if video_id:
        video = (
            db.query(Video)
            .filter(
                Video.video_id == video_id,
                Video.athlete_id == athlete_id,
            )
            .first()
        )
        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video not found for this athlete",
            )

    return payload


def get_owned_coach_task(
    task_id: UUID,
    coach_profile: CoachProfile,
    db: Session,
) -> CoachTask:
    task = (
        db.query(CoachTask)
        .options(
            joinedload(CoachTask.coach).joinedload(CoachProfile.user),
            joinedload(CoachTask.athlete).joinedload(Athlete.user),
        )
        .filter(
            CoachTask.task_id == task_id,
            CoachTask.coach_id == coach_profile.coach_id,
        )
        .first()
    )
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coach task not found",
        )

    get_active_coach_athlete_relationship(
        task.athlete_id,
        coach_profile,
        db,
        permission="performance_information",
    )
    return task


def build_attention_alerts(
    db: Session,
    athlete_items: list[CoachConnectedAthleteItem],
    coach_profile: CoachProfile | None = None,
):
    alerts = []

    if coach_profile:
        pending_incoming = (
            db.query(ProfessionalAthleteRelationship)
            .options(joinedload(ProfessionalAthleteRelationship.athlete).joinedload(Athlete.user))
            .filter(
                ProfessionalAthleteRelationship.professional_user_id == coach_profile.user_id,
                ProfessionalAthleteRelationship.professional_role == COACH_RELATIONSHIP_ROLE,
                ProfessionalAthleteRelationship.status == ProfessionalAthleteRelationshipStatus.PENDING.value,
                ProfessionalAthleteRelationship.requested_by != coach_profile.user_id,
            )
            .all()
        )
        for req in pending_incoming:
            ath_name = req.athlete.user.name if req.athlete and req.athlete.user else "Athlete"
            alerts.append(
                CoachDashboardAlert(
                    athlete_id=req.athlete_id,
                    athlete_name=ath_name,
                    type="PENDING_REQUEST",
                    title="Pending athlete request",
                    detail=f"{ath_name} requested to connect with you.",
                    severity="MODERATE",
                    created_at=req.created_at,
                )
            )

    for item in athlete_items:
        if item.risk_category in ("HIGH", "CRITICAL"):
            alerts.append(
                CoachDashboardAlert(
                    athlete_id=item.athlete_id,
                    athlete_name=item.name,
                    type="RISK",
                    title=f"{item.risk_category.title()} risk athlete",
                    detail="Latest completed analysis needs coach attention.",
                    severity=item.risk_category,
                    created_at=item.last_analysis_at,
                )
            )

        if item.video_count > 0 and item.analysis_count == 0:
            alerts.append(
                CoachDashboardAlert(
                    athlete_id=item.athlete_id,
                    athlete_name=item.name,
                    type="NO_ANALYSIS",
                    title="No recent analysis",
                    detail="Athlete has uploaded videos but no completed analysis yet.",
                    severity="MODERATE",
                    created_at=item.latest_activity_at,
                )
            )

        recent_analyses = (
            db.query(AnalysisResult)
            .filter(
                AnalysisResult.athlete_id == item.athlete_id,
                AnalysisResult.status == "completed",
            )
            .order_by(
                AnalysisResult.completed_at.desc().nullslast(),
                AnalysisResult.analysis_date.desc(),
                AnalysisResult.created_at.desc(),
            )
            .limit(2)
            .all()
        )
        if len(recent_analyses) == 2:
            latest_score = get_analysis_score(recent_analyses[0])
            previous_score = get_analysis_score(recent_analyses[1])
            if (
                latest_score is not None
                and previous_score is not None
                and latest_score > previous_score
            ):
                alerts.append(
                    CoachDashboardAlert(
                        athlete_id=item.athlete_id,
                        athlete_name=item.name,
                        type="RISK_INCREASED",
                        title="Risk increased",
                        detail=f"Latest score increased from {previous_score:.1f} to {latest_score:.1f}.",
                        severity=normalize_risk_category(latest_score),
                        created_at=recent_analyses[0].completed_at,
                    )
                )

    alerts.sort(key=lambda alert: alert.created_at or datetime.min, reverse=True)
    return alerts[:6]


@router.get(
    "/profile",
    response_model=CoachProfileResponse,
)
def get_my_coach_profile(
    coach_profile: CoachProfile = Depends(get_verified_coach_profile),
):
    return coach_profile


@router.put(
    "/profile",
    response_model=CoachProfileResponse,
)
def update_my_coach_profile(
    profile_data: CoachProfileUpdate,
    coach_profile: CoachProfile = Depends(get_verified_coach_profile),
    db: Session = Depends(get_db),
):
    update_data = profile_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(coach_profile, field, value)

    completed_fields = [
        "primary_sport",
        "other_sports",
        "years_of_experience",
        "coaching_specialization",
        "organization",
        "certifications",
        "professional_bio",
    ]
    completed_count = sum(
        1
        for field in completed_fields
        if getattr(coach_profile, field, None) not in (None, "")
    )
    coach_profile.profile_completion = round(
        (completed_count / len(completed_fields)) * 100,
        1,
    )

    db.commit()
    db.refresh(coach_profile)

    return coach_profile


@router.get("/dashboard", response_model=CoachDashboardResponse)
def get_coach_dashboard(
    coach_profile: CoachProfile = Depends(get_verified_coach_profile),
    db: Session = Depends(get_db),
):
    relationships = get_active_relationships_query(db, coach_profile).all()
    athlete_ids = [relationship.athlete_id for relationship in relationships]
    athlete_items = [
        build_connected_athlete_item(db, relationship)
        for relationship in relationships
        if relationship.athlete is not None
    ]

    video_count = 0
    analysis_count = 0
    if athlete_ids:
        video_count = db.query(Video).filter(Video.athlete_id.in_(athlete_ids)).count()
        analysis_count = (
            db.query(AnalysisResult)
            .filter(AnalysisResult.athlete_id.in_(athlete_ids))
            .count()
        )

    high_risk_count = sum(
        1
        for item in athlete_items
        if item.risk_category in ("HIGH", "CRITICAL")
    )
    athlete_items.sort(key=lambda item: item.latest_activity_at or datetime.min, reverse=True)

    # 1. Performance trends across active connected athletes
    trend_analyses = []
    if athlete_ids:
        trend_analyses = (
            db.query(AnalysisResult)
            .options(joinedload(AnalysisResult.athlete).joinedload(Athlete.user))
            .filter(
                AnalysisResult.athlete_id.in_(athlete_ids),
                AnalysisResult.status == "completed",
            )
            .order_by(
                AnalysisResult.completed_at.asc().nullslast(),
                AnalysisResult.analysis_date.asc().nullslast(),
                AnalysisResult.created_at.asc(),
            )
            .all()
        )

    performance_trends = []
    for a in trend_analyses:
        adate = a.completed_at or a.analysis_date or a.created_at
        mq = a.movement_quality
        eff = a.biomechanical_score
        if eff is None and a.summary_metrics and isinstance(a.summary_metrics, dict):
            eff = a.summary_metrics.get("biomechanical_efficiency_score") or a.summary_metrics.get("biomechanical_efficiency")
        if eff is None and a.risk_assessment and isinstance(a.risk_assessment, dict):
            eff = a.risk_assessment.get("biomechanical_efficiency_score")
        rscore = get_analysis_score(a)
        performance_trends.append({
            "date": adate.isoformat() if adate else None,
            "movement_quality": round(float(mq), 1) if mq is not None else None,
            "biomechanical_efficiency": round(float(eff), 1) if eff is not None else None,
            "risk_score": round(float(rscore), 1) if rscore is not None else None,
            "athlete_name": a.athlete.user.name if a.athlete and a.athlete.user else "Athlete",
            "analysis_id": str(a.analysis_id),
        })

    # 2. Recent completed analyses (top 5 so frontend can display 3 and knows if total > 3)
    recent_analyses = []
    total_completed = 0
    if athlete_ids:
        completed_analyses_query = (
            db.query(AnalysisResult)
            .options(
                joinedload(AnalysisResult.athlete).joinedload(Athlete.user),
                joinedload(AnalysisResult.video),
            )
            .filter(
                AnalysisResult.athlete_id.in_(athlete_ids),
                AnalysisResult.status == "completed",
            )
            .order_by(
                AnalysisResult.completed_at.desc().nullslast(),
                AnalysisResult.analysis_date.desc().nullslast(),
                AnalysisResult.created_at.desc(),
            )
        )
        total_completed = completed_analyses_query.count()
        for a in completed_analyses_query.limit(5).all():
            adate = a.completed_at or a.analysis_date or a.created_at
            rscore = get_analysis_score(a)
            risk_cat = normalize_risk_category_label(rscore)
            act = a.video_activity or (a.video.activity if a.video else None) or "Movement Analysis"
            recent_analyses.append({
                "analysis_id": str(a.analysis_id),
                "athlete_id": str(a.athlete_id),
                "athlete_name": a.athlete.user.name if a.athlete and a.athlete.user else "Athlete",
                "athlete_sport": a.athlete.sport if a.athlete else None,
                "activity": act,
                "date": adate.isoformat() if adate else None,
                "risk_score": round(float(rscore), 1) if rscore is not None else None,
                "risk_category": risk_cat,
                "movement_quality": round(float(a.movement_quality), 1) if a.movement_quality is not None else None,
                "video_id": str(a.video_id) if a.video_id else None,
            })

    # 3. Connection requests summary (Received & Sent)
    all_requests = (
        db.query(ProfessionalAthleteRelationship)
        .options(
            joinedload(ProfessionalAthleteRelationship.athlete).joinedload(Athlete.user),
        )
        .filter(
            ProfessionalAthleteRelationship.professional_user_id == coach_profile.user_id,
            ProfessionalAthleteRelationship.professional_role == COACH_RELATIONSHIP_ROLE,
        )
        .order_by(ProfessionalAthleteRelationship.created_at.desc())
        .all()
    )
    recent_requests_list = []
    for req in all_requests[:5]:
        direction = "SENT" if req.requested_by == coach_profile.user_id else "RECEIVED"
        ath_name = req.athlete.user.name if req.athlete and req.athlete.user else "Athlete"
        sport = req.athlete.sport if req.athlete else None
        recent_requests_list.append({
            "relationship_id": str(req.relationship_id),
            "athlete_id": str(req.athlete_id),
            "athlete_name": ath_name,
            "athlete_sport": sport,
            "direction": direction,
            "status": req.status,
            "date": req.created_at.isoformat() if req.created_at else None,
        })
    requests_summary = {
        "total_requests": len(all_requests),
        "recent_requests": recent_requests_list,
    }

    # 4. Optional tasks summary
    tasks_query = (
        db.query(CoachTask)
        .options(joinedload(CoachTask.athlete).joinedload(Athlete.user))
        .filter(CoachTask.coach_id == coach_profile.coach_id)
    )
    total_tasks = tasks_query.count()
    tasks_summary = None
    if total_tasks > 0:
        assigned = tasks_query.filter(CoachTask.status == CoachTaskStatus.ASSIGNED.value).count()
        in_progress = tasks_query.filter(CoachTask.status == CoachTaskStatus.IN_PROGRESS.value).count()
        completed = tasks_query.filter(CoachTask.status == CoachTaskStatus.COMPLETED.value).count()
        recent_tasks_db = tasks_query.order_by(CoachTask.created_at.desc()).limit(3).all()
        tasks_summary = {
            "total": total_tasks,
            "assigned": assigned,
            "in_progress": in_progress,
            "completed": completed,
            "recent_tasks": [
                {
                    "task_id": str(t.task_id),
                    "athlete_id": str(t.athlete_id),
                    "athlete_name": t.athlete.user.name if t.athlete and t.athlete.user else "Athlete",
                    "title": t.title,
                    "status": t.status,
                    "priority": t.priority,
                    "due_date": t.due_date.isoformat() if t.due_date else None,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                }
                for t in recent_tasks_db
            ],
        }

    return {
        "coach_id": coach_profile.coach_id,
        "verification_status": coach_profile.verification_status,
        "stats": {
            "total_athletes": len(athlete_items),
            "analyses": analysis_count,
            "videos": video_count,
            "high_risk": high_risk_count,
        },
        "attention": build_attention_alerts(db, athlete_items, coach_profile),
        "athletes": athlete_items[:5],
        "recent_analyses": recent_analyses,
        "total_recent_analyses": total_completed,
        "performance_trends": performance_trends,
        "requests_summary": requests_summary,
        "tasks_summary": tasks_summary,
    }


@router.get(
    "/athletes/discover",
    response_model=list[AthleteDiscoveryItem],
)
def discover_athletes(
    search: str | None = Query(default=None),
    sport: str | None = Query(default=None),
    risk_category: str | None = Query(default=None),
    availability: str | None = Query(default=None),
    connection_status: str | None = Query(default=None),
    sort: str = Query(default="name"),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    coach_profile: CoachProfile = Depends(get_verified_coach_profile),
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

    athletes = query.all()
    items = []

    for athlete in athletes:
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
                ProfessionalAthleteRelationship.professional_user_id == coach_profile.user_id,
                ProfessionalAthleteRelationship.athlete_id == athlete.athlete_id,
                ProfessionalAthleteRelationship.professional_role == COACH_RELATIONSHIP_ROLE,
            )
            .order_by(ProfessionalAthleteRelationship.created_at.desc())
            .first()
        )
        status_value = relationship.status if relationship else "NONE"
        latest_analysis = get_latest_completed_analysis(db, athlete.athlete_id)
        item = build_discovery_item(athlete, latest_analysis, status_value)

        if connection_status and item.connection_status != connection_status.upper():
            continue

        if availability and item.availability != availability.upper():
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
    response_model=CoachRelationshipResponse,
    status_code=status.HTTP_201_CREATED,
)
def send_connection_request(
    athlete_id: UUID,
    coach_profile: CoachProfile = Depends(get_verified_coach_profile),
    current_user: User = Depends(require_roles(UserRole.COACH)),
    db: Session = Depends(get_db),
):
    athlete = db.query(Athlete).filter(Athlete.athlete_id == athlete_id).first()
    if not athlete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Athlete not found"
        )

    existing = (
        db.query(ProfessionalAthleteRelationship)
        .filter(
            ProfessionalAthleteRelationship.professional_user_id == coach_profile.user_id,
            ProfessionalAthleteRelationship.athlete_id == athlete_id,
            ProfessionalAthleteRelationship.professional_role == COACH_RELATIONSHIP_ROLE,
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
            detail="A pending or active relationship already exists"
        )

    relationship = ProfessionalAthleteRelationship(
        professional_user_id=coach_profile.user_id,
        athlete_id=athlete_id,
        professional_role=COACH_RELATIONSHIP_ROLE,
        status=ProfessionalAthleteRelationshipStatus.PENDING.value,
        requested_by=current_user.user_id,
    )
    db.add(relationship)
    db.flush()
    create_notification(
        db,
        recipient_user_id=athlete.user_id,
        notification_type=NotificationType.CONNECTION_REQUEST,
        title="Coach connection request",
        message=f"{current_user.name} requested access to your athlete profile.",
        actor_user_id=current_user.user_id,
        entity_type="professional_athlete_relationship",
        entity_id=relationship.relationship_id,
        action_url="/dashboard",
    )
    db.commit()
    db.refresh(relationship)

    return relationship


@router.get(
    "/athletes",
    response_model=list[CoachConnectedAthleteItem],
)
def get_connected_athletes(
    search: str | None = None,
    risk_category: str | None = None,
    sort: str = "recent",
    coach_profile: CoachProfile = Depends(get_verified_coach_profile),
    db: Session = Depends(get_db),
):
    relationships = get_active_relationships_query(db, coach_profile).all()
    items = [
        build_connected_athlete_item(db, relationship)
        for relationship in relationships
        if relationship.athlete is not None
    ]

    if search:
        search_text = search.lower()
        items = [item for item in items if search_text in item.name.lower()]

    if risk_category and risk_category.upper() != "ALL":
        items = [
            item
            for item in items
            if item.risk_category == risk_category.upper()
        ]

    if sort == "risk_desc":
        items.sort(key=lambda item: item.latest_risk_score if item.latest_risk_score is not None else -1, reverse=True)
    elif sort == "risk_asc":
        items.sort(key=lambda item: item.latest_risk_score if item.latest_risk_score is not None else 101)
    elif sort == "name":
        items.sort(key=lambda item: item.name.lower())
    else:
        items.sort(key=lambda item: item.latest_activity_at or datetime.min, reverse=True)

    return items


@router.get(
    "/athletes/{athlete_id}",
    response_model=CoachAthleteDetailResponse,
)
def get_connected_athlete_detail(
    athlete_id: UUID,
    coach_profile: CoachProfile = Depends(get_verified_coach_profile),
    db: Session = Depends(get_db),
):
    get_active_coach_athlete_relationship(
        athlete_id, coach_profile, db, permission="athlete_profile"
    )
    for permission in (
        "risk_results",
        "videos",
        "analyses",
        "performance_information",
    ):
        require_role_permission(COACH_RELATIONSHIP_ROLE, permission)

    athlete = (
        db.query(Athlete)
        .options(joinedload(Athlete.user))
        .filter(Athlete.athlete_id == athlete_id)
        .first()
    )
    if not athlete:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Active coach-athlete relationship required"
        )

    latest_analysis = get_latest_completed_analysis(db, athlete_id)
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
    videos = (
        db.query(Video)
        .filter(Video.athlete_id == athlete_id)
        .order_by(Video.uploaded_at.desc())
        .all()
    )
    latest_score = get_analysis_score(latest_analysis)
    previous_completed = next(
        (
            analysis
            for analysis in analyses
            if latest_analysis and analysis.analysis_id != latest_analysis.analysis_id and analysis.status == "completed"
        ),
        None,
    )
    previous_score = get_analysis_score(previous_completed)
    if latest_score is None or previous_score is None:
        risk_trend = "No Previous Assessment" if latest_score is not None else "No Analysis"
    elif latest_score > previous_score:
        risk_trend = "Increasing"
    elif latest_score < previous_score:
        risk_trend = "Decreasing"
    else:
        risk_trend = "Stable"

    return CoachAthleteDetailResponse(
        profile=build_private_profile(athlete, latest_analysis),
        performance_overview={
            "biomechanical": latest_analysis.biomechanical_score if latest_analysis else None,
            "historical": latest_analysis.historical_score if latest_analysis else None,
            "movement_asymmetry": latest_analysis.asymmetry_score if latest_analysis else None,
            "training_load": latest_analysis.training_load_score if latest_analysis else None,
        },
        risk_overview={
            "current_risk": latest_score,
            "risk_category": normalize_risk_category_label(
                latest_analysis.risk_category if latest_analysis else None,
                latest_score,
            ),
            "previous_risk": previous_score,
            "risk_trend": risk_trend,
        },
        movement_comparison=build_coach_movement_comparison(
            [analysis for analysis in analyses if analysis.status == "completed"]
        ),
        recent_activity=build_recent_activity(analyses, videos),
        latest_analysis=build_analysis_item(latest_analysis) if latest_analysis else None,
        videos=[build_video_item(db, video) for video in videos],
        analyses=[build_analysis_item(analysis) for analysis in analyses],
    )


@router.get(
    "/athletes/{athlete_id}/physiotherapists",
    response_model=list[PhysiotherapistRelationshipResponse],
)
def get_athlete_physiotherapist_assignments(
    athlete_id: UUID,
    coach_profile: CoachProfile = Depends(get_verified_coach_profile),
    db: Session = Depends(get_db),
):
    get_active_coach_athlete_relationship(
        athlete_id, coach_profile, db, permission="athlete_profile"
    )

    return (
        db.query(ProfessionalAthleteRelationship)
        .options(
            joinedload(ProfessionalAthleteRelationship.professional_user).joinedload(
                User.professional_profiles
            ),
            joinedload(ProfessionalAthleteRelationship.athlete).joinedload(Athlete.user),
            joinedload(ProfessionalAthleteRelationship.requester),
        )
        .filter(
            ProfessionalAthleteRelationship.athlete_id == athlete_id,
            ProfessionalAthleteRelationship.professional_role == PHYSIO_RELATIONSHIP_ROLE,
            ProfessionalAthleteRelationship.status.in_([
                ProfessionalAthleteRelationshipStatus.PENDING.value,
                ProfessionalAthleteRelationshipStatus.ACTIVE.value,
            ]),
        )
        .order_by(ProfessionalAthleteRelationship.created_at.desc())
        .all()
    )


@router.get(
    "/athletes/{athlete_id}/physiotherapists/available",
    response_model=list[CoachAssignablePhysiotherapist],
)
def list_assignable_physiotherapists(
    athlete_id: UUID,
    search: str | None = None,
    coach_profile: CoachProfile = Depends(get_verified_coach_profile),
    db: Session = Depends(get_db),
):
    get_active_coach_athlete_relationship(
        athlete_id, coach_profile, db, permission="athlete_profile"
    )

    query = (
        db.query(ProfessionalProfile)
        .join(User, User.user_id == ProfessionalProfile.user_id)
        .filter(
            User.role == UserRole.PHYSIOTHERAPIST,
            ProfessionalProfile.professional_role == PHYSIO_RELATIONSHIP_ROLE,
            ProfessionalProfile.verification_status == ProfessionalVerificationStatus.VERIFIED.value,
        )
    )

    if search:
        search_value = f"%{search.strip()}%"
        query = query.filter(
            (User.name.ilike(search_value))
            | (ProfessionalProfile.specialization.ilike(search_value))
            | (ProfessionalProfile.primary_sport.ilike(search_value))
            | (ProfessionalProfile.organization.ilike(search_value))
        )

    profiles = query.order_by(User.name.asc()).limit(25).all()
    existing_relationships = (
        db.query(ProfessionalAthleteRelationship)
        .filter(
            ProfessionalAthleteRelationship.athlete_id == athlete_id,
            ProfessionalAthleteRelationship.professional_role == PHYSIO_RELATIONSHIP_ROLE,
            ProfessionalAthleteRelationship.professional_user_id.in_([
                profile.user_id for profile in profiles
            ] or [coach_profile.user_id]),
            ProfessionalAthleteRelationship.status.in_([
                ProfessionalAthleteRelationshipStatus.PENDING.value,
                ProfessionalAthleteRelationshipStatus.ACTIVE.value,
            ]),
        )
        .all()
    )
    status_by_user = {
        relationship.professional_user_id: relationship.status
        for relationship in existing_relationships
    }

    return [
        CoachAssignablePhysiotherapist(
            user_id=profile.user_id,
            name=profile.user.name if profile.user else "Physiotherapist",
            professional_role=profile.professional_role,
            verification_status=profile.verification_status,
            primary_sport=profile.primary_sport,
            years_of_experience=profile.years_of_experience,
            specialization=profile.specialization,
            organization=profile.organization,
            professional_bio=profile.professional_bio,
            relationship_status=status_by_user.get(profile.user_id, "NONE"),
        )
        for profile in profiles
    ]


@router.post(
    "/athletes/{athlete_id}/physiotherapists/{physiotherapist_user_id}/assign",
    response_model=PhysiotherapistRelationshipResponse,
    status_code=status.HTTP_201_CREATED,
)
def assign_physiotherapist_to_athlete(
    athlete_id: UUID,
    physiotherapist_user_id: UUID,
    coach_profile: CoachProfile = Depends(get_verified_coach_profile),
    db: Session = Depends(get_db),
):
    get_active_coach_athlete_relationship(
        athlete_id, coach_profile, db, permission="athlete_profile"
    )

    physiotherapist = (
        db.query(User)
        .filter(
            User.user_id == physiotherapist_user_id,
            User.role == UserRole.PHYSIOTHERAPIST,
        )
        .first()
    )
    if not physiotherapist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Verified Physiotherapist not found",
        )

    physiotherapist_profile = require_verified_professional_profile(
        db=db,
        current_user=physiotherapist,
        professional_role=PHYSIO_RELATIONSHIP_ROLE,
    )
    if physiotherapist_profile.verification_status != ProfessionalVerificationStatus.VERIFIED.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Physiotherapist is not verified",
        )

    existing = (
        db.query(ProfessionalAthleteRelationship)
        .filter(
            ProfessionalAthleteRelationship.professional_user_id == physiotherapist_user_id,
            ProfessionalAthleteRelationship.athlete_id == athlete_id,
            ProfessionalAthleteRelationship.professional_role == PHYSIO_RELATIONSHIP_ROLE,
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
            detail="A pending or active physiotherapist relationship already exists",
        )

    relationship = ProfessionalAthleteRelationship(
        professional_user_id=physiotherapist_user_id,
        athlete_id=athlete_id,
        professional_role=PHYSIO_RELATIONSHIP_ROLE,
        status=ProfessionalAthleteRelationshipStatus.PENDING.value,
        requested_by=coach_profile.user_id,
    )
    db.add(relationship)
    db.flush()
    create_notification(
        db,
        recipient_user_id=physiotherapist_user_id,
        notification_type=NotificationType.CONNECTION_REQUEST,
        title="Athlete assignment request",
        message="A Coach requested your physiotherapy support for an athlete.",
        actor_user_id=coach_profile.user_id,
        entity_type="professional_athlete_relationship",
        entity_id=relationship.relationship_id,
        action_url="/physiotherapist/requests",
    )
    db.commit()
    db.refresh(relationship)

    return relationship


@router.get(
    "/athletes/{athlete_id}/tasks",
    response_model=list[CoachTaskResponse],
)
def list_athlete_tasks(
    athlete_id: UUID,
    coach_profile: CoachProfile = Depends(get_verified_coach_profile),
    db: Session = Depends(get_db),
):
    get_active_coach_athlete_relationship(
        athlete_id, coach_profile, db, permission="performance_information"
    )

    tasks = (
        db.query(CoachTask)
        .options(
            joinedload(CoachTask.coach).joinedload(CoachProfile.user),
            joinedload(CoachTask.athlete).joinedload(Athlete.user),
        )
        .filter(
            CoachTask.coach_id == coach_profile.coach_id,
            CoachTask.athlete_id == athlete_id,
        )
        .order_by(CoachTask.created_at.desc())
        .all()
    )
    return [build_coach_task_response(task) for task in tasks]


@router.post(
    "/athletes/{athlete_id}/tasks",
    response_model=CoachTaskResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_athlete_task(
    athlete_id: UUID,
    task_data: CoachTaskCreate,
    coach_profile: CoachProfile = Depends(get_verified_coach_profile),
    db: Session = Depends(get_db),
):
    get_active_coach_athlete_relationship(
        athlete_id, coach_profile, db, permission="performance_information"
    )
    validate_coach_task_payload(task_data)
    payload = validate_coach_task_analysis_context(
        athlete_id,
        task_data.model_dump(),
        db,
    )

    task = CoachTask(
        coach_id=coach_profile.coach_id,
        athlete_id=athlete_id,
        **payload,
    )
    if task.status == CoachTaskStatus.COMPLETED.value:
        task.completed_at = datetime.now(timezone.utc)

    db.add(task)
    db.flush()
    athlete = db.query(Athlete).options(joinedload(Athlete.user)).filter(Athlete.athlete_id == athlete_id).first()
    if athlete and athlete.user_id:
        create_notification(
            db,
            recipient_user_id=athlete.user_id,
            notification_type=NotificationType.COACH_RECOMMENDATION,
            title="New coach task",
            message=f"{coach_profile.user.name if coach_profile.user else 'Your Coach'} assigned: {task.title}.",
            actor_user_id=coach_profile.user_id,
            entity_type="coach_task",
            entity_id=task.task_id,
            action_url="/my-work",
        )
    db.commit()
    db.refresh(task)
    return build_coach_task_response(task)


@router.put(
    "/tasks/{task_id}",
    response_model=CoachTaskResponse,
)
def update_athlete_task(
    task_id: UUID,
    task_data: CoachTaskUpdate,
    coach_profile: CoachProfile = Depends(get_verified_coach_profile),
    db: Session = Depends(get_db),
):
    task = get_owned_coach_task(task_id, coach_profile, db)
    update_data = task_data.model_dump(exclude_unset=True)
    if "priority" in update_data and update_data["priority"] not in VALID_COACH_TASK_PRIORITIES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid task priority")
    if "status" in update_data and update_data["status"] not in VALID_COACH_TASK_STATUSES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid task status")
    if "analysis_id" in update_data or "video_id" in update_data:
        context_payload = validate_coach_task_analysis_context(
            task.athlete_id,
            {
                "analysis_id": update_data.get("analysis_id"),
                "video_id": update_data.get("video_id"),
            },
            db,
        )
        update_data["analysis_id"] = context_payload.get("analysis_id")
        update_data["video_id"] = context_payload.get("video_id")

    for field, value in update_data.items():
        setattr(task, field, value)
    if "status" in update_data:
        task.completed_at = (
            datetime.now(timezone.utc)
            if update_data["status"] == CoachTaskStatus.COMPLETED.value
            else None
        )

    if update_data:
        athlete = db.query(Athlete).filter(Athlete.athlete_id == task.athlete_id).first()
        if athlete and athlete.user_id:
            create_notification(
                db,
                recipient_user_id=athlete.user_id,
                notification_type=NotificationType.COACH_TASK_UPDATED,
                title="Coach task updated",
                message=f"Your Coach updated: {task.title}.",
                actor_user_id=coach_profile.user_id,
                entity_type="coach_task_update",
                entity_id=task.task_id,
                action_url="/my-work",
                dedupe=False,
            )

    db.commit()
    db.refresh(task)
    return build_coach_task_response(task)


@router.post(
    "/tasks/{task_id}/cancel",
    response_model=CoachTaskResponse,
)
def cancel_athlete_task(
    task_id: UUID,
    coach_profile: CoachProfile = Depends(get_verified_coach_profile),
    db: Session = Depends(get_db),
):
    task = get_owned_coach_task(task_id, coach_profile, db)
    task.status = CoachTaskStatus.CANCELLED.value
    task.completed_at = None
    db.commit()
    db.refresh(task)
    return build_coach_task_response(task)


@router.get(
    "/athletes/{athlete_id}/analyses/{analysis_id}",
    response_model=CoachAthleteAnalysisItem,
)
def get_connected_athlete_analysis(
    athlete_id: UUID,
    analysis_id: UUID,
    coach_profile: CoachProfile = Depends(get_verified_coach_profile),
    db: Session = Depends(get_db),
):
    get_active_coach_athlete_relationship(
        athlete_id, coach_profile, db, permission="analyses"
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )

    return build_analysis_item(analysis)


@router.get("/athletes/{athlete_id}/videos/{video_id}/pdf")
def download_connected_athlete_pdf(
    athlete_id: UUID,
    video_id: UUID,
    coach_profile: CoachProfile = Depends(get_verified_coach_profile),
    db: Session = Depends(get_db),
):
    get_active_coach_athlete_relationship(
        athlete_id, coach_profile, db, permission="reports"
    )
    video = (
        db.query(Video)
        .filter(Video.video_id == video_id, Video.athlete_id == athlete_id)
        .first()
    )
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )

    pdf_path = get_report_path(video_id, "pdf")
    if not pdf_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF report file not found."
        )

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=f"movement_analysis_report_{video_id}.pdf",
    )


@router.get(
    "/requests",
    response_model=list[CoachRelationshipResponse],
)
def get_my_sent_connection_requests(
    coach_profile: CoachProfile = Depends(get_verified_coach_profile),
    db: Session = Depends(get_db),
):
    return (
        db.query(ProfessionalAthleteRelationship)
        .options(
            joinedload(ProfessionalAthleteRelationship.athlete).joinedload(Athlete.user),
            joinedload(ProfessionalAthleteRelationship.professional_user).joinedload(
                User.professional_profiles
            ),
        )
        .filter(
            ProfessionalAthleteRelationship.professional_user_id == coach_profile.user_id,
            ProfessionalAthleteRelationship.professional_role == COACH_RELATIONSHIP_ROLE,
        )
        .order_by(ProfessionalAthleteRelationship.created_at.desc())
        .all()
    )


@router.post(
    "/requests/{relationship_id}/accept",
    response_model=CoachRelationshipResponse,
)
def accept_coach_incoming_request(
    relationship_id: UUID,
    coach_profile: CoachProfile = Depends(get_verified_coach_profile),
    db: Session = Depends(get_db),
):
    relationship = (
        db.query(ProfessionalAthleteRelationship)
        .options(
            joinedload(ProfessionalAthleteRelationship.athlete).joinedload(Athlete.user),
            joinedload(ProfessionalAthleteRelationship.professional_user).joinedload(
                User.professional_profiles
            ),
        )
        .filter(
            ProfessionalAthleteRelationship.relationship_id == relationship_id,
            ProfessionalAthleteRelationship.professional_user_id == coach_profile.user_id,
            ProfessionalAthleteRelationship.professional_role == COACH_RELATIONSHIP_ROLE,
        )
        .first()
    )
    if not relationship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found",
        )
    if relationship.status != ProfessionalAthleteRelationshipStatus.PENDING.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending requests can be accepted",
        )
    if relationship.requested_by == coach_profile.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Athlete approval is required for requests you initiated",
        )

    now = datetime.now(timezone.utc)
    relationship.status = ProfessionalAthleteRelationshipStatus.ACTIVE.value
    relationship.responded_at = now
    relationship.accepted_at = now

    athlete_user_id = relationship.athlete.user_id if relationship.athlete else None
    if athlete_user_id:
        create_notification(
            db,
            recipient_user_id=athlete_user_id,
            notification_type=NotificationType.CONNECTION_ACCEPTED,
            title="Coach accepted connection",
            message=f"{coach_profile.user.name if coach_profile.user else 'Your Coach'} accepted your connection request.",
            actor_user_id=coach_profile.user_id,
            entity_type="professional_athlete_relationship",
            entity_id=relationship.relationship_id,
            action_url="/dashboard",
        )

    db.commit()
    db.refresh(relationship)
    return relationship


@router.post(
    "/requests/{relationship_id}/reject",
    response_model=CoachRelationshipResponse,
)
def reject_coach_incoming_request(
    relationship_id: UUID,
    coach_profile: CoachProfile = Depends(get_verified_coach_profile),
    db: Session = Depends(get_db),
):
    relationship = (
        db.query(ProfessionalAthleteRelationship)
        .options(
            joinedload(ProfessionalAthleteRelationship.athlete).joinedload(Athlete.user),
            joinedload(ProfessionalAthleteRelationship.professional_user).joinedload(
                User.professional_profiles
            ),
        )
        .filter(
            ProfessionalAthleteRelationship.relationship_id == relationship_id,
            ProfessionalAthleteRelationship.professional_user_id == coach_profile.user_id,
            ProfessionalAthleteRelationship.professional_role == COACH_RELATIONSHIP_ROLE,
        )
        .first()
    )
    if not relationship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found",
        )
    if relationship.status != ProfessionalAthleteRelationshipStatus.PENDING.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending requests can be rejected",
        )

    now = datetime.now(timezone.utc)
    relationship.status = ProfessionalAthleteRelationshipStatus.REJECTED.value
    relationship.responded_at = now
    relationship.accepted_at = None

    db.commit()
    db.refresh(relationship)
    return relationship


@router.get(
    "/athletes/{athlete_id}/profile",
    response_model=CoachPrivateAthleteProfile,
)
def get_connected_athlete_profile(
    athlete_id: UUID,
    coach_profile: CoachProfile = Depends(get_verified_coach_profile),
    db: Session = Depends(get_db),
):
    get_active_coach_athlete_relationship(
        athlete_id, coach_profile, db, permission="athlete_profile"
    )

    athlete = (
        db.query(Athlete)
        .options(joinedload(Athlete.user))
        .filter(Athlete.athlete_id == athlete_id)
        .first()
    )

    if not athlete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Athlete not found"
        )

    latest_analysis = get_latest_completed_analysis(db, athlete.athlete_id)
    return build_private_profile(athlete, latest_analysis)
