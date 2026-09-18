from datetime import date, datetime, time
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.dependencies.auth import require_roles
from app.models.analysis_result import AnalysisResult
from app.models.athlete import Athlete
from app.models.user import User, UserRole
from app.models.video import Video
from app.services.professional_analysis import get_existing_analysis_report_path


router = APIRouter(prefix="/admin/reports", tags=["Admin Reports"])


def _report_date(analysis: AnalysisResult):
    return analysis.completed_at or analysis.analysis_date or analysis.created_at


def _report_status(analysis: AnalysisResult):
    if get_existing_analysis_report_path(analysis.video_id, "pdf"):
        return "AVAILABLE"
    normalized = str(analysis.status or "").lower()
    if normalized in {"processing", "pending"}:
        return "PROCESSING"
    if normalized in {"failed", "error"}:
        return "FAILED"
    return "UNAVAILABLE"


def _report_title(analysis: AnalysisResult):
    athlete_name = analysis.athlete.user.name if analysis.athlete and analysis.athlete.user else "Athlete"
    activity = analysis.video.activity if analysis.video and analysis.video.activity else "Movement Analysis"
    return f"{athlete_name} - {activity}"


def _report_payload(analysis: AnalysisResult):
    pdf_path = get_existing_analysis_report_path(analysis.video_id, "pdf")
    athlete = analysis.athlete
    creator = athlete.user if athlete and athlete.user else None
    return {
        "report_id": str(analysis.analysis_id),
        "analysis_id": str(analysis.analysis_id),
        "video_id": str(analysis.video_id),
        "report_name": _report_title(analysis),
        "report_type": "Movement Analysis PDF",
        "created_by": creator.name if creator else "Unknown",
        "creator_role": creator.role.value if creator and creator.role else "Athlete",
        "sport": athlete.sport if athlete else None,
        "scope": "Athlete",
        "athlete_name": creator.name if creator else None,
        "created_date": _report_date(analysis).isoformat() if _report_date(analysis) else None,
        "status": _report_status(analysis),
        "pdf_available": bool(pdf_path),
        "metadata": {
            "activity": analysis.video.activity if analysis.video else None,
            "analysis_status": analysis.status,
            "risk_category": analysis.risk_category,
            "algorithm_version": analysis.algorithm_version,
        },
    }


def _base_report_query(db: Session):
    return (
        db.query(AnalysisResult)
        .options(
            joinedload(AnalysisResult.athlete).joinedload(Athlete.user),
            joinedload(AnalysisResult.video),
        )
        .join(Athlete, AnalysisResult.athlete_id == Athlete.athlete_id)
        .join(User, Athlete.user_id == User.user_id)
        .outerjoin(Video, AnalysisResult.video_id == Video.video_id)
    )


@router.get("")
def list_admin_reports(
    search: str | None = Query(default=None, max_length=120),
    report_type: str | None = Query(default=None, max_length=80),
    sport: str | None = Query(default=None, max_length=100),
    creator_role: UserRole | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    report_status: str | None = Query(default=None, max_length=40),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    admin_user: User = Depends(require_roles(UserRole.ADMINISTRATOR)),
    db: Session = Depends(get_db),
):
    del admin_user
    query = _base_report_query(db)

    if search:
        term = f"%{search.strip()}%"
        if term != "%%":
            query = query.filter(
                or_(
                    User.name.ilike(term),
                    User.email.ilike(term),
                    Video.activity.ilike(term),
                )
            )
    if sport:
        query = query.filter(Athlete.sport.ilike(f"%{sport}%"))
    if creator_role:
        query = query.filter(User.role == creator_role)
    if date_from:
        query = query.filter(
            func.coalesce(AnalysisResult.completed_at, AnalysisResult.analysis_date, AnalysisResult.created_at)
            >= datetime.combine(date_from, time.min)
        )
    if date_to:
        query = query.filter(
            func.coalesce(AnalysisResult.completed_at, AnalysisResult.analysis_date, AnalysisResult.created_at)
            <= datetime.combine(date_to, time.max)
        )
    if report_type and "movement" not in report_type.lower():
        return {
            "reports": [],
            "total": 0,
            "limit": limit,
            "offset": offset,
            "summary": {
                "total_reports": 0,
                "reports_this_period": 0,
                "pending_processing": 0,
                "archived": None,
            },
            "archive_supported": False,
            "sports": [],
            "report_types": ["Movement Analysis PDF"],
            "statuses": ["AVAILABLE", "PROCESSING", "FAILED", "UNAVAILABLE"],
        }

    analyses = query.order_by(
        func.coalesce(AnalysisResult.completed_at, AnalysisResult.analysis_date, AnalysisResult.created_at).desc()
    ).all()
    reports = [_report_payload(analysis) for analysis in analyses]
    if report_status:
        reports = [report for report in reports if report["status"] == report_status.upper()]

    total = len(reports)
    page = reports[offset:offset + limit]
    pending_processing = sum(1 for report in reports if report["status"] == "PROCESSING")
    generated_count = sum(1 for report in reports if report["pdf_available"])
    sports = [
        value for (value,) in db.query(Athlete.sport).filter(Athlete.sport.isnot(None)).distinct().order_by(Athlete.sport).all()
        if value
    ]

    return {
        "reports": page,
        "total": total,
        "limit": limit,
        "offset": offset,
        "summary": {
            "total_reports": generated_count,
            "reports_this_period": generated_count,
            "pending_processing": pending_processing,
            "archived": None,
        },
        "archive_supported": False,
        "sports": sports,
        "report_types": ["Movement Analysis PDF"],
        "statuses": ["AVAILABLE", "PROCESSING", "FAILED", "UNAVAILABLE"],
    }


@router.get("/{analysis_id}")
def get_admin_report_detail(
    analysis_id: UUID,
    admin_user: User = Depends(require_roles(UserRole.ADMINISTRATOR)),
    db: Session = Depends(get_db),
):
    del admin_user
    analysis = (
        _base_report_query(db)
        .filter(AnalysisResult.analysis_id == analysis_id)
        .first()
    )
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    return _report_payload(analysis)


@router.get("/{analysis_id}/pdf")
def download_admin_report_pdf(
    analysis_id: UUID,
    admin_user: User = Depends(require_roles(UserRole.ADMINISTRATOR)),
    db: Session = Depends(get_db),
):
    del admin_user
    analysis = db.query(AnalysisResult).filter(AnalysisResult.analysis_id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    pdf_path = get_existing_analysis_report_path(analysis.video_id, "pdf")
    if not pdf_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PDF report file is not available")
    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=f"movement_analysis_report_{analysis.video_id}.pdf",
    )
