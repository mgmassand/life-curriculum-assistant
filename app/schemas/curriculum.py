"""Curriculum schemas."""

from datetime import datetime

from pydantic import BaseModel


class DomainResponse(BaseModel):
    """Development domain response."""

    id: str
    name: str
    slug: str
    description: str | None
    icon: str | None
    color: str | None

    class Config:
        from_attributes = True


class AgeStageResponse(BaseModel):
    """Age stage response."""

    id: str
    name: str
    slug: str
    min_age_months: int
    max_age_months: int
    description: str | None
    order: int

    class Config:
        from_attributes = True


class AgeStageWithCountsResponse(AgeStageResponse):
    """Age stage with milestone and activity counts."""

    milestone_count: int = 0
    activity_count: int = 0


class MilestoneResponse(BaseModel):
    """Milestone response."""

    id: str
    title: str
    description: str
    typical_age_months: int | None
    importance: str
    domain: DomainResponse | None = None
    age_stage: AgeStageResponse | None = None

    class Config:
        from_attributes = True


class ActivityResponse(BaseModel):
    """Activity response."""

    id: str
    title: str
    description: str
    instructions: str
    duration_minutes: int | None
    materials_needed: list[str] | None
    difficulty: str
    week_number: int | None
    domain: DomainResponse | None = None
    age_stage: AgeStageResponse | None = None

    class Config:
        from_attributes = True


class CurriculumOverviewResponse(BaseModel):
    """Overview of curriculum for a specific age stage."""

    age_stage: AgeStageResponse
    domains: list[DomainResponse]
    milestones: list[MilestoneResponse]
    activities: list[ActivityResponse]
