"""Progress tracking schemas."""

from datetime import datetime

from pydantic import BaseModel


class ProgressCreate(BaseModel):
    """Schema for creating a progress entry."""

    child_id: str
    milestone_id: str | None = None
    activity_id: str | None = None
    status: str = "completed"  # not_started, in_progress, completed, skipped
    notes: str | None = None
    rating: int | None = None  # 1-5


class ProgressUpdate(BaseModel):
    """Schema for updating a progress entry."""

    status: str | None = None
    notes: str | None = None
    rating: int | None = None


class ProgressResponse(BaseModel):
    """Progress entry response."""

    id: str
    child_id: str
    milestone_id: str | None
    activity_id: str | None
    status: str
    completed_at: datetime | None
    notes: str | None
    rating: int | None
    created_at: datetime
    updated_at: datetime

    # Related data
    milestone_title: str | None = None
    activity_title: str | None = None
    domain_name: str | None = None
    domain_color: str | None = None

    class Config:
        from_attributes = True


class ProgressStatsResponse(BaseModel):
    """Progress statistics for a child."""

    child_id: str
    child_name: str
    total_milestones: int
    completed_milestones: int
    total_activities: int
    completed_activities: int
    milestone_percentage: float
    activity_percentage: float
    by_domain: list["DomainProgressResponse"]


class DomainProgressResponse(BaseModel):
    """Progress stats by domain."""

    domain_id: str
    domain_name: str
    domain_color: str
    total_milestones: int
    completed_milestones: int
    total_activities: int
    completed_activities: int
    percentage: float


class RecentProgressResponse(BaseModel):
    """Recent progress entry for display."""

    id: str
    title: str
    type: str  # milestone or activity
    status: str
    completed_at: datetime | None
    domain_name: str
    domain_color: str
    notes: str | None
