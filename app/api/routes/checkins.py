"""API routes for Fun Check-in emoji-based enjoyment tracking."""

from datetime import date, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.athletic import Athlete, FunCheckIn, ActivityLog
from app.models.user import User

router = APIRouter(prefix="/checkins", tags=["checkins"])


class FunCheckInCreate(BaseModel):
    """Schema for creating a fun check-in."""

    athlete_id: UUID
    check_in_date: date
    activity_log_id: UUID | None = None
    fun_rating: int = Field(..., ge=1, le=5, description="1=Not fun, 5=Super fun!")
    energy_rating: int | None = Field(None, ge=1, le=5, description="1=Tired, 5=Energized")
    friend_rating: int | None = Field(None, ge=1, le=5, description="1=Alone, 5=Lots of friends")
    favorite_moment: str | None = Field(None, max_length=500)
    want_to_do_again: bool | None = None


class FunCheckInResponse(BaseModel):
    """Schema for fun check-in response."""

    id: UUID
    athlete_id: UUID
    check_in_date: date
    activity_log_id: UUID | None
    fun_rating: int
    energy_rating: int | None
    friend_rating: int | None
    favorite_moment: str | None
    want_to_do_again: bool | None

    class Config:
        from_attributes = True


class FunTrend(BaseModel):
    """Trend analysis for fun ratings."""

    athlete_id: UUID
    period_start: date
    period_end: date
    average_fun: float
    average_energy: float | None
    average_friends: float | None
    total_checkins: int
    want_to_repeat_percent: float | None
    fun_trend: str  # improving, stable, declining
    highlights: list[str]


# Emoji mappings for display
FUN_EMOJIS = {
    1: {"emoji": "😢", "label": "Not fun"},
    2: {"emoji": "😕", "label": "Meh"},
    3: {"emoji": "😐", "label": "Okay"},
    4: {"emoji": "😊", "label": "Fun!"},
    5: {"emoji": "🤩", "label": "Super fun!"},
}

ENERGY_EMOJIS = {
    1: {"emoji": "😴", "label": "Exhausted"},
    2: {"emoji": "🥱", "label": "Tired"},
    3: {"emoji": "😌", "label": "Normal"},
    4: {"emoji": "😃", "label": "Energized"},
    5: {"emoji": "⚡", "label": "Super energized!"},
}

FRIEND_EMOJIS = {
    1: {"emoji": "🧍", "label": "Alone"},
    2: {"emoji": "👥", "label": "One friend"},
    3: {"emoji": "👥👤", "label": "A few friends"},
    4: {"emoji": "👨‍👩‍👧‍👦", "label": "Team"},
    5: {"emoji": "🎉", "label": "Big group!"},
}


@router.get("/emojis")
async def get_emoji_options():
    """Get emoji options for the check-in interface."""
    return {
        "fun": FUN_EMOJIS,
        "energy": ENERGY_EMOJIS,
        "friends": FRIEND_EMOJIS,
    }


