"""Chat routes for AI coaching."""

import json
from datetime import datetime
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sse_starlette.sse import EventSourceResponse

from app.api.deps import get_current_user
from app.config import get_settings
from app.db.session import get_db
from app.models.chat import ChatMessage, ChatSession
from app.models.child import Child
from app.models.user import User
from app.schemas.chat import (
    ChatMessageCreate,
    ChatMessageResponse,
    ChatSessionCreate,
    ChatSessionListResponse,
    ChatSessionResponse,
)
from app.services.claude_service import get_claude_service

router = APIRouter(prefix="/chat", tags=["chat"])
settings = get_settings()

# Templates for HTML responses
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent.parent / "web" / "templates"))


@router.get("/sessions")
async def list_chat_sessions(
    request: Request,
    format: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all chat sessions for the user's family."""
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.family_id == current_user.family_id)
        .order_by(ChatSession.updated_at.desc())
    )
    sessions = result.scalars().all()

    sessions_data = []
    for session in sessions:
        # Get message count
        count_result = await db.execute(
            select(func.count(ChatMessage.id)).where(
                ChatMessage.session_id == session.id
            )
        )
        message_count = count_result.scalar() or 0

        sessions_data.append({
            "id": str(session.id),
            "title": session.title,
            "child_id": str(session.child_id) if session.child_id else None,
            "created_at": session.created_at,
            "updated_at": session.updated_at,
            "message_count": message_count,
        })

    # Return HTML if requested (for HTMX)
    if format == "html" or request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            "partials/chat_sessions_list.html",
            {"request": request, "sessions": sessions_data},
        )

    # Return JSON by default
    return [
        ChatSessionListResponse(
            id=s["id"],
            title=s["title"],
            child_id=s["child_id"],
            created_at=s["created_at"],
            updated_at=s["updated_at"],
            message_count=s["message_count"],
        )
        for s in sessions_data
    ]


@router.post("/sessions", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_chat_session(
    data: ChatSessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new chat session."""
    # Verify child belongs to family if provided
    child_id = None
    if data.child_id:
        result = await db.execute(
            select(Child).where(
                Child.id == UUID(data.child_id),
                Child.family_id == current_user.family_id,
            )
        )
        child = result.scalar_one_or_none()
        if not child:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Child not found",
            )
        child_id = child.id

    session = ChatSession(
        family_id=current_user.family_id,
        user_id=current_user.id,
        child_id=child_id,
        title=data.title or "New Chat",
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    return ChatSessionResponse(
        id=str(session.id),
        family_id=str(session.family_id),
        user_id=str(session.user_id),
        child_id=str(session.child_id) if session.child_id else None,
        title=session.title,
        summary=session.summary,
        created_at=session.created_at,
        updated_at=session.updated_at,
        messages=[],
    )


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_chat_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific chat session with messages."""
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    return ChatSessionResponse(
        id=str(session.id),
        family_id=str(session.family_id),
        user_id=str(session.user_id),
        child_id=str(session.child_id) if session.child_id else None,
        title=session.title,
        summary=session.summary,
        created_at=session.created_at,
        updated_at=session.updated_at,
        messages=[
            ChatMessageResponse(
                id=str(m.id),
                role=m.role,
                content=m.content,
                tokens_used=m.tokens_used,
                created_at=m.created_at,
            )
            for m in session.messages
        ],
    )


@router.post("/sessions/{session_id}/message")
async def send_message(
    session_id: UUID,
    data: ChatMessageCreate,
    stream: bool = True,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a message and get AI response."""
    # Get session
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    # Check rate limit
    await _check_rate_limit(db, current_user.family_id)

    # Save user message
    user_message = ChatMessage(
        session_id=session_id,
        role="user",
        content=data.content,
    )
    db.add(user_message)
    await db.commit()

    # Build message history
    messages = [{"role": m.role, "content": m.content} for m in session.messages]
    messages.append({"role": "user", "content": data.content})

    # Get child context if session has child_id
    child_context = None
    if session.child_id:
        child_context = await _build_child_context(db, session.child_id)

    claude_service = get_claude_service()

    # Get parent mood for sentiment-adaptive responses
    parent_mood = data.mood

    if stream:
        async def generate():
            full_response = []
            async for chunk in claude_service.stream_chat_response(messages, child_context, parent_mood):
                full_response.append(chunk)
                yield {"event": "message", "data": json.dumps({"content": chunk})}

            # Save complete assistant message
            assistant_message = ChatMessage(
                session_id=session_id,
                role="assistant",
                content="".join(full_response),
                model_used=settings.claude_model,
            )
            db.add(assistant_message)

            # Update session timestamp
            session.updated_at = datetime.utcnow()
            await db.commit()

            yield {"event": "done", "data": ""}

        return EventSourceResponse(generate())
    else:
        response, tokens = await claude_service.get_chat_response(messages, child_context, parent_mood)

        assistant_message = ChatMessage(
            session_id=session_id,
            role="assistant",
            content=response,
            tokens_used=tokens,
            model_used=settings.claude_model,
        )
        db.add(assistant_message)

        session.updated_at = datetime.utcnow()
        await db.commit()

        return {
            "content": response,
            "tokens_used": tokens,
        }


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a chat session."""
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.family_id == current_user.family_id,
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    await db.delete(session)
    await db.commit()


async def _check_rate_limit(db: AsyncSession, family_id: UUID) -> None:
    """Check if family has remaining chat quota."""
    # Get family subscription tier
    from app.models.family import Family

    result = await db.execute(select(Family).where(Family.id == family_id))
    family = result.scalar_one_or_none()

    daily_limit = (
        settings.premium_daily_chat_limit
        if family and family.subscription_tier == "premium"
        else settings.free_daily_chat_limit
    )

    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    count_result = await db.execute(
        select(func.count(ChatMessage.id))
        .join(ChatSession)
        .where(
            ChatMessage.role == "user",
            ChatSession.family_id == family_id,
            ChatMessage.created_at >= today_start,
        )
    )
    count = count_result.scalar() or 0

    if count >= daily_limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Daily message limit ({daily_limit}) reached. Upgrade to premium for more.",
        )


async def _build_child_context(db: AsyncSession, child_id: UUID) -> dict:
    """Build context about a child for the AI."""
    result = await db.execute(select(Child).where(Child.id == child_id))
    child = result.scalar_one_or_none()

    if not child:
        return {}

    return {
        "name": child.name,
        "age_description": child.age_description,
        "recent_milestones": "none recorded",  # TODO: fetch from progress
        "focus_areas": "general development",
    }
