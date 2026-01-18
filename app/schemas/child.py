"""Child schemas."""

from datetime import date, datetime

from pydantic import BaseModel


class ChildBase(BaseModel):
    """Base child schema."""

    name: str
    date_of_birth: date
    gender: str | None = None
    notes: str | None = None


class ChildCreate(ChildBase):
    """Schema for creating a child."""

    pass


class ChildUpdate(BaseModel):
    """Schema for updating a child."""

    name: str | None = None
    date_of_birth: date | None = None
    gender: str | None = None
    notes: str | None = None


class ChildResponse(ChildBase):
    """Child response schema."""

    id: str
    family_id: str
    avatar_url: str | None
    is_active: bool
    created_at: datetime
    age_in_months: int
    age_description: str

    class Config:
        from_attributes = True
