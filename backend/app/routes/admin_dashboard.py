from collections import Counter, defaultdict
from datetime import date, datetime, time, timedelta, timezone
import importlib.util
import os

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, text
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.dependencies.auth import require_roles
from app.models.analysis_result import AnalysisResult
from app.models.athlete import Athlete
from app.models.professional_athlete_relationship import (
    ProfessionalAthleteRelationship,
    ProfessionalAthleteRelationshipStatus,
)
from app.models.professional_profile import (
    ProfessionalProfile,
    ProfessionalProfileRole,
    ProfessionalVerificationStatus,
)
from app.models.professional_role_request import (
    ProfessionalRoleRequest,
    ProfessionalRoleRequestStatus,
)
from app.models.user import User, UserRole
from app.models.video import Video
from app.services.professional_analysis import (
    get_analysis_score,
    normalize_risk_category_label,
)


router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])

PROFESSIONAL_ROLES = {
    ProfessionalProfileRole.COACH.value,
    ProfessionalProfileRole.PHYSIOTHERAPIST.value,
    ProfessionalProfileRole.SPORTS_SCIENTIST.value,
}
RISK_BANDS = ["LOW", "MODERATE", "HIGH", "CRITICAL"]
USER_ROLE_TO_PROFESSIONAL_ROLE = {
    UserRole.COACH: ProfessionalProfileRole.COACH.value,
    UserRole.PHYSIOTHERAPIST: ProfessionalProfileRole.PHYSIOTHERAPIST.value,
    UserRole.SPORTS_SCIENTIST: ProfessionalProfileRole.SPORTS_SCIENTIST.value,
}


def _utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _completed_analyses_query(db: Session):
    return (
        db.query(AnalysisResult)
        .options(joinedload(AnalysisResult.athlete))
        .filter(func.lower(AnalysisResult.status) == "completed")
    )


def _event_date(analysis: AnalysisResult):
    return analysis.completed_at or analysis.analysis_date or analysis.created_at


def _serialize_date(value):
    if not value:
        return None
    return value.isoformat()


def _activity_item(title, detail, activity_type, occurred_at):
    return {
        "title": title,
        "detail": detail,
        "type": activity_type,
        "occurred_at": _serialize_date(occurred_at),
    }


def _range_bounds(range_days: int, date_from: date | None, date_to: date | None):
    if date_from or date_to:
        start_date = date_from or (_utc_now().date() - timedelta(days=range_days))
        end_date = date_to or _utc_now().date()
        return (
            datetime.combine(start_date, time.min),
            datetime.combine(end_date, time.max),
        )

    return (_utc_now() - timedelta(days=range_days), _utc_now())


def _date_key(value):
    return value.date().isoformat() if value else None


def _role_value(role):
    return role.value if hasattr(role, "value") else str(role)


def _professional_role_for_user_role(role):
    return USER_ROLE_TO_PROFESSIONAL_ROLE.get(role)


def _health_status(status, detail, last_checked_at):
    return {
        "status": status,
        "detail": detail,
        "last_checked_at": _serialize_date(last_checked_at),
    }


def _normalized_processing_status(value):
    normalized = str(value or "pending").strip().lower()
    if normalized in {"queued", "uploaded", "pending", "not started"}:
        return "QUEUED"
    if normalized in {"processing", "frames_extracted", "analyzing"}:
        return "PROCESSING"
    if normalized in {"completed", "analyzed", "complete"}:
        return "COMPLETED"
    if normalized in {"failed", "error", "processing_failed"}:
        return "FAILED"
    return normalized.upper()


def _analysis_time(analysis: AnalysisResult):
    return analysis.completed_at or analysis.analysis_date or analysis.created_at


def _required_storage_dirs():
    return [
        "uploads",
        os.path.join("uploads", "videos"),
        os.path.join("uploads", "frames"),
        os.path.join("uploads", "analysis"),
        os.path.join("uploads", "analysis", "skeleton"),
        os.path.join("uploads", "analysis", "reports"),
        os.path.join("uploads", "professional_documents"),
    ]


