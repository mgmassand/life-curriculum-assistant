"""Children routes."""

from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.child import Child
from app.models.curriculum import Activity, AgeStage, Milestone
from app.models.progress import ChildProgress
from app.models.user import User
from app.schemas.child import ChildCreate, ChildResponse, ChildUpdate

router = APIRouter(prefix="/children", tags=["children"])

# Templates for HTMX responses
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent.parent / "web" / "templates"))


@router.get("")
async def list_children(
    request: Request,
    format: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all children in the user's family."""
    result = await db.execute(
        select(Child)
        .where(Child.family_id == current_user.family_id, Child.is_active == True)
        .order_by(Child.date_of_birth)
    )
    children = result.scalars().all()

    # Return HTML for HTMX requests
    if request.headers.get("HX-Request"):
        # Calculate progress stats for each child
        children_with_stats = []
        for child in children:
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
                result = await db.execute(
                    select(AgeStage).order_by(AgeStage.order).limit(1)
                )
                age_stage = result.scalar_one_or_none()

            # Count total and completed milestones/activities
            total_milestones = 0
            total_activities = 0
            if age_stage:
                m_count = await db.execute(
                    select(func.count(Milestone.id)).where(
                        Milestone.age_stage_id == age_stage.id,
                        Milestone.is_active == True,
                    )
                )
                total_milestones = m_count.scalar() or 0

                a_count = await db.execute(
                    select(func.count(Activity.id)).where(
                        Activity.age_stage_id == age_stage.id,
                        Activity.is_active == True,
                    )
                )
                total_activities = a_count.scalar() or 0

            # Count completed
            comp_m = await db.execute(
                select(func.count(ChildProgress.id)).where(
                    ChildProgress.child_id == child.id,
                    ChildProgress.milestone_id.isnot(None),
                    ChildProgress.status == "completed",
                )
            )
            completed_milestones = comp_m.scalar() or 0

            comp_a = await db.execute(
                select(func.count(ChildProgress.id)).where(
                    ChildProgress.child_id == child.id,
                    ChildProgress.activity_id.isnot(None),
                    ChildProgress.status == "completed",
                )
            )
            completed_activities = comp_a.scalar() or 0

            total = total_milestones + total_activities
            completed = completed_milestones + completed_activities
            percentage = (completed / total * 100) if total > 0 else 0

            children_with_stats.append({
                "child": child,
                "age_stage": age_stage,
                "total_milestones": total_milestones,
                "completed_milestones": completed_milestones,
                "total_activities": total_activities,
                "completed_activities": completed_activities,
                "total": total,
                "completed": completed,
                "percentage": round(percentage, 1),
            })

        # Use selector template if requested
        template_name = "partials/child_selector.html" if format == "selector" else "partials/children_list.html"
        return templates.TemplateResponse(
            template_name,
            {"request": request, "children_data": children_with_stats},
        )

    # Return JSON for API requests
    return [
        ChildResponse(
            id=str(child.id),
            family_id=str(child.family_id),
            name=child.name,
            date_of_birth=child.date_of_birth,
            gender=child.gender,
            notes=child.notes,
            avatar_url=child.avatar_url,
            is_active=child.is_active,
            created_at=child.created_at,
            age_in_months=child.age_in_months,
            age_description=child.age_description,
        )
        for child in children
    ]


@router.post("", response_model=ChildResponse, status_code=status.HTTP_201_CREATED)
async def create_child(
    data: ChildCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new child in the user's family."""
    child = Child(
        family_id=current_user.family_id,
        name=data.name,
        date_of_birth=data.date_of_birth,
        gender=data.gender,
        notes=data.notes,
    )
    db.add(child)
    await db.commit()
    await db.refresh(child)

    return ChildResponse(
        id=str(child.id),
        family_id=str(child.family_id),
        name=child.name,
        date_of_birth=child.date_of_birth,
        gender=child.gender,
        notes=child.notes,
        avatar_url=child.avatar_url,
        is_active=child.is_active,
        created_at=child.created_at,
        age_in_months=child.age_in_months,
        age_description=child.age_description,
    )


@router.get("/{child_id}", response_model=ChildResponse)
async def get_child(
    child_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific child."""
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

    return ChildResponse(
        id=str(child.id),
        family_id=str(child.family_id),
        name=child.name,
        date_of_birth=child.date_of_birth,
        gender=child.gender,
        notes=child.notes,
        avatar_url=child.avatar_url,
        is_active=child.is_active,
        created_at=child.created_at,
        age_in_months=child.age_in_months,
        age_description=child.age_description,
    )


@router.patch("/{child_id}", response_model=ChildResponse)
async def update_child(
    child_id: UUID,
    data: ChildUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a child's information."""
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

    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(child, field, value)

    await db.commit()
    await db.refresh(child)

    return ChildResponse(
        id=str(child.id),
        family_id=str(child.family_id),
        name=child.name,
        date_of_birth=child.date_of_birth,
        gender=child.gender,
        notes=child.notes,
        avatar_url=child.avatar_url,
        is_active=child.is_active,
        created_at=child.created_at,
        age_in_months=child.age_in_months,
        age_description=child.age_description,
    )


@router.delete("/{child_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_child(
    child_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Soft delete a child."""
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

    child.is_active = False
    await db.commit()
