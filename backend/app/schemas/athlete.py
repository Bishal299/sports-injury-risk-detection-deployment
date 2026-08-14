from uuid import UUID

from pydantic import BaseModel, ConfigDict

from typing import Optional

class AthleteCreate(BaseModel):
    sport: str | None = None
    position: str | None = None
    age: int | None = None
    height: float | None = None
    weight: float | None = None

    training_load: float | None = None
    flexibility: float | None = None
    strength: float | None = None
    balance: float | None = None
    endurance: float | None = None

    coach_notes: str | None = None


class AthleteRead(BaseModel):
    athlete_id: UUID
    user_id: UUID

    sport: str | None = None
    position: str | None = None
    age: int | None = None
    height: float | None = None
    weight: float | None = None

    training_load: float | None = None
    flexibility: float | None = None
    strength: float | None = None
    balance: float | None = None
    endurance: float | None = None

    coach_notes: str | None = None

    model_config = ConfigDict(from_attributes=True)





class AthleteUpdate(BaseModel):
    sport: Optional[str] = None
    position: Optional[str] = None
    age: Optional[int] = None
    height: Optional[float] = None
    weight: Optional[float] = None

    training_load: Optional[float] = None
    flexibility: Optional[float] = None
    strength: Optional[float] = None
    balance: Optional[float] = None
    endurance: Optional[float] = None

    coach_notes: Optional[str] = None