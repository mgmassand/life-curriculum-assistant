"""Chat schemas."""

from datetime import datetime

from pydantic import BaseModel


class ChatMessageCreate(BaseModel):
    """Schema for creating a chat message."""

    content: str
    mood: str | None = None  # Parent's current mood for sentiment-adaptive responses


class ChatMessageResponse(BaseModel):
    """Chat message response schema."""

    id: str
    role: str
    content: str
    tokens_used: int | None
    created_at: datetime

    class Config:
        from_attributes = True


class ChatSessionCreate(BaseModel):
    """Schema for creating a chat session."""

    child_id: str | None = None
    title: str | None = None


class ChatSessionResponse(BaseModel):
    """Chat session response schema."""

    id: str
    family_id: str
    user_id: str
    child_id: str | None
    title: str | None
    summary: str | None
    created_at: datetime
    updated_at: datetime
    messages: list[ChatMessageResponse] = []

    class Config:
        from_attributes = True


class ChatSessionListResponse(BaseModel):
    """Chat session list item (without messages)."""

    id: str
    title: str | None
    child_id: str | None
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

    class Config:
        from_attributes = True