@router.get("/dashboard")
def get_admin_dashboard(
    range_days: int = Query(default=30, ge=7, le=365),
    admin_user: User = Depends(require_roles(UserRole.ADMINISTRATOR)),
    db: Session = Depends(get_db),
):
    del admin_user

    completed_analyses = _completed_analyses_query(db).all()
    since = _utc_now() - timedelta(days=range_days)
    range_analyses = [
        analysis
        for analysis in completed_analyses
        if _event_date(analysis) and _event_date(analysis) >= since
    ]

    user_distribution_rows = (
        db.query(User.role, func.count(User.user_id))
        .group_by(User.role)
        .all()
    )
    user_counts = {str(role.value if hasattr(role, "value") else role): count for role, count in user_distribution_rows}

    athletes_count = user_counts.get(UserRole.ATHLETE.value, 0)
    active_professional_roles = (
        db.query(func.count(ProfessionalProfile.professional_profile_id))
        .filter(
            ProfessionalProfile.professional_role.in_(PROFESSIONAL_ROLES),
            ProfessionalProfile.verification_status == ProfessionalVerificationStatus.VERIFIED.value,
        )
        .scalar()
        or 0
    )
    pending_requests = (
        db.query(func.count(ProfessionalRoleRequest.request_id))
        .filter(ProfessionalRoleRequest.status == ProfessionalRoleRequestStatus.PENDING.value)
        .scalar()
        or 0
    )
    active_connections = (
        db.query(func.count(ProfessionalAthleteRelationship.relationship_id))
        .filter(ProfessionalAthleteRelationship.status == ProfessionalAthleteRelationshipStatus.ACTIVE.value)
        .scalar()
        or 0
    )

    risk_counts = Counter({band: 0 for band in RISK_BANDS})
    sport_counts = Counter()
    activity_counts = Counter()

    for analysis in completed_analyses:
        score = get_analysis_score(analysis)
        risk_counts[normalize_risk_category_label(analysis.risk_category, score)] += 1
        if analysis.athlete and analysis.athlete.sport:
            sport_counts[analysis.athlete.sport] += 1

    for analysis in range_analyses:
        date_value = _event_date(analysis)
        if date_value:
            activity_counts[date_value.date().isoformat()] += 1

    recent_activity = []

    recent_users = (
        db.query(User)
        .filter(User.created_at.isnot(None))
        .order_by(User.created_at.desc())
        .limit(8)
        .all()
    )
    for user in recent_users:
        recent_activity.append(
            _activity_item(
                "User registered",
                f"{user.name} joined as {user.role.value if hasattr(user.role, 'value') else user.role}",
                "USER_REGISTERED",
                user.created_at,
            )
        )

    recent_requests = (
        db.query(ProfessionalRoleRequest)
        .options(joinedload(ProfessionalRoleRequest.user))
        .order_by(ProfessionalRoleRequest.updated_at.desc())
        .limit(8)
        .all()
    )
    for request in recent_requests:
        if request.status == ProfessionalRoleRequestStatus.APPROVED.value and request.reviewed_at:
            recent_activity.append(
                _activity_item(
                    "Professional approved",
                    f"{request.applicant_name or 'Applicant'} approved for {request.requested_role.replace('_', ' ')}",
                    "PROFESSIONAL_APPROVED",
                    request.reviewed_at,
                )
            )
        elif request.status == ProfessionalRoleRequestStatus.REJECTED.value and request.reviewed_at:
            recent_activity.append(
                _activity_item(
                    "Professional rejected",
                    f"{request.applicant_name or 'Applicant'} rejected for {request.requested_role.replace('_', ' ')}",
                    "PROFESSIONAL_REJECTED",
                    request.reviewed_at,
                )
            )
        elif request.submitted_at:
            recent_activity.append(
                _activity_item(
                    "Professional request submitted",
                    f"{request.applicant_name or 'Applicant'} requested {request.requested_role.replace('_', ' ')} access",
                    "PROFESSIONAL_REQUESTED",
                    request.submitted_at,
                )
            )

    recent_relationships = (
        db.query(ProfessionalAthleteRelationship)
        .options(
            joinedload(ProfessionalAthleteRelationship.professional_user),
            joinedload(ProfessionalAthleteRelationship.athlete).joinedload(Athlete.user),
        )
        .order_by(ProfessionalAthleteRelationship.created_at.desc())
        .limit(8)
        .all()
    )
    for relationship in recent_relationships:
        recent_activity.append(
            _activity_item(
                "Connection created",
                f"{relationship.professional_name or 'Professional'} requested {relationship.athlete_name or 'athlete'} access",
                "CONNECTION_CREATED",
                relationship.created_at,
            )
        )

    recent_analyses = sorted(
        [analysis for analysis in completed_analyses if _event_date(analysis)],
        key=lambda analysis: _event_date(analysis),
        reverse=True,
    )[:8]
    for analysis in recent_analyses:
        athlete_name = analysis.athlete.user.name if analysis.athlete and analysis.athlete.user else "Athlete"
        recent_activity.append(
            _activity_item(
                "Analysis completed",
                f"{athlete_name} completed a movement analysis",
                "ANALYSIS_COMPLETED",
                _event_date(analysis),
            )
        )

    recent_activity = sorted(
        [item for item in recent_activity if item["occurred_at"]],
        key=lambda item: item["occurred_at"],
        reverse=True,
    )[:12]

    return {
        "summary": {
            "total_users": db.query(func.count(User.user_id)).scalar() or 0,
            "athletes": athletes_count,
            "active_professionals": active_professional_roles,
            "pending_professional_requests": pending_requests,
            "active_connections": active_connections,
            "completed_analyses": len(completed_analyses),
        },
        "user_distribution": [
            {"label": role.value, "count": user_counts.get(role.value, 0)}
            for role in UserRole
        ],
        "analysis_activity": [
            {"date": date_key, "completed_analyses": activity_counts[date_key]}
            for date_key in sorted(activity_counts)
        ],
        "risk_distribution": [
            {"label": band.title(), "count": risk_counts[band]}
            for band in RISK_BANDS
        ],
        "analyses_by_sport": [
            {"sport": sport, "count": count}
            for sport, count in sport_counts.most_common()
        ],
        "recent_activity": recent_activity,
        "range_days": range_days,
    }


