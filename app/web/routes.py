"""Web routes for serving HTML pages."""

from uuid import UUID

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from sqlalchemy import func

from app.api.deps import get_current_user
from app.core.security import decode_token
from app.db.session import get_db
from app.models.chat import ChatSession
from app.models.child import Child
from app.models.curriculum import Activity, AgeStage, DevelopmentDomain, Milestone
from app.models.progress import ChildProgress
from app.models.resource import Resource
from app.models.bookmark import Bookmark
from app.models.user import User

router = APIRouter()

# Templates configuration
from pathlib import Path

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


def get_optional_user(request: Request):
    """Get current user if authenticated, otherwise None."""
    token = request.cookies.get("access_token")
    if not token:
        return None
    payload = decode_token(token)
    return payload


# Public pages
@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page - redirect to dashboard if logged in."""
    user = get_optional_user(request)
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse("pages/landing.html", {"request": request})


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page."""
    user = get_optional_user(request)
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse("pages/auth/login.html", {"request": request})


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Registration page."""
    user = get_optional_user(request)
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse("pages/auth/register.html", {"request": request})


@router.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_page(request: Request):
    """Forgot password page."""
    user = get_optional_user(request)
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse("pages/auth/forgot-password.html", {"request": request})


@router.get("/reset-password", response_class=HTMLResponse)
async def reset_password_page(request: Request, token: str | None = None):
    """Reset password page."""
    if not token:
        return RedirectResponse(url="/forgot-password", status_code=302)
    return templates.TemplateResponse(
        "pages/auth/reset-password.html",
        {"request": request, "token": token},
    )


@router.get("/verify-email", response_class=HTMLResponse)
async def verify_email_page(request: Request, token: str | None = None):
    """Email verification page."""
    return templates.TemplateResponse(
        "pages/auth/verify-email.html",
        {"request": request, "token": token},
    )


# Protected pages
@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Dashboard page."""
    return templates.TemplateResponse(
        "pages/dashboard.html",
        {"request": request, "current_user": current_user},
    )


