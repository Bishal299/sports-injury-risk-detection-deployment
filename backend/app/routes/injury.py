from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.athlete import Athlete
from app.models.injury_history import InjuryHistory
from app.schemas.injury_history import (
    InjuryHistoryCreate,
    InjuryHistoryResponse,
    InjuryHistoryUpdate,
)


router = APIRouter(tags=["Injury History"])


def _get_owned_athlete(athlete_id: UUID, current_user: User, db: Session) -> Athlete:
    athlete = (
        db.query(Athlete)
        .filter(
            Athlete.athlete_id == athlete_id,
            Athlete.user_id == current_user.user_id,
        )
        .first()
    )

    if not athlete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Athlete profile not found"
        )

    return athlete


def _get_current_user_athlete(current_user: User, db: Session) -> Athlete:
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


def _get_owned_injury(
    athlete_id: UUID,
    injury_id: UUID,
    current_user: User,
    db: Session,
) -> InjuryHistory:
    _get_owned_athlete(athlete_id, current_user, db)

    injury = (
        db.query(InjuryHistory)
        .filter(
            InjuryHistory.injury_id == injury_id,
            InjuryHistory.athlete_id == athlete_id,
        )
        .first()
    )

    if not injury:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Injury record not found"
        )

    return injury


def _validate_injury_record(injury: InjuryHistory):
    if not injury.injury_type or not injury.injury_type.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="injury_type cannot be empty",
        )

    if not injury.body_part or not injury.body_part.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="body_part cannot be empty",
        )

    if injury.recovery_date and injury.injury_date and injury.recovery_date < injury.injury_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="recovery_date cannot be earlier than injury_date",
        )

    if injury.status == "ACTIVE" and injury.recovery_date is not None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="recovery_date should be empty for ACTIVE injuries",
        )


@router.get(
    "/athletes/{athlete_id}/injury-history",
    response_model=list[InjuryHistoryResponse]
)
def list_athlete_injuries(
    athlete_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    _get_owned_athlete(athlete_id, current_user, db)

    return (
        db.query(InjuryHistory)
        .filter(InjuryHistory.athlete_id == athlete_id)
        .order_by(InjuryHistory.injury_date.desc(), InjuryHistory.created_at.desc())
        .all()
    )


@router.get(
    "/athletes/{athlete_id}/injury-history/{injury_id}",
    response_model=InjuryHistoryResponse
)
def get_athlete_injury(
    athlete_id: UUID,
    injury_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return _get_owned_injury(athlete_id, injury_id, current_user, db)


@router.post(
    "/athletes/{athlete_id}/injury-history",
    response_model=InjuryHistoryResponse,
    status_code=status.HTTP_201_CREATED
)
def create_athlete_injury(
    athlete_id: UUID,
    injury_data: InjuryHistoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    _get_owned_athlete(athlete_id, current_user, db)

    injury = InjuryHistory(
        athlete_id=athlete_id,
        injury_type=injury_data.injury_type.strip(),
        body_part=injury_data.body_part.strip(),
        affected_side=injury_data.affected_side.value,
        severity=injury_data.severity.value,
        status=injury_data.status.value,
        injury_date=injury_data.injury_date,
        recovery_date=injury_data.recovery_date,
        remarks=injury_data.remarks
    )

    _validate_injury_record(injury)

    db.add(injury)
    db.commit()
    db.refresh(injury)

    return injury


@router.put(
    "/athletes/{athlete_id}/injury-history/{injury_id}",
    response_model=InjuryHistoryResponse
)
def update_athlete_injury(
    athlete_id: UUID,
    injury_id: UUID,
    injury_data: InjuryHistoryUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    injury = _get_owned_injury(athlete_id, injury_id, current_user, db)
    updates = injury_data.model_dump(exclude_unset=True)

    for field, value in updates.items():
        if field in {"injury_type", "body_part"} and value is not None:
            value = value.strip()
        if hasattr(value, "value"):
            value = value.value
        setattr(injury, field, value)

    _validate_injury_record(injury)

    db.commit()
    db.refresh(injury)

    return injury


@router.delete(
    "/athletes/{athlete_id}/injury-history/{injury_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_athlete_injury(
    athlete_id: UUID,
    injury_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    injury = _get_owned_injury(athlete_id, injury_id, current_user, db)

    db.delete(injury)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/injuries",
    response_model=list[InjuryHistoryResponse]
)
def get_my_injuries(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    athlete = _get_current_user_athlete(current_user, db)
    return list_athlete_injuries(athlete.athlete_id, current_user, db)


@router.post(
    "/injuries",
    response_model=InjuryHistoryResponse,
    status_code=status.HTTP_201_CREATED
)
def create_my_injury(
    injury_data: InjuryHistoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    athlete = _get_current_user_athlete(current_user, db)
    return create_athlete_injury(athlete.athlete_id, injury_data, current_user, db)
