"""User schemas."""

from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    """Base user schema."""

    email: EmailStr
    full_name: str


class UserCreate(UserBase):
    """Schema for creating a user."""

    password: str
    family_id: str | None = None


class UserUpdate(BaseModel):
    """Schema for updating a user."""

    full_name: str | None = None
    email: EmailStr | None = None


class UserResponse(BaseModel):
    """User response schema."""

    id: str
    email: str
    full_name: str
    family_id: str
    role: str
    is_active: bool
    email_verified: bool
    created_at: datetime
    last_login: datetime | None

    class Config:
        from_attributes = True