@router.get("/chat", response_class=HTMLResponse)
async def chat_list_page(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Chat sessions list page."""
    return templates.TemplateResponse(
        "pages/chat/index.html",
        {"request": request, "current_user": current_user},
    )


@router.get("/chat/{session_id}", response_class=HTMLResponse)
async def chat_session_page(
    request: Request,
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Single chat session page."""
    result = await db.execute(
        select(ChatSession)
        .options(selectinload(ChatSession.messages))
        .where(
            ChatSession.id == session_id,
            ChatSession.family_id == current_user.family_id,
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        return RedirectResponse(url="/chat", status_code=302)

    # Get child if linked
    child = None
    if session.child_id:
        result = await db.execute(select(Child).where(Child.id == session.child_id))
        child = result.scalar_one_or_none()

    return templates.TemplateResponse(
        "pages/chat/session.html",
        {
            "request": request,
            "current_user": current_user,
            "session": session,
            "messages": session.messages,
            "child": child,
        },
    )


@router.get("/curriculum", response_class=HTMLResponse)
async def curriculum_page(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Curriculum browse page - list all age stages."""
    result = await db.execute(select(AgeStage).order_by(AgeStage.order))
    stages = result.scalars().all()

    # Get counts for each stage
    age_stages = []
    for stage in stages:
        milestone_count = await db.execute(
            select(func.count(Milestone.id)).where(Milestone.age_stage_id == stage.id)
        )
        activity_count = await db.execute(
            select(func.count(Activity.id)).where(Activity.age_stage_id == stage.id)
        )
        age_stages.append({
            "id": str(stage.id),
            "name": stage.name,
            "slug": stage.slug,
            "description": stage.description,
            "order": stage.order,
            "milestone_count": milestone_count.scalar() or 0,
            "activity_count": activity_count.scalar() or 0,
        })

    return templates.TemplateResponse(
        "pages/curriculum/index.html",
        {"request": request, "current_user": current_user, "age_stages": age_stages},
    )


@router.get("/curriculum/{stage_slug}", response_class=HTMLResponse)
async def curriculum_stage_page(
    request: Request,
    stage_slug: str,
    domain: str | None = None,
    child: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Curriculum page for a specific age stage."""
    # Get age stage
    result = await db.execute(select(AgeStage).where(AgeStage.slug == stage_slug))
    stage = result.scalar_one_or_none()

    if not stage:
        return RedirectResponse(url="/curriculum", status_code=302)

    # Get all children for the family
    result = await db.execute(
        select(Child)
        .where(Child.family_id == current_user.family_id, Child.is_active == True)
        .order_by(Child.name)
    )
    children = result.scalars().all()

    # Get selected child if provided
    selected_child = None
    child_progress = {}
    if child:
        result = await db.execute(
            select(Child).where(
                Child.id == UUID(child),
                Child.family_id == current_user.family_id,
            )
        )
        selected_child = result.scalar_one_or_none()

        # Get progress for this child
        if selected_child:
            result = await db.execute(
                select(ChildProgress).where(ChildProgress.child_id == selected_child.id)
            )
            progress_entries = result.scalars().all()
            for entry in progress_entries:
                if entry.milestone_id:
                    child_progress[str(entry.milestone_id)] = entry
                if entry.activity_id:
                    child_progress[str(entry.activity_id)] = entry

    # Get all domains
    result = await db.execute(select(DevelopmentDomain).order_by(DevelopmentDomain.name))
    domains = result.scalars().all()

    # Build queries with optional domain filter
    milestone_query = (
        select(Milestone)
        .options(selectinload(Milestone.domain))
        .where(Milestone.age_stage_id == stage.id, Milestone.is_active == True)
    )
    activity_query = (
        select(Activity)
        .options(selectinload(Activity.domain))
        .where(Activity.age_stage_id == stage.id, Activity.is_active == True)
    )

    if domain:
        result = await db.execute(
            select(DevelopmentDomain).where(DevelopmentDomain.slug == domain)
        )
        domain_obj = result.scalar_one_or_none()
        if domain_obj:
            milestone_query = milestone_query.where(Milestone.domain_id == domain_obj.id)
            activity_query = activity_query.where(Activity.domain_id == domain_obj.id)

    result = await db.execute(milestone_query.order_by(Milestone.typical_age_months))
    milestones = result.scalars().all()

    result = await db.execute(activity_query.order_by(Activity.title))
    activities = result.scalars().all()

    return templates.TemplateResponse(
        "pages/curriculum/stage.html",
        {
            "request": request,
            "current_user": current_user,
            "stage": stage,
            "domains": domains,
            "milestones": milestones,
            "activities": activities,
            "selected_domain": domain,
            "children": children,
            "selected_child": selected_child,
            "child_progress": child_progress,
        },
    )


@router.get("/progress/{child_id}", response_class=HTMLResponse)
async def child_progress_page(
    request: Request,
    child_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Progress dashboard for a specific child."""
    # Get child
    result = await db.execute(
        select(Child).where(
            Child.id == child_id,
            Child.family_id == current_user.family_id,
        )
    )
    child = result.scalar_one_or_none()

    if not child:
        return RedirectResponse(url="/dashboard", status_code=302)

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
        result = await db.execute(select(AgeStage).order_by(AgeStage.order).limit(1))
        age_stage = result.scalar_one_or_none()

    # Calculate stats
    from app.schemas.progress import DomainProgressResponse, ProgressStatsResponse

    result = await db.execute(select(DevelopmentDomain))
    domains = result.scalars().all()

    total_milestones = 0
    completed_milestones = 0
    total_activities = 0
    completed_activities = 0
    by_domain = []

    for domain in domains:
        if age_stage:
            m_count = await db.execute(
                select(func.count(Milestone.id)).where(
                    Milestone.age_stage_id == age_stage.id,
                    Milestone.domain_id == domain.id,
                    Milestone.is_active == True,
                )
            )
            domain_milestones = m_count.scalar() or 0

            a_count = await db.execute(
                select(func.count(Activity.id)).where(
                    Activity.age_stage_id == age_stage.id,
                    Activity.domain_id == domain.id,
                    Activity.is_active == True,
                )
            )
            domain_activities = a_count.scalar() or 0
        else:
            domain_milestones = 0
            domain_activities = 0

        comp_m = await db.execute(
            select(func.count(ChildProgress.id))
            .join(Milestone)
            .where(
                ChildProgress.child_id == child_id,
                ChildProgress.status == "completed",
                Milestone.domain_id == domain.id,
            )
        )
        domain_completed_m = comp_m.scalar() or 0

        comp_a = await db.execute(
            select(func.count(ChildProgress.id))
            .join(Activity)
            .where(
                ChildProgress.child_id == child_id,
                ChildProgress.status == "completed",
                Activity.domain_id == domain.id,
            )
        )
        domain_completed_a = comp_a.scalar() or 0

        total_milestones += domain_milestones
        completed_milestones += domain_completed_m
        total_activities += domain_activities
        completed_activities += domain_completed_a

        total_domain = domain_milestones + domain_activities
        completed_domain = domain_completed_m + domain_completed_a
        percentage = (completed_domain / total_domain * 100) if total_domain > 0 else 0

        by_domain.append({
            "domain_id": str(domain.id),
            "domain_name": domain.name,
            "domain_color": domain.color or "#6B7280",
            "total_milestones": domain_milestones,
            "completed_milestones": domain_completed_m,
            "total_activities": domain_activities,
            "completed_activities": domain_completed_a,
            "percentage": round(percentage, 1),
        })

    milestone_pct = (completed_milestones / total_milestones * 100) if total_milestones > 0 else 0
    activity_pct = (completed_activities / total_activities * 100) if total_activities > 0 else 0

    stats = {
        "child_id": str(child.id),
        "child_name": child.name,
        "total_milestones": total_milestones,
        "completed_milestones": completed_milestones,
        "total_activities": total_activities,
        "completed_activities": completed_activities,
        "milestone_percentage": round(milestone_pct, 1),
        "activity_percentage": round(activity_pct, 1),
        "by_domain": by_domain,
    }

    # Get recent progress
    result = await db.execute(
        select(ChildProgress)
        .where(ChildProgress.child_id == child_id)
        .order_by(ChildProgress.updated_at.desc())
        .limit(10)
    )
    progress_entries = result.scalars().all()

    recent_progress = []
    for entry in progress_entries:
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
            recent_progress.append({
                "id": str(entry.id),
                "title": title,
                "type": entry_type,
                "status": entry.status,
                "completed_at": entry.completed_at,
                "domain_name": domain_name,
                "domain_color": domain_color,
                "notes": entry.notes,
            })

    return templates.TemplateResponse(
        "pages/progress/child.html",
        {
            "request": request,
            "current_user": current_user,
            "child": child,
            "age_stage": age_stage,
            "stats": stats,
            "recent_progress": recent_progress,
        },
    )


@router.get("/interests", response_class=HTMLResponse)
async def interests_page(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Interest Discovery page."""
    return templates.TemplateResponse(
        "pages/interests/index.html",
        {"request": request, "current_user": current_user},
    )


@router.get("/roadmap", response_class=HTMLResponse)
async def roadmap_page(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """12-Week Roadmap page."""
    return templates.TemplateResponse(
        "pages/roadmap/index.html",
        {"request": request, "current_user": current_user},
    )


@router.get("/resources", response_class=HTMLResponse)
async def resources_page(
    request: Request,
    resource_type: str | None = None,
    age_stage: str | None = None,
    domain: str | None = None,
    tag: str | None = None,
    search: str | None = None,
    bookmarked: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Resources page."""
    # Get all age stages for filter
    result = await db.execute(select(AgeStage).order_by(AgeStage.order))
    age_stages = result.scalars().all()

    # Get all domains for filter
    result = await db.execute(select(DevelopmentDomain).order_by(DevelopmentDomain.name))
    domains = result.scalars().all()

    # Get all unique tags from resources
    result = await db.execute(select(Resource.tags).where(Resource.tags.isnot(None)))
    all_tags = set()
    for row in result.scalars().all():
        if row:
            all_tags.update(row)
    tags = sorted(all_tags)

    # Resource types
    resource_types = [
        {"value": "article", "label": "Articles"},
        {"value": "video", "label": "Videos"},
        {"value": "guide", "label": "Guides"},
        {"value": "tool", "label": "Tools"},
        {"value": "book", "label": "Books"},
    ]

    return templates.TemplateResponse(
        "pages/resources/index.html",
        {
            "request": request,
            "current_user": current_user,
            "age_stages": age_stages,
            "domains": domains,
            "tags": tags,
            "resource_types": resource_types,
            "selected_type": resource_type,
            "selected_age_stage": age_stage,
            "selected_domain": domain,
            "selected_tag": tag,
            "search_query": search,
            "bookmarked_only": bookmarked,
        },
    )
