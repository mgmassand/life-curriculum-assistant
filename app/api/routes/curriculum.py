"""Curriculum routes."""

from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.child import Child
from app.models.curriculum import Activity, AgeStage, DevelopmentDomain, Milestone
from app.models.user import User
from app.schemas.curriculum import (
    ActivityResponse,
    AgeStageResponse,
    AgeStageWithCountsResponse,
    CurriculumOverviewResponse,
    DomainResponse,
    MilestoneResponse,
)

router = APIRouter(prefix="/curriculum", tags=["curriculum"])

# Templates for HTMX responses
templates = Jinja2Templates(
    directory=str(Path(__file__).parent.parent.parent / "web" / "templates")
)


@router.get("/domains", response_model=list[DomainResponse])
async def list_domains(db: AsyncSession = Depends(get_db)):
    """List all development domains."""
    result = await db.execute(select(DevelopmentDomain).order_by(DevelopmentDomain.name))
    domains = result.scalars().all()

    return [
        DomainResponse(
            id=str(d.id),
            name=d.name,
            slug=d.slug,
            description=d.description,
            icon=d.icon,
            color=d.color,
        )
        for d in domains
    ]


@router.get("/age-stages", response_model=list[AgeStageWithCountsResponse])
async def list_age_stages(db: AsyncSession = Depends(get_db)):
    """List all age stages with counts."""
    result = await db.execute(select(AgeStage).order_by(AgeStage.order))
    stages = result.scalars().all()

    response = []
    for stage in stages:
        # Get counts
        milestone_count = await db.execute(
            select(func.count(Milestone.id)).where(Milestone.age_stage_id == stage.id)
        )
        activity_count = await db.execute(
            select(func.count(Activity.id)).where(Activity.age_stage_id == stage.id)
        )

        response.append(
            AgeStageWithCountsResponse(
                id=str(stage.id),
                name=stage.name,
                slug=stage.slug,
                min_age_months=stage.min_age_months,
                max_age_months=stage.max_age_months,
                description=stage.description,
                order=stage.order,
                milestone_count=milestone_count.scalar() or 0,
                activity_count=activity_count.scalar() or 0,
            )
        )

    return response