@router.get("/analytics")
def get_admin_platform_analytics(
    range_days: int = Query(default=30, ge=7, le=365),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    sport: str | None = Query(default=None, max_length=100),
    user_role: UserRole | None = Query(default=None),
    admin_user: User = Depends(require_roles(UserRole.ADMINISTRATOR)),
    db: Session = Depends(get_db),
):
    del admin_user
    start_at, end_at = _range_bounds(range_days, date_from, date_to)

    user_query = db.query(User)
    if user_role:
        user_query = user_query.filter(User.role == user_role)
    users = user_query.all()
    new_users = [
        user for user in users
        if user.created_at and start_at <= user.created_at <= end_at
    ]

    video_query = (
        db.query(Video)
        .join(Athlete, Video.athlete_id == Athlete.athlete_id)
        .join(User, Athlete.user_id == User.user_id)
        .options(joinedload(Video.athlete).joinedload(Athlete.user))
    )
    if sport:
        video_query = video_query.filter(Athlete.sport.ilike(f"%{sport}%"))
    if user_role:
        video_query = video_query.filter(User.role == user_role)
    videos = [
        video for video in video_query.all()
        if video.uploaded_at and start_at <= video.uploaded_at <= end_at
    ]

    analysis_query = (
        db.query(AnalysisResult)
        .join(Athlete, AnalysisResult.athlete_id == Athlete.athlete_id)
        .join(User, Athlete.user_id == User.user_id)
        .options(joinedload(AnalysisResult.athlete).joinedload(Athlete.user))
        .filter(func.lower(AnalysisResult.status) == "completed")
    )
    if sport:
        analysis_query = analysis_query.filter(Athlete.sport.ilike(f"%{sport}%"))
    if user_role:
        analysis_query = analysis_query.filter(User.role == user_role)
    analyses = [
        analysis for analysis in analysis_query.all()
        if _event_date(analysis) and start_at <= _event_date(analysis) <= end_at
    ]

    professional_profile_query = db.query(ProfessionalProfile).filter(
        ProfessionalProfile.verification_status == ProfessionalVerificationStatus.VERIFIED.value,
        ProfessionalProfile.professional_role.in_(PROFESSIONAL_ROLES),
    )
    if sport:
        professional_profile_query = professional_profile_query.filter(ProfessionalProfile.primary_sport.ilike(f"%{sport}%"))
    professional_role_filter = _professional_role_for_user_role(user_role) if user_role else None

    if professional_role_filter:
        professional_profile_query = professional_profile_query.filter(
            ProfessionalProfile.professional_role == professional_role_filter
        )
    elif user_role:
        professional_profile_query = professional_profile_query.filter(False)

    active_professional_roles = professional_profile_query.count()

    relationship_query = (
        db.query(ProfessionalAthleteRelationship)
        .join(Athlete, ProfessionalAthleteRelationship.athlete_id == Athlete.athlete_id)
        .filter(ProfessionalAthleteRelationship.status == ProfessionalAthleteRelationshipStatus.ACTIVE.value)
    )
    if sport:
        relationship_query = relationship_query.filter(Athlete.sport.ilike(f"%{sport}%"))
    if professional_role_filter:
        relationship_query = relationship_query.filter(
            ProfessionalAthleteRelationship.professional_role == professional_role_filter
        )
    elif user_role and user_role != UserRole.ATHLETE:
        relationship_query = relationship_query.filter(False)
    active_connections = relationship_query.count()

    request_query = db.query(ProfessionalRoleRequest)
    if sport:
        request_query = request_query.filter(ProfessionalRoleRequest.primary_sport.ilike(f"%{sport}%"))
    if professional_role_filter:
        request_query = request_query.filter(
            ProfessionalRoleRequest.requested_role == professional_role_filter
        )
    elif user_role and user_role.value not in PROFESSIONAL_ROLES:
        request_query = request_query.filter(False)
    requests = [
        request for request in request_query.all()
        if request.submitted_at and start_at <= request.submitted_at <= end_at
    ]

    user_growth_counts = Counter()
    for user in new_users:
        key = _date_key(user.created_at)
        if key:
            user_growth_counts[key] += 1

    analysis_counts = Counter()
    risk_counts = Counter({band: 0 for band in RISK_BANDS})
    sport_counts = Counter()
    for analysis in analyses:
        key = _date_key(_event_date(analysis))
        if key:
            analysis_counts[key] += 1
        score = get_analysis_score(analysis)
        risk_counts[normalize_risk_category_label(analysis.risk_category, score)] += 1
        if analysis.athlete and analysis.athlete.sport:
            sport_counts[analysis.athlete.sport] += 1

    role_counts = Counter()
    for user in users:
        role_counts[_role_value(user.role)] += 1

    request_status_counts = Counter({status.value: 0 for status in ProfessionalRoleRequestStatus})
    for request in requests:
        request_status_counts[request.status] += 1

    sports = [
        sport_value for (sport_value,) in (
            db.query(Athlete.sport)
            .filter(Athlete.sport.isnot(None))
            .distinct()
            .order_by(Athlete.sport)
            .all()
        )
        if sport_value
    ]

    return {
        "filters": {
            "range_days": range_days,
            "date_from": start_at.date().isoformat(),
            "date_to": end_at.date().isoformat(),
            "sport": sport,
            "user_role": user_role.value if user_role else None,
        },
        "sports": sports,
        "summary": {
            "total_users": len(users),
            "new_users": len(new_users),
            "videos_uploaded": len(videos),
            "analyses_completed": len(analyses),
            "active_professionals": active_professional_roles,
            "active_athlete_connections": active_connections,
        },
        "user_growth": [
            {"date": key, "new_users": user_growth_counts[key]}
            for key in sorted(user_growth_counts)
        ],
        "analysis_activity": [
            {"date": key, "completed_analyses": analysis_counts[key]}
            for key in sorted(analysis_counts)
        ],
        "users_by_role": [
            {"label": role.value, "count": role_counts[role.value]}
            for role in UserRole
            if not user_role or role == user_role
        ],
        "analyses_by_sport": [
            {"sport": sport_name, "count": count}
            for sport_name, count in sport_counts.most_common()
        ],
        "risk_distribution": [
            {"label": band.title(), "count": risk_counts[band]}
            for band in RISK_BANDS
        ],
        "professional_activity": {
            "applications": len(requests),
            "approved": request_status_counts[ProfessionalRoleRequestStatus.APPROVED.value],
            "rejected": request_status_counts[ProfessionalRoleRequestStatus.REJECTED.value],
            "pending": request_status_counts[ProfessionalRoleRequestStatus.PENDING.value],
            "active_connections": active_connections,
        },
    }


