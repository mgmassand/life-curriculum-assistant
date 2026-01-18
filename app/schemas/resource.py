"""Resource schemas for API validation."""

from datetime import datetime

from pydantic import BaseModel, Field


class ResourceResponse(BaseModel):
    """Resource response schema."""

    id: str
    title: str
    description: str
    resource_type: str
    url: str | None = None
    content: str | None = None
    thumbnail_url: str | None = None
    age_stage_ids: list[str] | None = None
    domain_ids: list[str] | None = None
    tags: list[str] | None = None
    is_premium: bool = False
    is_featured: bool = False
    view_count: int = 0
    created_at: datetime
    is_bookmarked: bool = False

    # Resolved names for display
    age_stage_names: list[str] | None = None
    domain_names: list[str] | None = None

    model_config = {"from_attributes": True}


class ResourceListResponse(BaseModel):
    """Paginated resource list response."""

    resources: list[ResourceResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ResourceCreate(BaseModel):
    """Resource creation schema (admin only)."""

    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    resource_type: str = Field(..., pattern="^(article|video|guide|tool|book)$")
    url: str | None = None
    content: str | None = None
    thumbnail_url: str | None = None
    age_stage_ids: list[str] | None = None
    domain_ids: list[str] | None = None
    tags: list[str] | None = None
    is_premium: bool = False
    is_featured: bool = False


class ResourceUpdate(BaseModel):
    """Resource update schema (admin only)."""

    title: str | None = None
    description: str | None = None
    resource_type: str | None = None
    url: str | None = None
    content: str | None = None
    thumbnail_url: str | None = None
    age_stage_ids: list[str] | None = None
    domain_ids: list[str] | None = None
    tags: list[str] | None = None
    is_premium: bool | None = None
    is_featured: bool | None = None


class BookmarkResponse(BaseModel):
    """Bookmark response schema."""

    id: str
    resource_id: str
    created_at: datetime

    model_config = {"from_attributes": True}
