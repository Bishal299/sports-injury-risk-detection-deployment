from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.athlete import Athlete
from app.models.injury_history import InjuryHistory
from app.schemas.injury_history import (
    InjuryHistoryCreate,
    InjuryHistoryResponse
)


router = APIRouter(
    prefix="/injuries",
    tags=["Injury History"]
)


@router.post(
    "",
    response_model=InjuryHistoryResponse,
    status_code=status.HTTP_201_CREATED
)
def create_injury(
    injury_data: InjuryHistoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Find the athlete profile belonging to the logged-in user
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

    # Create injury record
    injury = InjuryHistory(
        athlete_id=athlete.athlete_id,
        injury_type=injury_data.injury_type,
        body_part=injury_data.body_part,
        severity=injury_data.severity,
        injury_date=injury_data.injury_date,
        recovery_date=injury_data.recovery_date,
        remarks=injury_data.remarks
    )

    db.add(injury)
    db.commit()
    db.refresh(injury)

    return injury


@router.get(
    "",
    response_model=list[InjuryHistoryResponse]
)
def get_injuries(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Find athlete profile
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

    injuries = (
        db.query(InjuryHistory)
        .filter(InjuryHistory.athlete_id == athlete.athlete_id)
        .all()
    )

    return injuries