@router.post("", response_model=FunCheckInResponse, status_code=status.HTTP_201_CREATED)
async def create_checkin(
    checkin: FunCheckInCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new fun check-in for an athlete."""
    # Verify athlete exists
    result = await db.execute(
        select(Athlete).where(Athlete.id == checkin.athlete_id)
    )
    athlete = result.scalar_one_or_none()
    if not athlete:
        raise HTTPException(status_code=404, detail="Athlete not found")

    # Verify activity log if provided
    if checkin.activity_log_id:
        result = await db.execute(
            select(ActivityLog).where(
                ActivityLog.id == checkin.activity_log_id,
                ActivityLog.athlete_id == checkin.athlete_id,
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Activity log not found")

    db_checkin = FunCheckIn(
        athlete_id=checkin.athlete_id,
        check_in_date=checkin.check_in_date,
        activity_log_id=checkin.activity_log_id,
        fun_rating=checkin.fun_rating,
        energy_rating=checkin.energy_rating,
        friend_rating=checkin.friend_rating,
        favorite_moment=checkin.favorite_moment,
        want_to_do_again=checkin.want_to_do_again,
    )

    db.add(db_checkin)
    await db.commit()
    await db.refresh(db_checkin)

    return db_checkin


@router.get("/{athlete_id}/recent", response_model=list[FunCheckInResponse])
async def get_recent_checkins(
    athlete_id: UUID,
    days: int = 14,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get recent fun check-ins for an athlete."""
    start_date = date.today() - timedelta(days=days)

    result = await db.execute(
        select(FunCheckIn)
        .where(
            FunCheckIn.athlete_id == athlete_id,
            FunCheckIn.check_in_date >= start_date,
        )
        .order_by(FunCheckIn.check_in_date.desc())
    )
    checkins = result.scalars().all()

    return checkins


@router.get("/{athlete_id}/trend", response_model=FunTrend)
async def get_fun_trend(
    athlete_id: UUID,
    days: int = 30,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get fun rating trend analysis for an athlete."""
    # Verify athlete exists
    result = await db.execute(
        select(Athlete).where(Athlete.id == athlete_id)
    )
    athlete = result.scalar_one_or_none()
    if not athlete:
        raise HTTPException(status_code=404, detail="Athlete not found")

    period_end = date.today()
    period_start = period_end - timedelta(days=days)
    period_mid = period_end - timedelta(days=days // 2)

    # Get all check-ins for the period
    result = await db.execute(
        select(FunCheckIn)
        .where(
            FunCheckIn.athlete_id == athlete_id,
            FunCheckIn.check_in_date >= period_start,
        )
        .order_by(FunCheckIn.check_in_date)
    )
    checkins = list(result.scalars().all())

    if not checkins:
        return FunTrend(
            athlete_id=athlete_id,
            period_start=period_start,
            period_end=period_end,
            average_fun=0.0,
            average_energy=None,
            average_friends=None,
            total_checkins=0,
            want_to_repeat_percent=None,
            fun_trend="stable",
            highlights=["No check-ins recorded yet. Start tracking how you feel after activities!"],
        )

    # Calculate averages
    avg_fun = sum(c.fun_rating for c in checkins) / len(checkins)

    energy_ratings = [c.energy_rating for c in checkins if c.energy_rating]
    avg_energy = sum(energy_ratings) / len(energy_ratings) if energy_ratings else None

    friend_ratings = [c.friend_rating for c in checkins if c.friend_rating]
    avg_friends = sum(friend_ratings) / len(friend_ratings) if friend_ratings else None

    # Calculate want to repeat percentage
    repeat_answers = [c.want_to_do_again for c in checkins if c.want_to_do_again is not None]
    if repeat_answers:
        want_to_repeat_percent = (sum(1 for r in repeat_answers if r) / len(repeat_answers)) * 100
    else:
        want_to_repeat_percent = None

    # Determine trend by comparing first half to second half
    first_half = [c for c in checkins if c.check_in_date < period_mid]
    second_half = [c for c in checkins if c.check_in_date >= period_mid]

    if first_half and second_half:
        first_avg = sum(c.fun_rating for c in first_half) / len(first_half)
        second_avg = sum(c.fun_rating for c in second_half) / len(second_half)
        diff = second_avg - first_avg

        if diff > 0.5:
            fun_trend = "improving"
        elif diff < -0.5:
            fun_trend = "declining"
        else:
            fun_trend = "stable"
    else:
        fun_trend = "stable"

    # Generate highlights
    highlights = []

    if avg_fun >= 4.0:
        highlights.append("Great job keeping sports fun! High enjoyment leads to lifelong activity.")
    elif avg_fun >= 3.0:
        highlights.append("Good overall enjoyment. Consider what makes activities more fun.")
    else:
        highlights.append("Fun levels are lower than ideal. Let's talk about what would make sports more enjoyable.")

    if fun_trend == "improving":
        highlights.append("Your enjoyment is trending up - keep doing what you're doing!")
    elif fun_trend == "declining":
        highlights.append("Enjoyment seems to be decreasing. It might be time to try something new or take a break.")

    # Check for favorite moments
    moments = [c.favorite_moment for c in checkins if c.favorite_moment]
    if moments:
        highlights.append(f"You've shared {len(moments)} favorite moments - these memories matter!")

    if avg_friends and avg_friends >= 4.0:
        highlights.append("Strong social connections in your activities - friends make everything better!")

    return FunTrend(
        athlete_id=athlete_id,
        period_start=period_start,
        period_end=period_end,
        average_fun=round(avg_fun, 2),
        average_energy=round(avg_energy, 2) if avg_energy else None,
        average_friends=round(avg_friends, 2) if avg_friends else None,
        total_checkins=len(checkins),
        want_to_repeat_percent=round(want_to_repeat_percent, 1) if want_to_repeat_percent else None,
        fun_trend=fun_trend,
        highlights=highlights,
    )


@router.delete("/{checkin_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_checkin(
    checkin_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a fun check-in."""
    result = await db.execute(
        select(FunCheckIn).where(FunCheckIn.id == checkin_id)
    )
    checkin = result.scalar_one_or_none()

    if not checkin:
        raise HTTPException(status_code=404, detail="Check-in not found")

    await db.delete(checkin)
    await db.commit()