@router.get("/system-monitoring")
def get_admin_system_monitoring(
    service: str | None = Query(default=None, max_length=80),
    event_status: str | None = Query(default=None, max_length=40),
    event_date: date | None = Query(default=None),
    admin_user: User = Depends(require_roles(UserRole.ADMINISTRATOR)),
    db: Session = Depends(get_db),
):
    del admin_user
    checked_at = _utc_now()

    service_health = []

    service_health.append({
        "service": "Backend / API",
        **_health_status("Healthy", "Admin monitoring endpoint responded successfully.", checked_at),
    })

    try:
        db.execute(text("SELECT 1")).scalar()
        database_status = _health_status("Healthy", "Database connection check succeeded.", checked_at)
    except Exception as exc:
        database_status = _health_status("Unavailable", f"Database connection check failed: {str(exc)}", checked_at)
    service_health.append({"service": "PostgreSQL Database", **database_status})

    if os.getenv("SECRET_KEY"):
        auth_status = _health_status("Healthy", "JWT signing secret is configured.", checked_at)
    else:
        auth_status = _health_status("Unavailable", "JWT signing secret is not configured.", checked_at)
    service_health.append({"service": "Authentication", **auth_status})

    videos = db.query(Video).all()
    analyses = db.query(AnalysisResult).all()

    video_failed_count = sum(
        1 for video in videos
        if _normalized_processing_status(video.processing_status) == "FAILED"
    )
    analysis_failed_count = sum(
        1 for analysis in analyses
        if _normalized_processing_status(analysis.status) == "FAILED"
    )
    active_processing_count = sum(
        1 for video in videos
        if _normalized_processing_status(video.processing_status) == "PROCESSING"
    ) + sum(
        1 for analysis in analyses
        if _normalized_processing_status(analysis.status) == "PROCESSING"
    )

    video_status = "Healthy"
    video_detail = "No failed video-processing records are currently stored."
    if video_failed_count:
        video_status = "Degraded"
        video_detail = f"{video_failed_count} video-processing record(s) are failed."
    service_health.append({
        "service": "Video Processing",
        **_health_status(video_status, video_detail, checked_at),
    })

    mediapipe_status = "Healthy" if importlib.util.find_spec("mediapipe") else "Unavailable"
    mediapipe_detail = (
        "MediaPipe package is importable by the backend runtime."
        if mediapipe_status == "Healthy"
        else "MediaPipe package is not importable by the backend runtime."
    )
    if analysis_failed_count:
        mediapipe_status = "Degraded" if mediapipe_status == "Healthy" else mediapipe_status
        mediapipe_detail = f"{mediapipe_detail} {analysis_failed_count} analysis record(s) are failed."
    service_health.append({
        "service": "MediaPipe Analysis",
        **_health_status(mediapipe_status, mediapipe_detail, checked_at),
    })

    missing_storage_dirs = [
        directory for directory in _required_storage_dirs()
        if not os.path.isdir(directory) or not os.access(directory, os.W_OK)
    ]
    storage_status = "Healthy" if not missing_storage_dirs else "Degraded"
    storage_detail = (
        "Required upload/storage directories exist and are writable."
        if not missing_storage_dirs
        else f"Storage directories unavailable or not writable: {', '.join(missing_storage_dirs)}"
    )
    service_health.append({
        "service": "File Storage",
        **_health_status(storage_status, storage_detail, checked_at),
    })

    processing_counts = Counter({"QUEUED": 0, "PROCESSING": 0, "COMPLETED": 0, "FAILED": 0})
    for video in videos:
        processing_counts[_normalized_processing_status(video.processing_status)] += 1
    for analysis in analyses:
        processing_counts[_normalized_processing_status(analysis.status)] += 1

    events = []
    for analysis in analyses:
        if _normalized_processing_status(analysis.status) != "FAILED":
            continue
        occurred_at = _analysis_time(analysis)
        events.append({
            "time": _serialize_date(occurred_at),
            "service": "MediaPipe Analysis",
            "event": analysis.error_message or analysis.stage or "Analysis failed",
            "status": "FAILED",
        })

    for video in videos:
        if _normalized_processing_status(video.processing_status) != "FAILED":
            continue
        events.append({
            "time": _serialize_date(video.uploaded_at),
            "service": "Video Processing",
            "event": f"Video processing status: {video.processing_status}",
            "status": "FAILED",
        })

    filtered_events = []
    for item in events:
        if service and item["service"].lower() != service.lower():
            continue
        if event_status and item["status"].lower() != event_status.lower():
            continue
        if event_date:
            parsed_time = datetime.fromisoformat(item["time"]) if item["time"] else None
            if not parsed_time or parsed_time.date() != event_date:
                continue
        filtered_events.append(item)

    filtered_events.sort(key=lambda item: item["time"] or "", reverse=True)

    recent_activity_counts = Counter()
    for analysis in analyses:
        occurred_at = _analysis_time(analysis)
        if occurred_at:
            recent_activity_counts[occurred_at.date().isoformat()] += 1

    return {
        "service_health": service_health,
        "overview": {
            "api_status": "Healthy",
            "database_status": database_status["status"],
            "videos_currently_processing": active_processing_count,
            "completed_analyses": sum(1 for analysis in analyses if _normalized_processing_status(analysis.status) == "COMPLETED"),
            "failed_analyses": analysis_failed_count,
            "pending_queued_jobs": processing_counts["QUEUED"],
        },
        "processing_monitor": {
            "queued": processing_counts["QUEUED"],
            "processing": processing_counts["PROCESSING"],
            "completed": processing_counts["COMPLETED"],
            "failed": processing_counts["FAILED"],
            "recent_activity": [
                {"date": key, "records": recent_activity_counts[key]}
                for key in sorted(recent_activity_counts)
            ][-14:],
        },
        "events": filtered_events[:100],
        "event_filters": {
            "services": sorted({item["service"] for item in events}),
            "statuses": sorted({item["status"] for item in events}),
        },
        "last_checked_at": _serialize_date(checked_at),
    }