@router.get("/age-stages/{stage_slug}")
async def get_age_stage_curriculum(
    request: Request,
    stage_slug: str,
    domain_slug: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Get curriculum for a specific age stage."""
    # Get age stage
    result = await db.execute(select(AgeStage).where(AgeStage.slug == stage_slug))
    stage = result.scalar_one_or_none()

    if not stage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Age stage not found",
        )

    # Get domains
    result = await db.execute(select(DevelopmentDomain).order_by(DevelopmentDomain.name))
    domains = result.scalars().all()

    # Build milestone query
    milestone_query = (
        select(Milestone)
        .options(selectinload(Milestone.domain))
        .where(Milestone.age_stage_id == stage.id, Milestone.is_active == True)
    )
    if domain_slug:
        result = await db.execute(
            select(DevelopmentDomain).where(DevelopmentDomain.slug == domain_slug)
        )
        domain = result.scalar_one_or_none()
        if domain:
            milestone_query = milestone_query.where(Milestone.domain_id == domain.id)

    result = await db.execute(milestone_query.order_by(Milestone.typical_age_months))
    milestones = result.scalars().all()

    # Build activity query
    activity_query = (
        select(Activity)
        .options(selectinload(Activity.domain))
        .where(Activity.age_stage_id == stage.id, Activity.is_active == True)
    )
    if domain_slug:
        result = await db.execute(
            select(DevelopmentDomain).where(DevelopmentDomain.slug == domain_slug)
        )
        domain = result.scalar_one_or_none()
        if domain:
            activity_query = activity_query.where(Activity.domain_id == domain.id)

    result = await db.execute(activity_query.order_by(Activity.title))
    activities = result.scalars().all()

    # Return HTML for HTMX requests
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            "partials/curriculum_content.html",
            {
                "request": request,
                "stage": stage,
                "domains": domains,
                "milestones": milestones,
                "activities": activities,
                "selected_domain": domain_slug,
            },
        )

    # Return JSON for API requests
    return CurriculumOverviewResponse(
        age_stage=AgeStageResponse(
            id=str(stage.id),
            name=stage.name,
            slug=stage.slug,
            min_age_months=stage.min_age_months,
            max_age_months=stage.max_age_months,
            description=stage.description,
            order=stage.order,
        ),
        domains=[
            DomainResponse(
                id=str(d.id),
                name=d.name,
                slug=d.slug,
                description=d.description,
                icon=d.icon,
                color=d.color,
            )
            for d in domains
        ],
        milestones=[
            MilestoneResponse(
                id=str(m.id),
                title=m.title,
                description=m.description,
                typical_age_months=m.typical_age_months,
                importance=m.importance,
                domain=DomainResponse(
                    id=str(m.domain.id),
                    name=m.domain.name,
                    slug=m.domain.slug,
                    description=m.domain.description,
                    icon=m.domain.icon,
                    color=m.domain.color,
                )
                if m.domain
                else None,
            )
            for m in milestones
        ],
        activities=[
            ActivityResponse(
                id=str(a.id),
                title=a.title,
                description=a.description,
                instructions=a.instructions,
                duration_minutes=a.duration_minutes,
                materials_needed=a.materials_needed,
                difficulty=a.difficulty,
                week_number=a.week_number,
                domain=DomainResponse(
                    id=str(a.domain.id),
                    name=a.domain.name,
                    slug=a.domain.slug,
                    description=a.domain.description,
                    icon=a.domain.icon,
                    color=a.domain.color,
                )
                if a.domain
                else None,
            )
            for a in activities
        ],
    )


@router.get("/for-child/{child_id}")
async def get_curriculum_for_child(
    request: Request,
    child_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get age-appropriate curriculum for a specific child."""
    # Get child and verify access
    result = await db.execute(
        select(Child).where(
            Child.id == child_id,
            Child.family_id == current_user.family_id,
        )
    )
    child = result.scalar_one_or_none()

    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child not found",
        )

    # Find appropriate age stage
    age_months = child.age_in_months
    result = await db.execute(
        select(AgeStage).where(
            AgeStage.min_age_months <= age_months,
            AgeStage.max_age_months > age_months,
        )
    )
    stage = result.scalar_one_or_none()

    if not stage:
        # Default to closest stage
        result = await db.execute(select(AgeStage).order_by(AgeStage.order.desc()).limit(1))
        stage = result.scalar_one_or_none()

    if not stage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No curriculum found for this age",
        )

    # Redirect to the age stage curriculum
    return {"child": child.name, "age_stage_slug": stage.slug, "redirect": f"/curriculum/{stage.slug}"}


@router.get("/activities/{activity_id}", response_model=ActivityResponse)
async def get_activity(
    activity_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific activity."""
    result = await db.execute(
        select(Activity)
        .options(selectinload(Activity.domain), selectinload(Activity.age_stage))
        .where(Activity.id == activity_id)
    )
    activity = result.scalar_one_or_none()

    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found",
        )

    return ActivityResponse(
        id=str(activity.id),
        title=activity.title,
        description=activity.description,
        instructions=activity.instructions,
        duration_minutes=activity.duration_minutes,
        materials_needed=activity.materials_needed,
        difficulty=activity.difficulty,
        week_number=activity.week_number,
        domain=DomainResponse(
            id=str(activity.domain.id),
            name=activity.domain.name,
            slug=activity.domain.slug,
            description=activity.domain.description,
            icon=activity.domain.icon,
            color=activity.domain.color,
        )
        if activity.domain
        else None,
        age_stage=AgeStageResponse(
            id=str(activity.age_stage.id),
            name=activity.age_stage.name,
            slug=activity.age_stage.slug,
            min_age_months=activity.age_stage.min_age_months,
            max_age_months=activity.age_stage.max_age_months,
            description=activity.age_stage.description,
            order=activity.age_stage.order,
        )
        if activity.age_stage
        else None,
    )
