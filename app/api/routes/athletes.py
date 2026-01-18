"""Athletes API routes."""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.athletic import Athlete, Sport
from app.models.child import Child
from app.models.user import User
from app.schemas.athlete import (
    AthleteCreate,
    AthleteResponse,
    AthleteUpdate,
    SportResponse,
)

router = APIRouter(prefix="/athletes", tags=["athletes"])


@router.get("/sports", response_model=list[SportResponse])
async def list_sports(db: AsyncSession = Depends(get_db)):
    """List all available sports."""
    result = await db.execute(
        select(Sport).where(Sport.is_active == True).order_by(Sport.name)
    )
    sports = result.scalars().all()
    return [
        SportResponse(
            id=str(sport.id),
            name=sport.name,
            slug=sport.slug,
            description=sport.description,
            icon=sport.icon,
            color=sport.color,
            is_team_sport=sport.is_team_sport,
            has_positions=sport.has_positions,
            season_type=sport.season_type,
            is_active=sport.is_active,
        )
        for sport in sports
    ]


@router.get("", response_model=list[AthleteResponse])
async def list_athletes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all athletes in the user's family."""
    # Get all children in the family
    result = await db.execute(
        select(Child).where(
            Child.family_id == current_user.family_id,
            Child.is_active == True,
        )
    )
    children = result.scalars().all()
    child_ids = [c.id for c in children]

    # Get all athletes for those children
    result = await db.execute(
        select(Athlete)
        .where(Athlete.child_id.in_(child_ids))
        .options(selectinload(Athlete.child), selectinload(Athlete.primary_sport))
    )
    athletes = result.scalars().all()

    return [
        AthleteResponse(
            id=str(athlete.id),
            child_id=str(athlete.child_id),
            primary_sport_id=str(athlete.primary_sport_id) if athlete.primary_sport_id else None,
            secondary_sports=athlete.secondary_sports,
            position=athlete.position,
            height_inches=athlete.height_inches,
            weight_lbs=athlete.weight_lbs,
            dominant_hand=athlete.dominant_hand,
            club_team=athlete.club_team,
            school_team=athlete.school_team,
            jersey_number=athlete.jersey_number,
            recruitment_status=athlete.recruitment_status,
            target_division=athlete.target_division,
            graduation_year=athlete.graduation_year,
            created_at=athlete.created_at,
            updated_at=athlete.updated_at,
        )
        for athlete in athletes
    ]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_athlete(
    data: AthleteCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new athlete profile for a child."""
    # Verify child belongs to user's family
    result = await db.execute(
        select(Child).where(
            Child.id == UUID(data.child_id),
            Child.family_id == current_user.family_id,
            Child.is_active == True,
        )
    )
    child = result.scalar_one_or_none()

    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child not found",
        )

    # Check if athlete profile already exists
    result = await db.execute(
        select(Athlete).where(Athlete.child_id == UUID(data.child_id))
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Athlete profile already exists for this child",
        )

    # Create athlete
    athlete = Athlete(
        child_id=UUID(data.child_id),
        primary_sport_id=UUID(data.primary_sport_id) if data.primary_sport_id else None,
        secondary_sports=data.secondary_sports,
        position=data.position,
        height_inches=data.height_inches,
        weight_lbs=data.weight_lbs,
        dominant_hand=data.dominant_hand,
        club_team=data.club_team,
        school_team=data.school_team,
        jersey_number=data.jersey_number,
        recruitment_status=data.recruitment_status,
        target_division=data.target_division,
        graduation_year=data.graduation_year,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(athlete)
    await db.commit()

    # Redirect to dashboard
    return RedirectResponse(url="/athlete/dashboard", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/{athlete_id}", response_model=AthleteResponse)
async def get_athlete(
    athlete_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific athlete profile."""
    # Get athlete with child relation
    result = await db.execute(
        select(Athlete)
        .where(Athlete.id == athlete_id)
        .options(selectinload(Athlete.child))
    )
    athlete = result.scalar_one_or_none()

    if not athlete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Athlete not found",
        )

    # Verify child belongs to user's family
    if athlete.child.family_id != current_user.family_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    return AthleteResponse(
        id=str(athlete.id),
        child_id=str(athlete.child_id),
        primary_sport_id=str(athlete.primary_sport_id) if athlete.primary_sport_id else None,
        secondary_sports=athlete.secondary_sports,
        position=athlete.position,
        height_inches=athlete.height_inches,
        weight_lbs=athlete.weight_lbs,
        dominant_hand=athlete.dominant_hand,
        club_team=athlete.club_team,
        school_team=athlete.school_team,
        jersey_number=athlete.jersey_number,
        recruitment_status=athlete.recruitment_status,
        target_division=athlete.target_division,
        graduation_year=athlete.graduation_year,
        created_at=athlete.created_at,
        updated_at=athlete.updated_at,
    )


@router.patch("/{athlete_id}", response_model=AthleteResponse)
async def update_athlete(
    athlete_id: UUID,
    data: AthleteUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an athlete profile."""
    # Get athlete with child relation
    result = await db.execute(
        select(Athlete)
        .where(Athlete.id == athlete_id)
        .options(selectinload(Athlete.child))
    )
    athlete = result.scalar_one_or_none()

    if not athlete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Athlete not found",
        )

    # Verify child belongs to user's family
    if athlete.child.family_id != current_user.family_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "primary_sport_id" and value:
            value = UUID(value)
        setattr(athlete, field, value)

    athlete.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(athlete)

    return AthleteResponse(
        id=str(athlete.id),
        child_id=str(athlete.child_id),
        primary_sport_id=str(athlete.primary_sport_id) if athlete.primary_sport_id else None,
        secondary_sports=athlete.secondary_sports,
        position=athlete.position,
        height_inches=athlete.height_inches,
        weight_lbs=athlete.weight_lbs,
        dominant_hand=athlete.dominant_hand,
        club_team=athlete.club_team,
        school_team=athlete.school_team,
        jersey_number=athlete.jersey_number,
        recruitment_status=athlete.recruitment_status,
        target_division=athlete.target_division,
        graduation_year=athlete.graduation_year,
        created_at=athlete.created_at,
        updated_at=athlete.updated_at,
    )


@router.delete("/{athlete_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_athlete(
    athlete_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an athlete profile."""
    # Get athlete with child relation
    result = await db.execute(
        select(Athlete)
        .where(Athlete.id == athlete_id)
        .options(selectinload(Athlete.child))
    )
    athlete = result.scalar_one_or_none()

    if not athlete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Athlete not found",
        )

    # Verify child belongs to user's family
    if athlete.child.family_id != current_user.family_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    await db.delete(athlete)
    await db.commit()
