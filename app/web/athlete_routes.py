"""Athlete web routes."""

from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user_optional, get_current_user
from app.db.session import get_db
from app.models.athletic import (
    Athlete,
    AthleticAgeStage,
    AthleticDomain,
    AthleticMilestone,
    Sport,
    TrainingPlan,
)
from app.models.child import Child
from app.models.user import User

router = APIRouter(prefix="/athlete", tags=["athlete-web"])

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


@router.get("", response_class=HTMLResponse)
async def athlete_landing(
    request: Request,
    current_user: User | None = Depends(get_current_user_optional),
):
    """Athlete curriculum landing page."""
    return templates.TemplateResponse(
        "pages/athlete/landing.html",
        {
            "request": request,
            "current_user": current_user,
        },
    )


@router.get("/dashboard", response_class=HTMLResponse)
async def athlete_dashboard(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Athlete dashboard with all athlete profiles."""
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

    # Get available sports
    result = await db.execute(
        select(Sport).where(Sport.is_active == True).order_by(Sport.name)
    )
    sports = result.scalars().all()

    # Get children without athlete profiles
    athlete_child_ids = {a.child_id for a in athletes}
    available_children = [c for c in children if c.id not in athlete_child_ids]

    return templates.TemplateResponse(
        "pages/athlete/dashboard.html",
        {
            "request": request,
            "current_user": current_user,
            "athletes": athletes,
            "children": available_children,
            "sports": sports,
        },
    )


@router.get("/athletes/{athlete_id}", response_class=HTMLResponse)
async def athlete_profile(
    request: Request,
    athlete_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Individual athlete profile page."""
    # Get athlete with relationships
    result = await db.execute(
        select(Athlete)
        .where(Athlete.id == athlete_id)
        .options(
            selectinload(Athlete.child),
            selectinload(Athlete.primary_sport),
            selectinload(Athlete.academic_records),
            selectinload(Athlete.training_plan_assignments),
            selectinload(Athlete.recruitment_contacts),
        )
    )
    athlete = result.scalar_one_or_none()

    if not athlete or athlete.child.family_id != current_user.family_id:
        return RedirectResponse(url="/athlete/dashboard")

    # Get sports for editing
    result = await db.execute(
        select(Sport).where(Sport.is_active == True).order_by(Sport.name)
    )
    sports = result.scalars().all()

    return templates.TemplateResponse(
        "pages/athlete/profile.html",
        {
            "request": request,
            "current_user": current_user,
            "athlete": athlete,
            "sports": sports,
        },
    )


@router.get("/training", response_class=HTMLResponse)
async def training_index(
    request: Request,
    athlete_id: UUID | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Training plans browser."""
    # Get available training plan templates
    result = await db.execute(
        select(TrainingPlan)
        .where(TrainingPlan.is_template == True, TrainingPlan.is_active == True)
        .options(
            selectinload(TrainingPlan.sport),
            selectinload(TrainingPlan.athletic_age_stage),
        )
        .order_by(TrainingPlan.name)
    )
    plans = result.scalars().all()

    # Get sports and age stages for filtering
    result = await db.execute(
        select(Sport).where(Sport.is_active == True).order_by(Sport.name)
    )
    sports = result.scalars().all()

    result = await db.execute(
        select(AthleticAgeStage).order_by(AthleticAgeStage.order)
    )
    age_stages = result.scalars().all()

    # Get user's athletes
    result = await db.execute(
        select(Child).where(
            Child.family_id == current_user.family_id,
            Child.is_active == True,
        )
    )
    children = result.scalars().all()
    child_ids = [c.id for c in children]

    result = await db.execute(
        select(Athlete)
        .where(Athlete.child_id.in_(child_ids))
        .options(selectinload(Athlete.child))
    )
    athletes = result.scalars().all()

    return templates.TemplateResponse(
        "pages/athlete/training/index.html",
        {
            "request": request,
            "current_user": current_user,
            "plans": plans,
            "sports": sports,
            "age_stages": age_stages,
            "athletes": athletes,
            "selected_athlete_id": athlete_id,
        },
    )


@router.get("/academics", response_class=HTMLResponse)
async def academics_index(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Academic tracking overview."""
    # Get user's athletes with academic records
    result = await db.execute(
        select(Child).where(
            Child.family_id == current_user.family_id,
            Child.is_active == True,
        )
    )
    children = result.scalars().all()
    child_ids = [c.id for c in children]

    result = await db.execute(
        select(Athlete)
        .where(Athlete.child_id.in_(child_ids))
        .options(
            selectinload(Athlete.child),
            selectinload(Athlete.academic_records),
        )
    )
    athletes = result.scalars().all()

    return templates.TemplateResponse(
        "pages/athlete/academics/index.html",
        {
            "request": request,
            "current_user": current_user,
            "athletes": athletes,
        },
    )


@router.get("/recruitment", response_class=HTMLResponse)
async def recruitment_index(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Recruitment dashboard."""
    # Get user's athletes with recruitment data
    result = await db.execute(
        select(Child).where(
            Child.family_id == current_user.family_id,
            Child.is_active == True,
        )
    )
    children = result.scalars().all()
    child_ids = [c.id for c in children]

    result = await db.execute(
        select(Athlete)
        .where(Athlete.child_id.in_(child_ids))
        .options(
            selectinload(Athlete.child),
            selectinload(Athlete.recruitment_contacts),
            selectinload(Athlete.recruitment_events),
        )
    )
    athletes = result.scalars().all()

    return templates.TemplateResponse(
        "pages/athlete/recruitment/index.html",
        {
            "request": request,
            "current_user": current_user,
            "athletes": athletes,
        },
    )


@router.get("/progress", response_class=HTMLResponse)
async def progress_index(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Athletic progress and milestones overview."""
    # Get user's athletes
    result = await db.execute(
        select(Child).where(
            Child.family_id == current_user.family_id,
            Child.is_active == True,
        )
    )
    children = result.scalars().all()
    child_ids = [c.id for c in children]

    result = await db.execute(
        select(Athlete)
        .where(Athlete.child_id.in_(child_ids))
        .options(
            selectinload(Athlete.child),
            selectinload(Athlete.athletic_progress),
            selectinload(Athlete.performance_metrics),
        )
    )
    athletes = result.scalars().all()

    # Get domains for filtering
    result = await db.execute(select(AthleticDomain))
    domains = result.scalars().all()

    return templates.TemplateResponse(
        "pages/athlete/progress/index.html",
        {
            "request": request,
            "current_user": current_user,
            "athletes": athletes,
            "domains": domains,
        },
    )


@router.get("/chat", response_class=HTMLResponse)
async def athlete_chat(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """AI Coach for athletes."""
    # Get user's athletes for context
    result = await db.execute(
        select(Child).where(
            Child.family_id == current_user.family_id,
            Child.is_active == True,
        )
    )
    children = result.scalars().all()
    child_ids = [c.id for c in children]

    result = await db.execute(
        select(Athlete)
        .where(Athlete.child_id.in_(child_ids))
        .options(selectinload(Athlete.child), selectinload(Athlete.primary_sport))
    )
    athletes = result.scalars().all()

    return templates.TemplateResponse(
        "pages/athlete/chat.html",
        {
            "request": request,
            "current_user": current_user,
            "athletes": athletes,
        },
    )


# =============================================================================
# AthleteLife 360 - Foundation Features (Ages 5-10)
# =============================================================================


@router.get("/playometer", response_class=HTMLResponse)
async def playometer_index(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Play-o-Meter: Track organized vs free play activities."""
    # Get user's athletes
    result = await db.execute(
        select(Child).where(
            Child.family_id == current_user.family_id,
            Child.is_active == True,
        )
    )
    children = result.scalars().all()
    child_ids = [c.id for c in children]

    result = await db.execute(
        select(Athlete)
        .where(Athlete.child_id.in_(child_ids))
        .options(selectinload(Athlete.child), selectinload(Athlete.primary_sport))
    )
    athletes = result.scalars().all()

    # Get sports
    result = await db.execute(
        select(Sport).where(Sport.is_active == True).order_by(Sport.name)
    )
    sports = result.scalars().all()

    return templates.TemplateResponse(
        "pages/athlete/playometer/index.html",
        {
            "request": request,
            "current_user": current_user,
            "athletes": athletes,
            "sports": sports,
        },
    )


@router.get("/checkin", response_class=HTMLResponse)
async def checkin_index(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fun Check-in: Emoji-based enjoyment tracking."""
    # Get user's athletes
    result = await db.execute(
        select(Child).where(
            Child.family_id == current_user.family_id,
            Child.is_active == True,
        )
    )
    children = result.scalars().all()
    child_ids = [c.id for c in children]

    result = await db.execute(
        select(Athlete)
        .where(Athlete.child_id.in_(child_ids))
        .options(selectinload(Athlete.child), selectinload(Athlete.primary_sport))
    )
    athletes = result.scalars().all()

    return templates.TemplateResponse(
        "pages/athlete/checkin/index.html",
        {
            "request": request,
            "current_user": current_user,
            "athletes": athletes,
        },
    )


@router.get("/twin", response_class=HTMLResponse)
async def digital_twin_index(
    request: Request,
    athlete_id: UUID | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Digital Athlete Twin: Unified athlete data dashboard."""
    # Get user's athletes
    result = await db.execute(
        select(Child).where(
            Child.family_id == current_user.family_id,
            Child.is_active == True,
        )
    )
    children = result.scalars().all()
    child_ids = [c.id for c in children]

    result = await db.execute(
        select(Athlete)
        .where(Athlete.child_id.in_(child_ids))
        .options(
            selectinload(Athlete.child),
            selectinload(Athlete.primary_sport),
            selectinload(Athlete.academic_records),
            selectinload(Athlete.training_plan_assignments),
            selectinload(Athlete.recruitment_contacts),
        )
    )
    athletes = result.scalars().all()

    # Select athlete (use provided ID or first athlete)
    selected_athlete = None
    if athletes:
        if athlete_id:
            selected_athlete = next((a for a in athletes if a.id == athlete_id), athletes[0])
        else:
            selected_athlete = athletes[0]

    return templates.TemplateResponse(
        "pages/athlete/twin/index.html",
        {
            "request": request,
            "current_user": current_user,
            "athletes": athletes,
            "selected_athlete": selected_athlete,
        },
    )
