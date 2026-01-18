"""API routes for 12-Week Roadmap generation."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.services.gemini_service import get_openai_service

router = APIRouter(prefix="/roadmap", tags=["roadmap"])


class RoadmapGenerateRequest(BaseModel):
    """Request to generate a roadmap."""
    child_name: str
    age: str
    interests: list[str]
    challenges: str | None = None


class ActivityDetail(BaseModel):
    """Activity within a week."""
    name: str
    description: str
    duration: str
    materials: list[str]


class WeekDetail(BaseModel):
    """Single week in the roadmap."""
    week: int
    theme: str
    interest_focus: str
    academic_connections: list[str]
    activities: list[ActivityDetail]
    milestone: str


class RoadmapResponse(BaseModel):
    """Complete 12-week roadmap."""
    title: str
    overview: str
    weeks: list[WeekDetail]
    parent_tips: list[str]


@router.post("/generate", response_model=RoadmapResponse)
async def generate_roadmap(
    request: RoadmapGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a personalized 12-week Interest-to-Standard roadmap."""
    openai_service = get_openai_service()

    try:
        result = await openai_service.generate_12_week_roadmap(
            child_name=request.child_name,
            age=request.age,
            interests=request.interests,
            current_challenges=request.challenges
        )

        if "error" in result:
            raise HTTPException(status_code=500, detail="Failed to generate roadmap")

        # Parse the result
        weeks = []
        for week_data in result.get("weeks", []):
            activities = []
            for act in week_data.get("activities", []):
                activities.append(ActivityDetail(
                    name=act.get("name", "Activity"),
                    description=act.get("description", ""),
                    duration=act.get("duration", "20 minutes"),
                    materials=act.get("materials", [])
                ))

            weeks.append(WeekDetail(
                week=week_data.get("week", 1),
                theme=week_data.get("theme", "Learning Theme"),
                interest_focus=week_data.get("interest_focus", ""),
                academic_connections=week_data.get("academic_connections", []),
                activities=activities,
                milestone=week_data.get("milestone", "")
            ))

        return RoadmapResponse(
            title=result.get("title", "Your Personalized Learning Roadmap"),
            overview=result.get("overview", "A customized 12-week learning journey"),
            weeks=weeks,
            parent_tips=result.get("parent_tips", [])
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Roadmap generation failed: {str(e)}")
