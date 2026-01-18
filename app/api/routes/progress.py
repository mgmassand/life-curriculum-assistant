"""Progress tracking routes."""

from datetime import datetime
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.templating import Jinja2Templates
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.child import Child
from app.models.curriculum import Activity, AgeStage, DevelopmentDomain, Milestone
from app.models.progress import ChildProgress
from app.models.user import User
from app.schemas.progress import (
    DomainProgressResponse,
    ProgressCreate,
    ProgressResponse,
    ProgressStatsResponse,
    ProgressUpdate,
    RecentProgressResponse,
)

router = APIRouter(prefix="/progress", tags=["progress"])

templates = Jinja2Templates(
    directory=str(Path(__file__).parent.parent.parent / "web" / "templates")
)


@router.post("", response_model=ProgressResponse, status_code=status.HTTP_201_CREATED)
async def create_progress(
    data: ProgressCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Record progress for a milestone or activity."""
    # Verify child belongs to user's family
    result = await db.execute(
        select(Child).where(
            Child.id == UUID(data.child_id),
            Child.family_id == current_user.family_id,
        )
    )
    child = result.scalar_one_or_none()
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")

    # Validate that either milestone_id or activity_id is provided
    if not data.milestone_id and not data.activity_id:
        raise HTTPException(
            status_code=400,
            detail="Either milestone_id or activity_id is required",
        )
    if data.milestone_id and data.activity_id:
        raise HTTPException(
            status_code=400,
            detail="Only one of milestone_id or activity_id should be provided",
        )

    # Check for existing progress
    existing_query = select(ChildProgress).where(ChildProgress.child_id == UUID(data.child_id))
    if data.milestone_id:
        existing_query = existing_query.where(
            ChildProgress.milestone_id == UUID(data.milestone_id)
        )
    else:
        existing_query = existing_query.where(
            ChildProgress.activity_id == UUID(data.activity_id)
        )

    result = await db.execute(existing_query)
    existing = result.scalar_one_or_none()

    if existing:
        # Update existing progress
        existing.status = data.status
        existing.notes = data.notes or existing.notes
        existing.rating = data.rating or existing.rating
        if data.status == "completed" and not existing.completed_at:
            existing.completed_at = datetime.utcnow()
        progress = existing
    else:
        # Create new progress
        progress = ChildProgress(
            child_id=UUID(data.child_id),
            milestone_id=UUID(data.milestone_id) if data.milestone_id else None,
            activity_id=UUID(data.activity_id) if data.activity_id else None,
            status=data.status,
            notes=data.notes,
            rating=data.rating,
            recorded_by_id=current_user.id,
            completed_at=datetime.utcnow() if data.status == "completed" else None,
        )
        db.add(progress)

    await db.commit()
    await db.refresh(progress)

    # Get related data for response
    milestone_title = None
    activity_title = None
    domain_name = None
    domain_color = None

    if progress.milestone_id:
        result = await db.execute(
            select(Milestone)
            .options(selectinload(Milestone.domain))
            .where(Milestone.id == progress.milestone_id)
        )
        milestone = result.scalar_one_or_none()
        if milestone:
            milestone_title = milestone.title
            domain_name = milestone.domain.name
            domain_color = milestone.domain.color

    if progress.activity_id:
        result = await db.execute(
            select(Activity)
            .options(selectinload(Activity.domain))
            .where(Activity.id == progress.activity_id)
        )
        activity = result.scalar_one_or_none()
        if activity:
            activity_title = activity.title
            domain_name = activity.domain.name
            domain_color = activity.domain.color

    return ProgressResponse(
        id=str(progress.id),
        child_id=str(progress.child_id),
        milestone_id=str(progress.milestone_id) if progress.milestone_id else None,
        activity_id=str(progress.activity_id) if progress.activity_id else None,
        status=progress.status,
        completed_at=progress.completed_at,
        notes=progress.notes,
        rating=progress.rating,
        created_at=progress.created_at,
        updated_at=progress.updated_at,
        milestone_title=milestone_title,
        activity_title=activity_title,
        domain_name=domain_name,
        domain_color=domain_color,
    )


@router.get("/child/{child_id}", response_model=list[ProgressResponse])
async def get_child_progress(
    child_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all progress entries for a child."""
    # Verify child access
    result = await db.execute(
        select(Child).where(
            Child.id == child_id,
            Child.family_id == current_user.family_id,
        )
    )
    child = result.scalar_one_or_none()
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")

    # Get progress entries
    result = await db.execute(
        select(ChildProgress)
        .where(ChildProgress.child_id == child_id)
        .order_by(ChildProgress.updated_at.desc())
    )
    entries = result.scalars().all()

    response = []
    for entry in entries:
        milestone_title = None
        activity_title = None
        domain_name = None
        domain_color = None

        if entry.milestone_id:
            result = await db.execute(
                select(Milestone)
                .options(selectinload(Milestone.domain))
                .where(Milestone.id == entry.milestone_id)
            )
            milestone = result.scalar_one_or_none()
            if milestone:
                milestone_title = milestone.title
                domain_name = milestone.domain.name
                domain_color = milestone.domain.color

        if entry.activity_id:
            result = await db.execute(
                select(Activity)
                .options(selectinload(Activity.domain))
                .where(Activity.id == entry.activity_id)
            )
            activity = result.scalar_one_or_none()
            if activity:
                activity_title = activity.title
                domain_name = activity.domain.name
                domain_color = activity.domain.color

        response.append(
            ProgressResponse(
                id=str(entry.id),
                child_id=str(entry.child_id),
                milestone_id=str(entry.milestone_id) if entry.milestone_id else None,
                activity_id=str(entry.activity_id) if entry.activity_id else None,
                status=entry.status,
                completed_at=entry.completed_at,
                notes=entry.notes,
                rating=entry.rating,
                created_at=entry.created_at,
                updated_at=entry.updated_at,
                milestone_title=milestone_title,
                activity_title=activity_title,
                domain_name=domain_name,
                domain_color=domain_color,
            )
        )

    return response


@router.get("/child/{child_id}/stats", response_model=ProgressStatsResponse)
async def get_child_progress_stats(
    child_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get progress statistics for a child."""
    # Verify child access
    result = await db.execute(
        select(Child).where(
            Child.id == child_id,
            Child.family_id == current_user.family_id,
        )
    )
    child = result.scalar_one_or_none()
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")

    # Find child's age stage
    age_months = child.age_in_months
    result = await db.execute(
        select(AgeStage).where(
            AgeStage.min_age_months <= age_months,
            AgeStage.max_age_months > age_months,
        )
    )
    age_stage = result.scalar_one_or_none()

    if not age_stage:
        # Default to first stage if age doesn't match
        result = await db.execute(select(AgeStage).order_by(AgeStage.order).limit(1))
        age_stage = result.scalar_one_or_none()

    # Get domains
    result = await db.execute(select(DevelopmentDomain))
    domains = result.scalars().all()

    # Calculate stats
    total_milestones = 0
    completed_milestones = 0
    total_activities = 0
    completed_activities = 0
    by_domain = []

    for domain in domains:
        # Count milestones for this domain in child's age stage
        if age_stage:
            milestone_count_result = await db.execute(
                select(func.count(Milestone.id)).where(
                    Milestone.age_stage_id == age_stage.id,
                    Milestone.domain_id == domain.id,
                    Milestone.is_active == True,
                )
            )
            domain_milestones = milestone_count_result.scalar() or 0

            activity_count_result = await db.execute(
                select(func.count(Activity.id)).where(
                    Activity.age_stage_id == age_stage.id,
                    Activity.domain_id == domain.id,
                    Activity.is_active == True,
                )
            )
            domain_activities = activity_count_result.scalar() or 0
        else:
            domain_milestones = 0
            domain_activities = 0

        # Count completed for this domain
        completed_m_result = await db.execute(
            select(func.count(ChildProgress.id))
            .join(Milestone)
            .where(
                ChildProgress.child_id == child_id,
                ChildProgress.status == "completed",
                Milestone.domain_id == domain.id,
            )
        )
        domain_completed_m = completed_m_result.scalar() or 0

        completed_a_result = await db.execute(
            select(func.count(ChildProgress.id))
            .join(Activity)
            .where(
                ChildProgress.child_id == child_id,
                ChildProgress.status == "completed",
                Activity.domain_id == domain.id,
            )
        )
        domain_completed_a = completed_a_result.scalar() or 0

        total_milestones += domain_milestones
        completed_milestones += domain_completed_m
        total_activities += domain_activities
        completed_activities += domain_completed_a

        total_domain = domain_milestones + domain_activities
        completed_domain = domain_completed_m + domain_completed_a
        percentage = (completed_domain / total_domain * 100) if total_domain > 0 else 0

        by_domain.append(
            DomainProgressResponse(
                domain_id=str(domain.id),
                domain_name=domain.name,
                domain_color=domain.color or "#6B7280",
                total_milestones=domain_milestones,
                completed_milestones=domain_completed_m,
                total_activities=domain_activities,
                completed_activities=domain_completed_a,
                percentage=round(percentage, 1),
            )
        )

    milestone_percentage = (
        (completed_milestones / total_milestones * 100) if total_milestones > 0 else 0
    )
    activity_percentage = (
        (completed_activities / total_activities * 100) if total_activities > 0 else 0
    )

    return ProgressStatsResponse(
        child_id=str(child.id),
        child_name=child.name,
        total_milestones=total_milestones,
        completed_milestones=completed_milestones,
        total_activities=total_activities,
        completed_activities=completed_activities,
        milestone_percentage=round(milestone_percentage, 1),
        activity_percentage=round(activity_percentage, 1),
        by_domain=by_domain,
    )


@router.get("/child/{child_id}/recent", response_model=list[RecentProgressResponse])
async def get_recent_progress(
    child_id: UUID,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get recent progress entries for a child."""
    # Verify child access
    result = await db.execute(
        select(Child).where(
            Child.id == child_id,
            Child.family_id == current_user.family_id,
        )
    )
    child = result.scalar_one_or_none()
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")

    # Get recent progress
    result = await db.execute(
        select(ChildProgress)
        .where(ChildProgress.child_id == child_id)
        .order_by(ChildProgress.updated_at.desc())
        .limit(limit)
    )
    entries = result.scalars().all()

    response = []
    for entry in entries:
        title = ""
        entry_type = ""
        domain_name = ""
        domain_color = "#6B7280"

        if entry.milestone_id:
            result = await db.execute(
                select(Milestone)
                .options(selectinload(Milestone.domain))
                .where(Milestone.id == entry.milestone_id)
            )
            milestone = result.scalar_one_or_none()
            if milestone:
                title = milestone.title
                entry_type = "milestone"
                domain_name = milestone.domain.name
                domain_color = milestone.domain.color or "#6B7280"

        elif entry.activity_id:
            result = await db.execute(
                select(Activity)
                .options(selectinload(Activity.domain))
                .where(Activity.id == entry.activity_id)
            )
            activity = result.scalar_one_or_none()
            if activity:
                title = activity.title
                entry_type = "activity"
                domain_name = activity.domain.name
                domain_color = activity.domain.color or "#6B7280"

        if title:
            response.append(
                RecentProgressResponse(
                    id=str(entry.id),
                    title=title,
                    type=entry_type,
                    status=entry.status,
                    completed_at=entry.completed_at,
                    domain_name=domain_name,
                    domain_color=domain_color,
                    notes=entry.notes,
                )
            )

    return response


@router.patch("/{progress_id}", response_model=ProgressResponse)
async def update_progress(
    progress_id: UUID,
    data: ProgressUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a progress entry."""
    # Get progress and verify access through child
    result = await db.execute(
        select(ChildProgress)
        .options(selectinload(ChildProgress.child))
        .where(ChildProgress.id == progress_id)
    )
    progress = result.scalar_one_or_none()

    if not progress or progress.child.family_id != current_user.family_id:
        raise HTTPException(status_code=404, detail="Progress entry not found")

    # Update fields
    if data.status is not None:
        progress.status = data.status
        if data.status == "completed" and not progress.completed_at:
            progress.completed_at = datetime.utcnow()
    if data.notes is not None:
        progress.notes = data.notes
    if data.rating is not None:
        progress.rating = data.rating

    await db.commit()
    await db.refresh(progress)

    # Get related data
    milestone_title = None
    activity_title = None
    domain_name = None
    domain_color = None

    if progress.milestone_id:
        result = await db.execute(
            select(Milestone)
            .options(selectinload(Milestone.domain))
            .where(Milestone.id == progress.milestone_id)
        )
        milestone = result.scalar_one_or_none()
        if milestone:
            milestone_title = milestone.title
            domain_name = milestone.domain.name
            domain_color = milestone.domain.color

    if progress.activity_id:
        result = await db.execute(
            select(Activity)
            .options(selectinload(Activity.domain))
            .where(Activity.id == progress.activity_id)
        )
        activity = result.scalar_one_or_none()
        if activity:
            activity_title = activity.title
            domain_name = activity.domain.name
            domain_color = activity.domain.color

    return ProgressResponse(
        id=str(progress.id),
        child_id=str(progress.child_id),
        milestone_id=str(progress.milestone_id) if progress.milestone_id else None,
        activity_id=str(progress.activity_id) if progress.activity_id else None,
        status=progress.status,
        completed_at=progress.completed_at,
        notes=progress.notes,
        rating=progress.rating,
        created_at=progress.created_at,
        updated_at=progress.updated_at,
        milestone_title=milestone_title,
        activity_title=activity_title,
        domain_name=domain_name,
        domain_color=domain_color,
    )


@router.delete("/{progress_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_progress(
    progress_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a progress entry."""
    result = await db.execute(
        select(ChildProgress)
        .options(selectinload(ChildProgress.child))
        .where(ChildProgress.id == progress_id)
    )
    progress = result.scalar_one_or_none()

    if not progress or progress.child.family_id != current_user.family_id:
        raise HTTPException(status_code=404, detail="Progress entry not found")

    await db.delete(progress)
    await db.commit()
