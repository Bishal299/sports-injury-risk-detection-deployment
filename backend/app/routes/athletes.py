from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.athlete import Athlete
from app.schemas.athlete import AthleteCreate, AthleteRead, AthleteUpdate


router = APIRouter(
    prefix="/athletes",
    tags=["Athletes"]
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