"""API routes for Interest Discovery and Analysis."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.services.gemini_service import get_openai_service

router = APIRouter(prefix="/interests", tags=["interests"])


class QuizResponse(BaseModel):
    """Single quiz response."""
    question: str
    answer: str


class InterestAnalysisRequest(BaseModel):
    """Request to analyze interests."""
    child_id: UUID | None = None
    responses: list[QuizResponse]


class InterestAnalysisResponse(BaseModel):
    """Interest analysis result."""
    primary_interests: list[str]
    interest_scores: dict[str, int] | None = None
    learning_style: str
    recommended_approaches: list[str] | None = None
    interest_to_standard_opportunities: list[dict]
    parent_insight: str


@router.post("/analyze", response_model=InterestAnalysisResponse)
async def analyze_interests(
    request: InterestAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Analyze quiz responses to identify child's interests."""
    openai_service = get_openai_service()

    # Convert responses to list of dicts for OpenAI
    responses_data = [
        {"question": r.question, "answer": r.answer}
        for r in request.responses
    ]

    try:
        result = await openai_service.analyze_interests(responses_data)

        if "error" in result:
            raise HTTPException(status_code=500, detail="Failed to analyze interests")

        return InterestAnalysisResponse(
            primary_interests=result.get("primary_interests", []),
            interest_scores=result.get("interest_scores"),
            learning_style=result.get("learning_style", "Not determined"),
            recommended_approaches=result.get("recommended_approaches"),
            interest_to_standard_opportunities=result.get("interest_to_standard_opportunities", []),
            parent_insight=result.get("parent_insight", "")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
