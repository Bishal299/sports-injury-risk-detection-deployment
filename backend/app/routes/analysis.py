import os
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.athlete import Athlete
from app.models.video import Video
from app.models.analysis_result import AnalysisResult
from app.schemas.analysis_result import AnalysisHistoryItem, AnalysisResultResponse, AnalysisStatusResponse
from app.services.movement.pipeline import run_movement_analysis_pipeline


router = APIRouter(
    prefix="/analysis",
    tags=["Movement Analysis"]
)


def _get_athlete_and_video(video_id: UUID, current_user: User, db: Session):
    athlete = db.query(Athlete).filter(Athlete.user_id == current_user.user_id).first()
    if not athlete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Athlete profile not found"
        )

    video = db.query(Video).filter(
        Video.video_id == video_id,
        Video.athlete_id == athlete.athlete_id
    ).first()

    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found or access unauthorized"
        )

    return athlete, video


@router.post(
    "/{video_id}",
    response_model=AnalysisStatusResponse,
    status_code=status.HTTP_202_ACCEPTED
)
def trigger_analysis(
    video_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Triggers AI-based sports movement analysis for the specified video.
    Runs asynchronously in background tasks.
    """
    athlete, video = _get_athlete_and_video(video_id, current_user, db)

    processing = (
        db.query(AnalysisResult)
        .filter(
            AnalysisResult.video_id == video_id,
            AnalysisResult.status == "processing",
        )
        .order_by(AnalysisResult.created_at.desc())
        .first()
    )
    if processing:
        return processing

    active_analysis = (
        db.query(AnalysisResult)
        .filter(
            AnalysisResult.athlete_id == athlete.athlete_id,
            AnalysisResult.status == "processing",
            AnalysisResult.video_id != video.video_id,
        )
        .order_by(AnalysisResult.created_at.desc())
        .first()
    )
    if active_analysis:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Another video analysis is already running. Please wait for it to finish before starting a new one.",
        )

    analysis = AnalysisResult(
        video_id=video.video_id,
        athlete_id=athlete.athlete_id,
        status="processing",
        progress=5,
        stage="Initializing video pipeline...",
        algorithm_version="1.0-phase1-filtered",
    )
    db.add(analysis)

    video.processing_status = "processing"
    db.commit()
    db.refresh(analysis)

    # Dispatch to background task
    background_tasks.add_task(
        run_movement_analysis_pipeline,
        video_id=video_id,
        analysis_id=analysis.analysis_id,
    )

    return analysis


@router.get(
    "/history",
    response_model=list[AnalysisHistoryItem]
)
def get_my_analysis_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    athlete = db.query(Athlete).filter(Athlete.user_id == current_user.user_id).first()
    if not athlete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Athlete profile not found"
        )

    return (
        db.query(AnalysisResult)
        .filter(
            AnalysisResult.athlete_id == athlete.athlete_id,
            AnalysisResult.status == "completed",
        )
        .order_by(AnalysisResult.completed_at.desc(), AnalysisResult.created_at.desc())
        .all()
    )


@router.get(
    "/history/{analysis_id}",
    response_model=AnalysisResultResponse
)
def get_one_analysis(
    analysis_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    athlete = db.query(Athlete).filter(Athlete.user_id == current_user.user_id).first()
    if not athlete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Athlete profile not found"
        )

    analysis = (
        db.query(AnalysisResult)
        .filter(
            AnalysisResult.analysis_id == analysis_id,
            AnalysisResult.athlete_id == athlete.athlete_id,
        )
        .first()
    )
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )

    if hasattr(analysis, "summary_metrics") and isinstance(analysis.summary_metrics, dict):
        setattr(analysis, "risk_assessment", analysis.summary_metrics.get("risk_assessment"))

    return analysis


@router.get(
    "/{video_id}/status",
    response_model=AnalysisStatusResponse
)
def get_analysis_status(
    video_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves current processing progress, stage, and status for polling.
    """
    athlete, video = _get_athlete_and_video(video_id, current_user, db)

    analysis = (
        db.query(AnalysisResult)
        .filter(AnalysisResult.video_id == video_id)
        .order_by(AnalysisResult.created_at.desc())
        .first()
    )
    if not analysis:
        return AnalysisStatusResponse(
            video_id=video_id,
            status="pending",
            progress=0,
            stage="Not started"
        )

    return analysis


@router.get(
    "/{video_id}",
    response_model=AnalysisResultResponse
)
def get_analysis_results(
    video_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves complete movement analysis results for the video.
    """
    athlete, video = _get_athlete_and_video(video_id, current_user, db)

    analysis = (
        db.query(AnalysisResult)
        .filter(AnalysisResult.video_id == video_id)
        .order_by(AnalysisResult.created_at.desc())
        .first()
    )
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis has not been generated for this video yet."
        )

    if hasattr(analysis, "summary_metrics") and isinstance(analysis.summary_metrics, dict):
        setattr(analysis, "risk_assessment", analysis.summary_metrics.get("risk_assessment"))

    return analysis


@router.get(
    "/{video_id}/csv"
)
def download_analysis_csv(
    video_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Downloads the time-series CSV report.
    """
    athlete, video = _get_athlete_and_video(video_id, current_user, db)

    csv_path = os.path.join("uploads/analysis/reports", f"video_{video_id}_timeseries.csv")
    if not os.path.exists(csv_path):
        csv_path = os.path.join("uploads/analysis/reports", f"{video_id}_report.csv")
    if not os.path.exists(csv_path):
        csv_path = os.path.join("uploads/analysis/reports", f"{video_id}_features.csv")
    if not os.path.exists(csv_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CSV report file not found. Please run or re-run the analysis."
        )

    return FileResponse(
        path=csv_path,
        media_type="text/csv",
        filename=f"video_{video_id}_timeseries.csv"
    )


@router.get(
    "/{video_id}/ml-csv"
)
def download_video_ml_csv(
    video_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Downloads the one-row-per-video ML biomechanics CSV.
    """
    athlete, video = _get_athlete_and_video(video_id, current_user, db)

    ml_csv_path = os.path.join("uploads/analysis/reports", f"video_{video_id}_ml.csv")
    if not os.path.exists(ml_csv_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video ML CSV file not found. Please run or re-run the analysis."
        )

    return FileResponse(
        path=ml_csv_path,
        media_type="text/csv",
        filename=f"video_{video_id}_ml.csv"
    )


@router.get(
    "/ml-dataset/master"
)
def download_master_ml_dataset(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Downloads the master multi-video aggregated ML dataset CSV.
    """
    master_path = os.path.join("uploads/analysis/reports", "ml_dataset.csv")
    if not os.path.exists(master_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Master ML dataset has not been generated yet."
        )

    return FileResponse(
        path=master_path,
        media_type="text/csv",
        filename="ml_dataset.csv"
    )


@router.get(
    "/{video_id}/pdf"
)
def download_analysis_pdf(
    video_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Downloads the generated PDF movement analysis report.
    """
    athlete, video = _get_athlete_and_video(video_id, current_user, db)

    pdf_path = os.path.join("uploads/analysis/reports", f"{video_id}_report.pdf")
    if not os.path.exists(pdf_path):
        pdf_path = os.path.join("uploads/analysis/reports", f"{video_id}_features.pdf")
    if not os.path.exists(pdf_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF report file not found. Please run or re-run the analysis."
        )

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=f"movement_analysis_report_{video_id}.pdf"
    )
