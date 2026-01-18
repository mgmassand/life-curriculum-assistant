"""API routes for Play-o-Meter activity tracking."""

from datetime import date, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.athletic import ActivityLog, Athlete, FunCheckIn
from app.models.user import User

router = APIRouter(prefix="/activities", tags=["activities"])


class ActivityCreate(BaseModel):
    """Schema for creating an activity log."""

    athlete_id: UUID
    activity_date: date
    activity_type: str = Field(..., description="organized, free_play, or rest")
    sport_id: UUID | None = None
    duration_minutes: int = Field(..., ge=1)
    intensity: str = "moderate"
    context: str | None = None
    location: str | None = None
    rpe: int | None = Field(None, ge=1, le=10)
    notes: str | None = None


class ActivityResponse(BaseModel):
    """Schema for activity log response."""

    id: UUID
    athlete_id: UUID
    activity_date: date
    activity_type: str
    sport_id: UUID | None
    duration_minutes: int
    intensity: str
    context: str | None
    location: str | None
    training_load: float | None
    rpe: int | None
    notes: str | None

    class Config:
        from_attributes = True


class WeeklySummary(BaseModel):
    """Weekly activity summary."""

    athlete_id: UUID
    week_start: date
    week_end: date
    total_minutes: int
    organized_minutes: int
    free_play_minutes: int
    rest_days: int
    activity_count: int
    organized_to_free_ratio: float
    age_appropriate_hours: float
    current_hours: float
    is_over_limit: bool
    recommendations: list[str]


class PlayometerAlert(BaseModel):
    """Alert for Play-o-Meter issues."""

    alert_type: str
    severity: str  # info, warning, critical
    message: str
    recommendation: str


