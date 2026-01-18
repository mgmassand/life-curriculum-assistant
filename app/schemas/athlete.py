"""Athlete schemas."""

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# Sport schemas
class SportBase(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    is_team_sport: bool = True
    has_positions: bool = False
    season_type: str = "year-round"


class SportResponse(SportBase):
    id: str
    is_active: bool

    class Config:
        from_attributes = True


# Athletic Age Stage schemas
class AthleticAgeStageResponse(BaseModel):
    id: str
    name: str
    slug: str
    min_age_months: int
    max_age_months: int
    description: Optional[str] = None
    ltad_stage: str
    focus_areas: Optional[list] = None
    order: int

    class Config:
        from_attributes = True


# Athletic Domain schemas
class AthleticDomainResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None

    class Config:
        from_attributes = True


# Athletic Milestone schemas
class AthleticMilestoneResponse(BaseModel):
    id: str
    sport_id: Optional[str] = None
    athletic_age_stage_id: str
    athletic_domain_id: str
    title: str
    description: str
    typical_age_months: Optional[int] = None
    importance: str
    source: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


# Athlete schemas
class AthleteBase(BaseModel):
    primary_sport_id: Optional[str] = None
    secondary_sports: Optional[list] = None
    position: Optional[str] = None
    height_inches: Optional[int] = None
    weight_lbs: Optional[int] = None
    dominant_hand: Optional[str] = None
    club_team: Optional[str] = None
    school_team: Optional[str] = None
    jersey_number: Optional[str] = None
    recruitment_status: str = "not_started"
    target_division: Optional[str] = None
    graduation_year: Optional[int] = None


class AthleteCreate(AthleteBase):
    child_id: str


class AthleteUpdate(BaseModel):
    primary_sport_id: Optional[str] = None
    secondary_sports: Optional[list] = None
    position: Optional[str] = None
    height_inches: Optional[int] = None
    weight_lbs: Optional[int] = None
    dominant_hand: Optional[str] = None
    club_team: Optional[str] = None
    school_team: Optional[str] = None
    jersey_number: Optional[str] = None
    recruitment_status: Optional[str] = None
    target_division: Optional[str] = None
    graduation_year: Optional[int] = None


class AthleteResponse(AthleteBase):
    id: str
    child_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Academic Record schemas
class AcademicRecordBase(BaseModel):
    record_type: str
    semester: Optional[str] = None
    grade_level: Optional[int] = None
    gpa: Optional[float] = None
    cumulative_gpa: Optional[float] = None
    core_gpa: Optional[float] = None
    test_type: Optional[str] = None
    test_score: Optional[int] = None
    test_date: Optional[date] = None
    course_name: Optional[str] = None
    course_type: Optional[str] = None
    credits: Optional[float] = None
    grade: Optional[str] = None
    is_ncaa_approved: Optional[bool] = None
    notes: Optional[str] = None


class AcademicRecordCreate(AcademicRecordBase):
    athlete_id: str


class AcademicRecordResponse(AcademicRecordBase):
    id: str
    athlete_id: str
    created_at: datetime

    class Config:
        from_attributes = True


# Training Plan schemas
class TrainingPlanResponse(BaseModel):
    id: str
    sport_id: Optional[str] = None
    athletic_age_stage_id: str
    name: str
    description: str
    duration_weeks: int
    sessions_per_week: int
    focus: str
    difficulty: str
    equipment_needed: Optional[list] = None
    source: Optional[str] = None
    is_template: bool
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Athlete Training Plan Assignment
class AthleteTrainingPlanCreate(BaseModel):
    athlete_id: str
    training_plan_id: str
    start_date: date


class AthleteTrainingPlanResponse(BaseModel):
    id: str
    athlete_id: str
    training_plan_id: str
    start_date: date
    end_date: Optional[date] = None
    status: str
    current_week: int
    created_at: datetime

    class Config:
        from_attributes = True


# Recruitment Contact schemas
class RecruitmentContactBase(BaseModel):
    college_name: str
    division: str
    conference: Optional[str] = None
    coach_name: Optional[str] = None
    coach_title: Optional[str] = None
    coach_email: Optional[str] = None
    coach_phone: Optional[str] = None
    interest_level: str = "researching"
    status: str = "researching"
    next_action: Optional[str] = None
    next_action_date: Optional[date] = None
    notes: Optional[str] = None


class RecruitmentContactCreate(RecruitmentContactBase):
    athlete_id: str


class RecruitmentContactUpdate(BaseModel):
    college_name: Optional[str] = None
    division: Optional[str] = None
    conference: Optional[str] = None
    coach_name: Optional[str] = None
    coach_title: Optional[str] = None
    coach_email: Optional[str] = None
    coach_phone: Optional[str] = None
    interest_level: Optional[str] = None
    status: Optional[str] = None
    last_contact_date: Optional[date] = None
    next_action: Optional[str] = None
    next_action_date: Optional[date] = None
    notes: Optional[str] = None


class RecruitmentContactResponse(RecruitmentContactBase):
    id: str
    athlete_id: str
    last_contact_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Recruitment Event schemas
class RecruitmentEventBase(BaseModel):
    event_type: str
    name: str
    location: Optional[str] = None
    event_date: date
    end_date: Optional[date] = None
    cost: Optional[float] = None
    registration_deadline: Optional[date] = None
    status: str = "planned"
    outcome: Optional[str] = None
    contacts_made: Optional[list] = None
    notes: Optional[str] = None


class RecruitmentEventCreate(RecruitmentEventBase):
    athlete_id: str
    recruitment_contact_id: Optional[str] = None


class RecruitmentEventResponse(RecruitmentEventBase):
    id: str
    athlete_id: str
    recruitment_contact_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Athletic Progress schemas
class AthleticProgressBase(BaseModel):
    status: str = "not_started"
    notes: Optional[str] = None
    video_url: Optional[str] = None


class AthleticProgressCreate(AthleticProgressBase):
    athlete_id: str
    athletic_milestone_id: str


class AthleticProgressUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    video_url: Optional[str] = None


class AthleticProgressResponse(AthleticProgressBase):
    id: str
    athlete_id: str
    athletic_milestone_id: str
    completed_at: Optional[datetime] = None
    recorded_by_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Performance Metric schemas
class PerformanceMetricBase(BaseModel):
    metric_type: str
    value: float
    unit: str
    measurement_date: date
    measurement_context: Optional[str] = None
    notes: Optional[str] = None


class PerformanceMetricCreate(PerformanceMetricBase):
    athlete_id: str
    sport_id: Optional[str] = None


class PerformanceMetricResponse(PerformanceMetricBase):
    id: str
    athlete_id: str
    sport_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
