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
    video_url = f"{BACKEND_URL}/uploads/videos/{filename}",
    duration=metadata["duration"],
    fps=metadata["fps"],
    resolution=metadata["resolution"],
    processing_status="uploaded"
    )

    db.add(video)
    db.commit()
    db.refresh(video)

    # try:

    #     frame_result = extract_frames(
    #         video_path=file_path,
    #         video_id=str(video.video_id),
    #         frame_interval=5
    #     )

    #     print(
    #         f"Frame extraction complete: "
    #         f"{frame_result['saved_frames']} frames saved"
    #     )

    #     video.processing_status = "frames_extracted"

    #     db.commit()
    #     db.refresh(video)

    # except Exception as e:

    #     print(
    #         "Frame extraction failed:",
    #         str(e)
    #     )

    #     video.processing_status = "processing_failed"

    #     db.commit()

    #     raise HTTPException(
    #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #         detail="Video frame extraction failed"
    #     )

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

    # 3. Delete physical video file
    if video.video_url:
        filename = os.path.basename(video.video_url)

        file_path = os.path.join(
            UPLOAD_DIR,
            filename
        )

        if os.path.exists(file_path):
            os.remove(file_path)

    # 4. Delete database record
    db.delete(video)
    db.commit()

    return None