@router.post("", response_model=ActivityResponse, status_code=status.HTTP_201_CREATED)
async def create_activity(
    activity: ActivityCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Log a new activity for an athlete."""
    # Verify user has access to this athlete
    result = await db.execute(
        select(Athlete).where(Athlete.id == activity.athlete_id)
    )
    athlete = result.scalar_one_or_none()
    if not athlete:
        raise HTTPException(status_code=404, detail="Athlete not found")

    # Calculate training load if RPE provided
    training_load = None
    if activity.rpe:
        training_load = activity.rpe * activity.duration_minutes

    db_activity = ActivityLog(
        athlete_id=activity.athlete_id,
        activity_date=activity.activity_date,
        activity_type=activity.activity_type,
        sport_id=activity.sport_id,
        duration_minutes=activity.duration_minutes,
        intensity=activity.intensity,
        context=activity.context,
        location=activity.location,
        training_load=training_load,
        rpe=activity.rpe,
        notes=activity.notes,
        logged_by_id=current_user.id,
    )

    db.add(db_activity)
    await db.commit()
    await db.refresh(db_activity)

    return db_activity


@router.get("/{athlete_id}/weekly", response_model=WeeklySummary)
async def get_weekly_summary(
    athlete_id: UUID,
    week_offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get weekly activity summary for an athlete with Play-o-Meter analysis."""
    # Verify athlete exists
    result = await db.execute(select(Athlete).where(Athlete.id == athlete_id))
    athlete = result.scalar_one_or_none()
    if not athlete:
        raise HTTPException(status_code=404, detail="Athlete not found")

    # Calculate week boundaries
    today = date.today()
    week_start = today - timedelta(days=today.weekday() + (week_offset * 7))
    week_end = week_start + timedelta(days=6)

    # Query activities for the week
    result = await db.execute(
        select(ActivityLog).where(
            ActivityLog.athlete_id == athlete_id,
            ActivityLog.activity_date >= week_start,
            ActivityLog.activity_date <= week_end,
        )
    )
    activities = result.scalars().all()

    # Calculate summaries
    total_minutes = sum(a.duration_minutes for a in activities)
    organized_minutes = sum(
        a.duration_minutes for a in activities if a.activity_type == "organized"
    )
    free_play_minutes = sum(
        a.duration_minutes for a in activities if a.activity_type == "free_play"
    )

    # Count rest days (days with no activity)
    active_dates = {a.activity_date for a in activities}
    all_dates = {week_start + timedelta(days=i) for i in range(7)}
    rest_days = len(all_dates - active_dates)

    # Calculate organized to free play ratio
    if free_play_minutes > 0:
        ratio = organized_minutes / free_play_minutes
    else:
        ratio = float("inf") if organized_minutes > 0 else 0.0

    # Get athlete's age for age-appropriate guidelines
    # Default to 10 if we can't calculate (assume middle of foundation phase)
    child = athlete.child
    if child and child.date_of_birth:
        age_years = (date.today() - child.date_of_birth).days / 365.25
    else:
        age_years = 10

    # LTAD-based age-appropriate weekly hours
    # These are guidelines based on LTAD research
    age_guidelines = {
        (5, 8): 10,   # Active Start / FUNdamentals: max 10 hrs/week organized
        (8, 11): 12,  # Learn to Train: max 12 hrs/week
        (11, 15): 16, # Train to Train: max 16 hrs/week
        (15, 18): 20, # Train to Compete: max 20 hrs/week
    }

    age_appropriate_hours = 10.0
    for (min_age, max_age), hours in age_guidelines.items():
        if min_age <= age_years < max_age:
            age_appropriate_hours = float(hours)
            break
    else:
        if age_years >= 18:
            age_appropriate_hours = 25.0

    current_hours = total_minutes / 60.0
    is_over_limit = current_hours > age_appropriate_hours

    # Generate recommendations
    recommendations = []
    if is_over_limit:
        recommendations.append(
            f"Weekly hours ({current_hours:.1f}) exceed age-appropriate limit ({age_appropriate_hours:.0f} hours)"
        )
    if ratio > 2.0:
        recommendations.append(
            "Consider more free play - organized:free ratio is high"
        )
    if rest_days < 1:
        recommendations.append(
            "Recommend at least 1 rest day per week for recovery"
        )
    if organized_minutes > 0 and free_play_minutes == 0:
        recommendations.append(
            "Add unstructured free play for creativity and joy in movement"
        )

    return WeeklySummary(
        athlete_id=athlete_id,
        week_start=week_start,
        week_end=week_end,
        total_minutes=total_minutes,
        organized_minutes=organized_minutes,
        free_play_minutes=free_play_minutes,
        rest_days=rest_days,
        activity_count=len(activities),
        organized_to_free_ratio=ratio if ratio != float("inf") else 999.0,
        age_appropriate_hours=age_appropriate_hours,
        current_hours=current_hours,
        is_over_limit=is_over_limit,
        recommendations=recommendations,
    )


@router.get("/{athlete_id}/alerts", response_model=list[PlayometerAlert])
async def get_playometer_alerts(
    athlete_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get Play-o-Meter alerts for an athlete."""
    # Get weekly summary for alerts
    result = await db.execute(select(Athlete).where(Athlete.id == athlete_id))
    athlete = result.scalar_one_or_none()
    if not athlete:
        raise HTTPException(status_code=404, detail="Athlete not found")

    alerts = []

    # Check last 7 days of activity
    week_ago = date.today() - timedelta(days=7)
    result = await db.execute(
        select(ActivityLog).where(
            ActivityLog.athlete_id == athlete_id,
            ActivityLog.activity_date >= week_ago,
        )
    )
    recent_activities = result.scalars().all()

    total_minutes = sum(a.duration_minutes for a in recent_activities)
    organized_minutes = sum(
        a.duration_minutes for a in recent_activities if a.activity_type == "organized"
    )
    free_play_minutes = sum(
        a.duration_minutes for a in recent_activities if a.activity_type == "free_play"
    )

    # Get age for guidelines
    child = athlete.child
    if child and child.date_of_birth:
        age_years = (date.today() - child.date_of_birth).days / 365.25
    else:
        age_years = 10

    # Check for overtraining based on age
    age_max_hours = {5: 6, 8: 10, 11: 14, 15: 18, 18: 25}
    max_hours = 10
    for age_threshold, hours in sorted(age_max_hours.items()):
        if age_years >= age_threshold:
            max_hours = hours

    current_hours = total_minutes / 60

    if current_hours > max_hours * 1.2:
        alerts.append(PlayometerAlert(
            alert_type="overtraining",
            severity="critical",
            message=f"Activity exceeds safe limit: {current_hours:.1f} hours this week (max recommended: {max_hours} hours)",
            recommendation="Reduce organized activities and add more rest days"
        ))
    elif current_hours > max_hours:
        alerts.append(PlayometerAlert(
            alert_type="high_volume",
            severity="warning",
            message=f"Activity approaching limit: {current_hours:.1f} hours this week",
            recommendation="Monitor fatigue and consider reducing intensity"
        ))

    # Check organized vs free play ratio
    if organized_minutes > 0 and free_play_minutes == 0:
        alerts.append(PlayometerAlert(
            alert_type="no_free_play",
            severity="warning",
            message="No free play logged this week",
            recommendation="Add unstructured play for physical literacy and enjoyment"
        ))
    elif organized_minutes > free_play_minutes * 3:
        alerts.append(PlayometerAlert(
            alert_type="imbalanced",
            severity="info",
            message="Organized activities significantly outweigh free play",
            recommendation="Research suggests balance leads to better long-term development"
        ))

    # Check for rest days
    active_dates = {a.activity_date for a in recent_activities}
    week_dates = {week_ago + timedelta(days=i) for i in range(7)}
    rest_days = len(week_dates - active_dates)

    if rest_days == 0:
        alerts.append(PlayometerAlert(
            alert_type="no_rest",
            severity="warning",
            message="No rest days in the past week",
            recommendation="Athletes need 1-2 rest days per week for recovery and growth"
        ))

    # Check for fun ratings if available
    result = await db.execute(
        select(FunCheckIn).where(
            FunCheckIn.athlete_id == athlete_id,
            FunCheckIn.check_in_date >= week_ago,
        )
    )
    recent_checkins = result.scalars().all()

    if recent_checkins:
        avg_fun = sum(c.fun_rating for c in recent_checkins) / len(recent_checkins)
        if avg_fun < 3.0:
            alerts.append(PlayometerAlert(
                alert_type="low_enjoyment",
                severity="warning",
                message=f"Average fun rating is low ({avg_fun:.1f}/5)",
                recommendation="Focus on activities the athlete enjoys - fun is essential for development"
            ))

    return alerts


@router.get("/{athlete_id}/history", response_model=list[ActivityResponse])
async def get_activity_history(
    athlete_id: UUID,
    days: int = 30,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get activity history for an athlete."""
    start_date = date.today() - timedelta(days=days)

    result = await db.execute(
        select(ActivityLog)
        .where(
            ActivityLog.athlete_id == athlete_id,
            ActivityLog.activity_date >= start_date,
        )
        .order_by(ActivityLog.activity_date.desc())
    )
    activities = result.scalars().all()

    return activities


@router.delete("/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_activity(
    activity_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete an activity log."""
    result = await db.execute(
        select(ActivityLog).where(ActivityLog.id == activity_id)
    )
    activity = result.scalar_one_or_none()

    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    await db.delete(activity)
    await db.commit()
