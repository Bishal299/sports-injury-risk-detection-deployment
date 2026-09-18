import os
import uuid
import shutil
from app.utils.video import extract_video_metadata
from uuid import UUID
from app.services.video_processing import extract_frames
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

from fastapi import (
    APIRouter,
    Depends,
    File,
    UploadFile,
    Form,
    HTTPException,
    status
)

from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.athlete import Athlete
from app.models.video import Video
from app.models.analysis_result import AnalysisResult
from app.schemas.video import VideoRead


router = APIRouter(
    prefix="/videos",
    tags=["Videos"]
)


UPLOAD_DIR = "uploads/videos"

os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post(
    "/upload",
    response_model=VideoRead,
    status_code=status.HTTP_201_CREATED
)
def upload_video(
    file: UploadFile = File(...),
    activity: str | None = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    # 1. Check file type
    allowed_extensions = {
        ".mp4",
        ".mov",
        ".avi",
        ".mkv"
    }

    file_extension = os.path.splitext(
        file.filename
    )[1].lower()

    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported video format"
        )

    # 2. Find athlete profile
    athlete = (
        db.query(Athlete)
        .filter(
            Athlete.user_id == current_user.user_id
        )
        .first()
    )

    if not athlete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Athlete profile not found"
        )

    # 3. Generate unique filename
    unique_filename = (
        f"{uuid.uuid4()}{file_extension}"
    )

    file_path = os.path.join(
        UPLOAD_DIR,
        unique_filename
    )

    # 4. Save uploaded file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(
                file.file,
                buffer
            )

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save video"
        )
    # Extract video metadata
    try:
        metadata = extract_video_metadata(file_path)

    except Exception:
        metadata = {
            "duration": None,
            "fps": None,
            "resolution": None
        }

    # 5. Create database record
    video = Video(
    athlete_id=athlete.athlete_id,
    activity=activity,
    video_url = f"{BACKEND_URL}/uploads/videos/{unique_filename}",
    duration=metadata["duration"],
    fps=metadata["fps"],
    resolution=metadata["resolution"],
    processing_status="uploaded"
    )

    db.add(video)
    db.commit()
    db.refresh(video)

    

    return video

@router.get(
    "",
    response_model=list[VideoRead]
)
def get_my_videos(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Find athlete profile
    athlete = (
        db.query(Athlete)
        .filter(
            Athlete.user_id == current_user.user_id
        )
        .first()
    )

    if not athlete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Athlete profile not found"
        )

    # Get only this athlete's videos
    videos = (
        db.query(Video)
        .filter(
            Video.athlete_id == athlete.athlete_id
        )
        .order_by(Video.uploaded_at.desc())
        .all()
    )

    return videos


@router.get(
    "/{video_id}",
    response_model=VideoRead
)
def get_video(
    video_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Find athlete profile
    athlete = (
        db.query(Athlete)
        .filter(
            Athlete.user_id == current_user.user_id
        )
        .first()
    )

    if not athlete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Athlete profile not found"
        )

    # Find video belonging to this athlete
    video = (
        db.query(Video)
        .filter(
            Video.video_id == video_id,
            Video.athlete_id == athlete.athlete_id
        )
        .first()
    )

    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )

    return video

@router.post(
    "/{video_id}/analyze"
)
def analyze_video(
    video_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 1. Find athlete profile
    athlete = (
        db.query(Athlete)
        .filter(
            Athlete.user_id == current_user.user_id
        )
        .first()
    )

    if not athlete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Athlete profile not found"
        )

    # 2. Find video belonging to this athlete
    video = (
        db.query(Video)
        .filter(
            Video.video_id == video_id,
            Video.athlete_id == athlete.athlete_id
        )
        .first()
    )

    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )

    active_analysis = (
        db.query(AnalysisResult)
        .filter(
            AnalysisResult.athlete_id == athlete.athlete_id,
            AnalysisResult.status == "processing",
            AnalysisResult.video_id != video.video_id,
        )
        .first()
    )
    if active_analysis:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Another video analysis is already running. Please wait for it to finish before starting a new one.",
        )

    # 3. Get actual video file
    filename = os.path.basename(video.video_url)

    file_path = os.path.join(
        UPLOAD_DIR,
        filename
    )

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video file not found"
        )

    # 4. Update status
    video.processing_status = "processing"
    db.commit()

    # 5. Extract frames
    try:

        frame_result = extract_frames(
            video_path=file_path,
            video_id=str(video.video_id),
            frame_interval=5
        )

        print(
            f"Frame extraction complete: "
            f"{frame_result['saved_frames']} frames saved"
        )

        video.processing_status = "frames_extracted"

        db.commit()
        db.refresh(video)

    except Exception as e:

        print(
            "Frame extraction failed:",
            str(e)
        )

        video.processing_status = "processing_failed"

        db.commit()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Video frame extraction failed"
        )

    return {
        "message": "Video analysis started",
        "video_id": str(video.video_id),
        "status": video.processing_status
    }

def _cleanup_video_storage(video_id: UUID, video_url: str | None):
    """
    Purges all physical storage artifacts for a deleted video:
    - Original uploaded video file
    - Extracted video frames directory
    - Rendered skeleton visualizer video files
    - Generated CSV & PDF report files
    """
    str_id = str(video_id)

    # 1. Source video file
    if video_url:
        filename = os.path.basename(video_url)
        candidates = [
            os.path.join(UPLOAD_DIR, filename),
            os.path.join("uploads", "videos", filename),
        ]
        for c in candidates:
            if os.path.isfile(c):
                try:
                    os.remove(c)
                except OSError:
                    pass

    # 2. Extracted frames folder
    frames_dir = os.path.join("uploads", "frames", str_id)
    if os.path.exists(frames_dir):
        try:
            shutil.rmtree(frames_dir, ignore_errors=True)
        except Exception:
            pass

    # 3. Skeleton visualizer files
    skel_dir = os.path.join("uploads", "analysis", "skeleton")
    if os.path.exists(skel_dir):
        for fname in os.listdir(skel_dir):
            if fname.startswith(str_id):
                fpath = os.path.join(skel_dir, fname)
                try:
                    if os.path.isfile(fpath):
                        os.remove(fpath)
                    elif os.path.isdir(fpath):
                        shutil.rmtree(fpath, ignore_errors=True)
                except Exception:
                    pass

    # 4. CSV & PDF report files
    reports_dir = os.path.join("uploads", "analysis", "reports")
    if os.path.exists(reports_dir):
        for fname in os.listdir(reports_dir):
            if fname.startswith(str_id):
                fpath = os.path.join(reports_dir, fname)
                try:
                    if os.path.isfile(fpath):
                        os.remove(fpath)
                    elif os.path.isdir(fpath):
                        shutil.rmtree(fpath, ignore_errors=True)
                except Exception:
                    pass


@router.delete(
    "/{video_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_video(
    video_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 1. Find the athlete profile
    athlete = (
        db.query(Athlete)
        .filter(
            Athlete.user_id == current_user.user_id
        )
        .first()
    )

    if not athlete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Athlete profile not found"
        )

    # 2. Find the video belonging to this athlete
    video = (
        db.query(Video)
        .filter(
            Video.video_id == video_id,
            Video.athlete_id == athlete.athlete_id
        )
        .first()
    )

    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )

    # 3. Clean up physical files from storage in background
    _cleanup_video_storage(video.video_id, video.video_url)

    # 4. Delete database record (cascades to analysis_results)
    db.delete(video)
    db.commit()

    return None
