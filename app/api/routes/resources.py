"""Resource routes for browsing and bookmarking educational content."""

from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.bookmark import Bookmark
from app.models.curriculum import AgeStage, DevelopmentDomain
from app.models.resource import Resource
from app.models.user import User
from app.schemas.resource import (
    BookmarkResponse,
    ResourceCreate,
    ResourceListResponse,
    ResourceResponse,
    ResourceUpdate,
)

router = APIRouter(prefix="/resources", tags=["resources"])

templates = Jinja2Templates(
    directory=str(Path(__file__).parent.parent.parent / "web" / "templates")
)


async def get_resource_response(
    resource: Resource,
    db: AsyncSession,
    user_id: UUID | None = None,
) -> ResourceResponse:
    """Build a resource response with resolved names and bookmark status."""
    # Resolve age stage names
    age_stage_names = []
    if resource.age_stage_ids:
        for stage_id in resource.age_stage_ids:
            result = await db.execute(
                select(AgeStage.name).where(AgeStage.id == UUID(stage_id))
            )
            name = result.scalar_one_or_none()
            if name:
                age_stage_names.append(name)

    # Resolve domain names
    domain_names = []
    if resource.domain_ids:
        for domain_id in resource.domain_ids:
            result = await db.execute(
                select(DevelopmentDomain.name).where(
                    DevelopmentDomain.id == UUID(domain_id)
                )
            )
            name = result.scalar_one_or_none()
            if name:
                domain_names.append(name)

    # Check bookmark status
    is_bookmarked = False
    if user_id:
        result = await db.execute(
            select(Bookmark.id).where(
                Bookmark.user_id == user_id,
                Bookmark.resource_id == resource.id,
            )
        )
        is_bookmarked = result.scalar_one_or_none() is not None

    return ResourceResponse(
        id=str(resource.id),
        title=resource.title,
        description=resource.description,
        resource_type=resource.resource_type,
        url=resource.url,
        content=resource.content,
        thumbnail_url=resource.thumbnail_url,
        age_stage_ids=[str(id) for id in resource.age_stage_ids]
        if resource.age_stage_ids
        else None,
        domain_ids=[str(id) for id in resource.domain_ids]
        if resource.domain_ids
        else None,
        tags=resource.tags,
        is_premium=resource.is_premium,
        is_featured=resource.is_featured,
        view_count=resource.view_count,
        created_at=resource.created_at,
        is_bookmarked=is_bookmarked,
        age_stage_names=age_stage_names if age_stage_names else None,
        domain_names=domain_names if domain_names else None,
    )


@router.get("", response_model=ResourceListResponse)
async def list_resources(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=50),
    resource_type: str | None = None,
    age_stage: str | None = None,
    domain: str | None = None,
    tag: str | None = None,
    search: str | None = None,
    featured_only: bool = False,
    bookmarked_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List resources with filtering and pagination."""
    query = select(Resource)

    # Apply filters
    if resource_type:
        query = query.where(Resource.resource_type == resource_type)

    if age_stage:
        # Get age stage ID from slug
        result = await db.execute(
            select(AgeStage.id).where(AgeStage.slug == age_stage)
        )
        stage_id = result.scalar_one_or_none()
        if stage_id:
            query = query.where(
                Resource.age_stage_ids.contains([str(stage_id)])
            )

    if domain:
        # Get domain ID from slug
        result = await db.execute(
            select(DevelopmentDomain.id).where(DevelopmentDomain.slug == domain)
        )
        domain_id = result.scalar_one_or_none()
        if domain_id:
            query = query.where(Resource.domain_ids.contains([str(domain_id)]))

    if tag:
        query = query.where(Resource.tags.contains([tag]))

    if search:
        search_term = f"%{search}%"
        query = query.where(
            (Resource.title.ilike(search_term))
            | (Resource.description.ilike(search_term))
        )

    if featured_only:
        query = query.where(Resource.is_featured == True)

    if bookmarked_only:
        # Join with bookmarks
        query = query.join(Bookmark).where(Bookmark.user_id == current_user.id)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    result = await db.execute(count_query)
    total = result.scalar() or 0

    # Apply pagination and ordering
    query = query.order_by(Resource.is_featured.desc(), Resource.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    resources = result.scalars().all()

    # Build response
    resource_responses = []
    for resource in resources:
        response = await get_resource_response(resource, db, current_user.id)
        resource_responses.append(response)

    total_pages = (total + page_size - 1) // page_size

    # Return HTML for HTMX requests
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            "partials/resources_list.html",
            {
                "request": request,
                "resources": resource_responses,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
            },
        )

    return ResourceListResponse(
        resources=resource_responses,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/featured", response_model=list[ResourceResponse])
async def get_featured_resources(
    limit: int = Query(6, ge=1, le=20),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get featured resources for homepage display."""
    result = await db.execute(
        select(Resource)
        .where(Resource.is_featured == True)
        .order_by(Resource.created_at.desc())
        .limit(limit)
    )
    resources = result.scalars().all()

    responses = []
    for resource in resources:
        response = await get_resource_response(resource, db, current_user.id)
        responses.append(response)

    return responses


@router.get("/{resource_id}", response_model=ResourceResponse)
async def get_resource(
    resource_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single resource and increment view count."""
    result = await db.execute(select(Resource).where(Resource.id == resource_id))
    resource = result.scalar_one_or_none()

    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    # Increment view count
    resource.view_count += 1
    await db.commit()

    return await get_resource_response(resource, db, current_user.id)


# Bookmark routes
@router.post("/{resource_id}/bookmark", response_model=BookmarkResponse)
async def bookmark_resource(
    resource_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Bookmark a resource."""
    # Verify resource exists
    result = await db.execute(select(Resource).where(Resource.id == resource_id))
    resource = result.scalar_one_or_none()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    # Check if already bookmarked
    result = await db.execute(
        select(Bookmark).where(
            Bookmark.user_id == current_user.id,
            Bookmark.resource_id == resource_id,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        return BookmarkResponse(
            id=str(existing.id),
            resource_id=str(existing.resource_id),
            created_at=existing.created_at,
        )

    # Create bookmark
    bookmark = Bookmark(user_id=current_user.id, resource_id=resource_id)
    db.add(bookmark)
    await db.commit()
    await db.refresh(bookmark)

    return BookmarkResponse(
        id=str(bookmark.id),
        resource_id=str(bookmark.resource_id),
        created_at=bookmark.created_at,
    )


@router.delete("/{resource_id}/bookmark", status_code=status.HTTP_204_NO_CONTENT)
async def unbookmark_resource(
    resource_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a bookmark from a resource."""
    result = await db.execute(
        select(Bookmark).where(
            Bookmark.user_id == current_user.id,
            Bookmark.resource_id == resource_id,
        )
    )
    bookmark = result.scalar_one_or_none()

    if bookmark:
        await db.delete(bookmark)
        await db.commit()


@router.get("/bookmarks/all", response_model=list[ResourceResponse])
async def get_bookmarked_resources(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all bookmarked resources for the current user."""
    result = await db.execute(
        select(Resource)
        .join(Bookmark)
        .where(Bookmark.user_id == current_user.id)
        .order_by(Bookmark.created_at.desc())
    )
    resources = result.scalars().all()

    responses = []
    for resource in resources:
        response = await get_resource_response(resource, db, current_user.id)
        responses.append(response)

    return responses
