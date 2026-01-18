"""Authentication schemas."""

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    """Login request schema."""

    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    """Registration request schema."""

    email: EmailStr
    password: str
    full_name: str
    family_name: str


class TokenResponse(BaseModel):
    """Token response (for non-cookie based auth)."""

    access_token: str
    token_type: str = "bearer"


class AuthResponse(BaseModel):
    """Authentication response."""

    message: str
    user: "UserResponse"


class UserResponse(BaseModel):
    """User data in responses."""

    id: str
    email: str
    full_name: str
    family_id: str
    role: str

    class Config:
        from_attributes = True
