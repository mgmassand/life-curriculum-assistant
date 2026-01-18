"""Athletic models for Student-Athlete Curriculum."""

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Sport(Base):
    """Sports supported in the athletic curriculum."""

    __tablename__ = "sports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True)
    color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_team_sport: Mapped[bool] = mapped_column(Boolean, default=True)
    has_positions: Mapped[bool] = mapped_column(Boolean, default=False)
    season_type: Mapped[str] = mapped_column(String(20), default="year-round")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    milestones: Mapped[list["AthleticMilestone"]] = relationship(
        "AthleticMilestone", back_populates="sport"
    )
    training_plans: Mapped[list["TrainingPlan"]] = relationship(
        "TrainingPlan", back_populates="sport"
    )
    athletes: Mapped[list["Athlete"]] = relationship(
        "Athlete", back_populates="primary_sport", foreign_keys="Athlete.primary_sport_id"
    )


class AthleticAgeStage(Base):
    """Athletic development stages based on LTAD model (ages 5-18)."""

    __tablename__ = "athletic_age_stages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    min_age_months: Mapped[int] = mapped_column(Integer, nullable=False)
    max_age_months: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    ltad_stage: Mapped[str] = mapped_column(String(50), nullable=False)
    focus_areas: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    order: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationships
    milestones: Mapped[list["AthleticMilestone"]] = relationship(
        "AthleticMilestone", back_populates="athletic_age_stage"
    )
    training_plans: Mapped[list["TrainingPlan"]] = relationship(
        "TrainingPlan", back_populates="athletic_age_stage"
    )


class AthleticDomain(Base):
    """Athletic development domains (Physical Literacy, Technical Skills, etc.)."""

    __tablename__ = "athletic_domains"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True)
    color: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Relationships
    milestones: Mapped[list["AthleticMilestone"]] = relationship(
        "AthleticMilestone", back_populates="domain"
    )


class AthleticMilestone(Base):
    """Athletic development milestones by age and sport."""

    __tablename__ = "athletic_milestones"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    sport_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sports.id"), nullable=True
    )
    athletic_age_stage_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("athletic_age_stages.id"), nullable=False
    )
    athletic_domain_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("athletic_domains.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    typical_age_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    importance: Mapped[str] = mapped_column(String(20), default="normal")
    source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    sport: Mapped["Sport | None"] = relationship("Sport", back_populates="milestones")
    athletic_age_stage: Mapped["AthleticAgeStage"] = relationship(
        "AthleticAgeStage", back_populates="milestones"
    )
    domain: Mapped["AthleticDomain"] = relationship(
        "AthleticDomain", back_populates="milestones"
    )
    progress_entries: Mapped[list["AthleticProgress"]] = relationship(
        "AthleticProgress", back_populates="milestone"
    )


class Athlete(Base):
    """Athlete profile linked to a child."""

    __tablename__ = "athletes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    child_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("children.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    primary_sport_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sports.id"), nullable=True
    )
    secondary_sports: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    position: Mapped[str | None] = mapped_column(String(100), nullable=True)
    height_inches: Mapped[int | None] = mapped_column(Integer, nullable=True)
    weight_lbs: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dominant_hand: Mapped[str | None] = mapped_column(String(10), nullable=True)
    club_team: Mapped[str | None] = mapped_column(String(255), nullable=True)
    school_team: Mapped[str | None] = mapped_column(String(255), nullable=True)
    jersey_number: Mapped[str | None] = mapped_column(String(10), nullable=True)
    recruitment_status: Mapped[str] = mapped_column(String(50), default="not_started")
    target_division: Mapped[str | None] = mapped_column(String(20), nullable=True)
    graduation_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    child: Mapped["Child"] = relationship("Child", backref="athlete_profile")
    primary_sport: Mapped["Sport | None"] = relationship(
        "Sport", back_populates="athletes", foreign_keys=[primary_sport_id]
    )
    academic_records: Mapped[list["AcademicRecord"]] = relationship(
        "AcademicRecord", back_populates="athlete", cascade="all, delete-orphan"
    )
    training_plan_assignments: Mapped[list["AthleteTrainingPlan"]] = relationship(
        "AthleteTrainingPlan", back_populates="athlete", cascade="all, delete-orphan"
    )
    training_progress: Mapped[list["TrainingProgress"]] = relationship(
        "TrainingProgress", back_populates="athlete", cascade="all, delete-orphan"
    )
    recruitment_contacts: Mapped[list["RecruitmentContact"]] = relationship(
        "RecruitmentContact", back_populates="athlete", cascade="all, delete-orphan"
    )
    recruitment_events: Mapped[list["RecruitmentEvent"]] = relationship(
        "RecruitmentEvent", back_populates="athlete", cascade="all, delete-orphan"
    )
    athletic_progress: Mapped[list["AthleticProgress"]] = relationship(
        "AthleticProgress", back_populates="athlete", cascade="all, delete-orphan"
    )
    performance_metrics: Mapped[list["PerformanceMetric"]] = relationship(
        "PerformanceMetric", back_populates="athlete", cascade="all, delete-orphan"
    )

    # AthleteLife 360 relationships
    physiology_records: Mapped[list["AthletePhysiology"]] = relationship(
        "AthletePhysiology", back_populates="athlete", cascade="all, delete-orphan"
    )
    activity_logs: Mapped[list["ActivityLog"]] = relationship(
        "ActivityLog", back_populates="athlete", cascade="all, delete-orphan"
    )
    fun_check_ins: Mapped[list["FunCheckIn"]] = relationship(
        "FunCheckIn", back_populates="athlete", cascade="all, delete-orphan"
    )
    motor_assessments: Mapped[list["MotorSkillAssessment"]] = relationship(
        "MotorSkillAssessment", back_populates="athlete", cascade="all, delete-orphan"
    )
    calendar_events: Mapped[list["CalendarEvent"]] = relationship(
        "CalendarEvent", back_populates="athlete", cascade="all, delete-orphan"
    )
    injury_risk_logs: Mapped[list["InjuryRiskLog"]] = relationship(
        "InjuryRiskLog", back_populates="athlete", cascade="all, delete-orphan"
    )
    ncaa_courses: Mapped[list["NCAACourse"]] = relationship(
        "NCAACourse", back_populates="athlete", cascade="all, delete-orphan"
    )
    financial_projections: Mapped[list["FinancialProjection"]] = relationship(
        "FinancialProjection", back_populates="athlete", cascade="all, delete-orphan"
    )
    nil_deals: Mapped[list["NILDeal"]] = relationship(
        "NILDeal", back_populates="athlete", cascade="all, delete-orphan"
    )


class AcademicRecord(Base):
    """Academic tracking for NCAA eligibility."""

    __tablename__ = "academic_records"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    athlete_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("athletes.id", ondelete="CASCADE"), nullable=False
    )
    record_type: Mapped[str] = mapped_column(String(30), nullable=False)
    semester: Mapped[str | None] = mapped_column(String(50), nullable=True)
    grade_level: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # GPA tracking
    gpa: Mapped[float | None] = mapped_column(Float, nullable=True)
    cumulative_gpa: Mapped[float | None] = mapped_column(Float, nullable=True)
    core_gpa: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Test scores
    test_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    test_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    test_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Course tracking
    course_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    course_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    credits: Mapped[float | None] = mapped_column(Float, nullable=True)
    grade: Mapped[str | None] = mapped_column(String(5), nullable=True)
    is_ncaa_approved: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    athlete: Mapped["Athlete"] = relationship("Athlete", back_populates="academic_records")


class TrainingPlan(Base):
    """Training plan templates and assigned plans."""

    __tablename__ = "training_plans"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    sport_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sports.id"), nullable=True
    )
    athletic_age_stage_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("athletic_age_stages.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    duration_weeks: Mapped[int] = mapped_column(Integer, nullable=False)
    sessions_per_week: Mapped[int] = mapped_column(Integer, nullable=False)
    focus: Mapped[str] = mapped_column(String(30), default="hybrid")
    difficulty: Mapped[str] = mapped_column(String(20), default="beginner")
    equipment_needed: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_template: Mapped[bool] = mapped_column(Boolean, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    sport: Mapped["Sport | None"] = relationship("Sport", back_populates="training_plans")
    athletic_age_stage: Mapped["AthleticAgeStage"] = relationship(
        "AthleticAgeStage", back_populates="training_plans"
    )
    sessions: Mapped[list["TrainingSession"]] = relationship(
        "TrainingSession", back_populates="training_plan", cascade="all, delete-orphan"
    )
    assignments: Mapped[list["AthleteTrainingPlan"]] = relationship(
        "AthleteTrainingPlan", back_populates="training_plan"
    )


class TrainingSession(Base):
    """Individual training sessions within a plan."""

    __tablename__ = "training_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    training_plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("training_plans.id", ondelete="CASCADE"), nullable=False
    )
    week_number: Mapped[int] = mapped_column(Integer, nullable=False)
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)
    session_type: Mapped[str] = mapped_column(String(30), default="skills")
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    warmup: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    main_workout: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    cooldown: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    order: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    training_plan: Mapped["TrainingPlan"] = relationship(
        "TrainingPlan", back_populates="sessions"
    )
    progress_entries: Mapped[list["TrainingProgress"]] = relationship(
        "TrainingProgress", back_populates="training_session"
    )


class AthleteTrainingPlan(Base):
    """Training plans assigned to athletes."""

    __tablename__ = "athlete_training_plans"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    athlete_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("athletes.id", ondelete="CASCADE"), nullable=False
    )
    training_plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("training_plans.id"), nullable=False
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")
    current_week: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    athlete: Mapped["Athlete"] = relationship(
        "Athlete", back_populates="training_plan_assignments"
    )
    training_plan: Mapped["TrainingPlan"] = relationship(
        "TrainingPlan", back_populates="assignments"
    )
    progress_entries: Mapped[list["TrainingProgress"]] = relationship(
        "TrainingProgress", back_populates="athlete_training_plan", cascade="all, delete-orphan"
    )


class TrainingProgress(Base):
    """Track completion of training sessions."""

    __tablename__ = "training_progress"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    athlete_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("athletes.id", ondelete="CASCADE"), nullable=False
    )
    training_session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("training_sessions.id"), nullable=False
    )
    athlete_training_plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("athlete_training_plans.id", ondelete="CASCADE"), nullable=False
    )
    scheduled_date: Mapped[date] = mapped_column(Date, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="scheduled")
    actual_duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    difficulty_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    modifications: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    athlete: Mapped["Athlete"] = relationship("Athlete", back_populates="training_progress")
    training_session: Mapped["TrainingSession"] = relationship(
        "TrainingSession", back_populates="progress_entries"
    )
    athlete_training_plan: Mapped["AthleteTrainingPlan"] = relationship(
        "AthleteTrainingPlan", back_populates="progress_entries"
    )


class RecruitmentContact(Base):
    """College coach contacts for recruitment tracking."""

    __tablename__ = "recruitment_contacts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    athlete_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("athletes.id", ondelete="CASCADE"), nullable=False
    )
    college_name: Mapped[str] = mapped_column(String(255), nullable=False)
    division: Mapped[str] = mapped_column(String(20), nullable=False)
    conference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    coach_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    coach_title: Mapped[str | None] = mapped_column(String(100), nullable=True)
    coach_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    coach_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    interest_level: Mapped[str] = mapped_column(String(30), default="researching")
    status: Mapped[str] = mapped_column(String(30), default="researching")
    last_contact_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    next_action: Mapped[str | None] = mapped_column(String(255), nullable=True)
    next_action_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    athlete: Mapped["Athlete"] = relationship(
        "Athlete", back_populates="recruitment_contacts"
    )
    events: Mapped[list["RecruitmentEvent"]] = relationship(
        "RecruitmentEvent", back_populates="recruitment_contact"
    )


class RecruitmentEvent(Base):
    """Showcases, camps, visits, and recruitment events."""

    __tablename__ = "recruitment_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    athlete_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("athletes.id", ondelete="CASCADE"), nullable=False
    )
    recruitment_contact_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recruitment_contacts.id", ondelete="SET NULL"), nullable=True
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    registration_deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="planned")
    outcome: Mapped[str | None] = mapped_column(Text, nullable=True)
    contacts_made: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    athlete: Mapped["Athlete"] = relationship(
        "Athlete", back_populates="recruitment_events"
    )
    recruitment_contact: Mapped["RecruitmentContact | None"] = relationship(
        "RecruitmentContact", back_populates="events"
    )


class AthleticProgress(Base):
    """Track athlete's milestone completion."""

    __tablename__ = "athletic_progress"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    athlete_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("athletes.id", ondelete="CASCADE"), nullable=False
    )
    athletic_milestone_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("athletic_milestones.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(30), default="not_started")
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    video_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    recorded_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    athlete: Mapped["Athlete"] = relationship(
        "Athlete", back_populates="athletic_progress"
    )
    milestone: Mapped["AthleticMilestone"] = relationship(
        "AthleticMilestone", back_populates="progress_entries"
    )


class PerformanceMetric(Base):
    """Track measurable athletic performance."""

    __tablename__ = "performance_metrics"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    athlete_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("athletes.id", ondelete="CASCADE"), nullable=False
    )
    sport_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sports.id"), nullable=True
    )
    metric_type: Mapped[str] = mapped_column(String(50), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(30), nullable=False)
    measurement_date: Mapped[date] = mapped_column(Date, nullable=False)
    measurement_context: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    athlete: Mapped["Athlete"] = relationship(
        "Athlete", back_populates="performance_metrics"
    )


# ============================================================================
# AthleteLife 360 - New Models
# ============================================================================


class AthletePhysiology(Base):
    """Track physical growth and PHV (Peak Height Velocity) for Growth Spurt Guardian."""

    __tablename__ = "athlete_physiology"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    athlete_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("athletes.id", ondelete="CASCADE"), nullable=False
    )
    measurement_date: Mapped[date] = mapped_column(Date, nullable=False)
    height_cm: Mapped[float] = mapped_column(Float, nullable=False)
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    sitting_height_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    leg_length_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    arm_span_cm: Mapped[float | None] = mapped_column(Float, nullable=True)

    # PHV calculation fields (Mirwald equation)
    maturity_offset: Mapped[float | None] = mapped_column(Float, nullable=True)
    phv_status: Mapped[str | None] = mapped_column(String(30), nullable=True)  # pre-phv, phv, post-phv
    estimated_phv_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    growth_velocity_cm_month: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Training modifications
    recommended_modifications: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    injury_risk_factors: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    athlete: Mapped["Athlete"] = relationship(
        "Athlete", back_populates="physiology_records"
    )


class ActivityLog(Base):
    """Play-o-Meter: Track organized vs free play activities."""

    __tablename__ = "activity_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    athlete_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("athletes.id", ondelete="CASCADE"), nullable=False
    )
    activity_date: Mapped[date] = mapped_column(Date, nullable=False)
    activity_type: Mapped[str] = mapped_column(String(30), nullable=False)  # organized, free_play, rest
    sport_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sports.id"), nullable=True
    )
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    intensity: Mapped[str] = mapped_column(String(20), default="moderate")  # low, moderate, high
    context: Mapped[str | None] = mapped_column(String(50), nullable=True)  # practice, game, pickup, etc.
    location: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # For workload tracking (ACWR)
    training_load: Mapped[float | None] = mapped_column(Float, nullable=True)  # RPE x duration
    rpe: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1-10 rating

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    logged_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    athlete: Mapped["Athlete"] = relationship(
        "Athlete", back_populates="activity_logs"
    )


class FunCheckIn(Base):
    """Emoji-based enjoyment tracking for young athletes."""

    __tablename__ = "fun_check_ins"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    athlete_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("athletes.id", ondelete="CASCADE"), nullable=False
    )
    check_in_date: Mapped[date] = mapped_column(Date, nullable=False)
    activity_log_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("activity_logs.id", ondelete="SET NULL"), nullable=True
    )

    # Emoji ratings (1-5 scale with emoji representations)
    fun_rating: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5
    energy_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1-5
    friend_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1-5 (social enjoyment)

    # Optional context
    favorite_moment: Mapped[str | None] = mapped_column(String(500), nullable=True)
    want_to_do_again: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    athlete: Mapped["Athlete"] = relationship(
        "Athlete", back_populates="fun_check_ins"
    )

    __table_args__ = (
        CheckConstraint("fun_rating >= 1 AND fun_rating <= 5", name="fun_rating_range"),
        CheckConstraint("energy_rating IS NULL OR (energy_rating >= 1 AND energy_rating <= 5)", name="energy_rating_range"),
        CheckConstraint("friend_rating IS NULL OR (friend_rating >= 1 AND friend_rating <= 5)", name="friend_rating_range"),
    )


class ParentLearningModule(Base):
    """Parent University: Micro-learning content modules."""

    __tablename__ = "parent_learning_modules"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    content_type: Mapped[str] = mapped_column(String(30), nullable=False)  # video, article, quiz, infographic
    duration_seconds: Mapped[int] = mapped_column(Integer, default=60)  # target: 60-second lessons
    video_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    content_html: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Categorization
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # ltad, nutrition, mental, safety, recruiting
    age_stage_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("athletic_age_stages.id"), nullable=True
    )
    sport_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sports.id"), nullable=True
    )
    tags: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    # Source and credibility
    source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    expert_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    progress_records: Mapped[list["UserLearningProgress"]] = relationship(
        "UserLearningProgress", back_populates="module"
    )


class UserLearningProgress(Base):
    """Track user progress through Parent University modules."""

    __tablename__ = "user_learning_progress"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    module_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("parent_learning_modules.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), default="not_started")  # not_started, in_progress, completed
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    progress_percent: Mapped[int] = mapped_column(Integer, default=0)
    quiz_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    module: Mapped["ParentLearningModule"] = relationship(
        "ParentLearningModule", back_populates="progress_records"
    )


class MotorSkillAssessment(Base):
    """Sport Sampler AI: Motor skill assessments and sport recommendations."""

    __tablename__ = "motor_skill_assessments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    athlete_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("athletes.id", ondelete="CASCADE"), nullable=False
    )
    assessment_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Fundamental movement skills (FMS) scores
    locomotor_score: Mapped[int | None] = mapped_column(Integer, nullable=True)  # running, jumping, hopping
    stability_score: Mapped[int | None] = mapped_column(Integer, nullable=True)  # balance, core control
    object_control_score: Mapped[int | None] = mapped_column(Integer, nullable=True)  # catching, throwing, kicking
    spatial_awareness_score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Physical attributes
    speed_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    endurance_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    flexibility_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    power_score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Sport recommendations (AI-generated)
    recommended_sports: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # [{sport_id, score, reasoning}]
    strengths: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    areas_to_develop: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    overall_physical_literacy_score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    assessed_by: Mapped[str | None] = mapped_column(String(100), nullable=True)  # parent, coach, system
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    athlete: Mapped["Athlete"] = relationship(
        "Athlete", back_populates="motor_assessments"
    )


class CalendarEvent(Base):
    """Unified calendar for Academic-Athletic Load Balancer."""

    __tablename__ = "calendar_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    athlete_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("athletes.id", ondelete="CASCADE"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(30), nullable=False)  # practice, game, academic, rest, other
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_datetime: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_datetime: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    all_day: Mapped[bool] = mapped_column(Boolean, default=False)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # For crunch time detection
    priority: Mapped[str] = mapped_column(String(20), default="normal")  # low, normal, high, critical
    stress_factor: Mapped[int] = mapped_column(Integer, default=1)  # 1-5 scale
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=False)

    # Sport/academic linkage
    sport_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sports.id"), nullable=True
    )
    academic_subject: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Recurrence
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    recurrence_rule: Mapped[str | None] = mapped_column(String(255), nullable=True)
    parent_event_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("calendar_events.id"), nullable=True
    )

    color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    athlete: Mapped["Athlete"] = relationship(
        "Athlete", back_populates="calendar_events"
    )


class InjuryRiskLog(Base):
    """Injury Risk Dashboard: ACWR (Acute:Chronic Workload Ratio) tracking."""

    __tablename__ = "injury_risk_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    athlete_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("athletes.id", ondelete="CASCADE"), nullable=False
    )
    calculation_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Workload metrics
    acute_load: Mapped[float] = mapped_column(Float, nullable=False)  # Last 7 days
    chronic_load: Mapped[float] = mapped_column(Float, nullable=False)  # Last 28 days average
    acwr: Mapped[float] = mapped_column(Float, nullable=False)  # Acute:Chronic ratio

    # Risk assessment
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False)  # low, moderate, high, very_high
    risk_score: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-100

    # Contributing factors
    weekly_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    weekly_sessions: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rest_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    high_intensity_sessions: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # PHV-related risk adjustment
    phv_adjustment: Mapped[float | None] = mapped_column(Float, nullable=True)
    growth_spurt_flag: Mapped[bool] = mapped_column(Boolean, default=False)

    # Recommendations
    recommendations: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    alerts: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    athlete: Mapped["Athlete"] = relationship(
        "Athlete", back_populates="injury_risk_logs"
    )


class ConversationScript(Base):
    """Car Ride Home Coach: Context-aware communication scripts."""

    __tablename__ = "conversation_scripts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    # Contextual matching
    context_type: Mapped[str] = mapped_column(String(50), nullable=False)  # post_game, post_practice, general
    outcome_type: Mapped[str | None] = mapped_column(String(30), nullable=True)  # win, loss, poor_performance, great_performance
    emotion_type: Mapped[str | None] = mapped_column(String(30), nullable=True)  # frustrated, excited, disappointed, neutral
    age_stage_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("athletic_age_stages.id"), nullable=True
    )
    sport_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sports.id"), nullable=True
    )

    # Script content
    opening_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    talking_points: Mapped[list] = mapped_column(JSONB, nullable=False)  # [{topic, suggestion, avoid}]
    questions_to_ask: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    phrases_to_avoid: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    closing_suggestion: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Source
    source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    expert_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class NCAACourse(Base):
    """NCAA Eligibility Tracker: Core course tracking."""

    __tablename__ = "ncaa_courses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    athlete_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("athletes.id", ondelete="CASCADE"), nullable=False
    )
    course_name: Mapped[str] = mapped_column(String(255), nullable=False)
    course_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    subject_area: Mapped[str] = mapped_column(String(50), nullable=False)  # english, math, science, social_science, additional
    grade_level: Mapped[int] = mapped_column(Integer, nullable=False)  # 9-12
    semester: Mapped[str] = mapped_column(String(20), nullable=False)  # fall, spring, full_year
    school_year: Mapped[str] = mapped_column(String(20), nullable=False)  # e.g., "2024-2025"

    # Credits and grades
    credits: Mapped[float] = mapped_column(Float, nullable=False)
    grade: Mapped[str | None] = mapped_column(String(5), nullable=True)
    grade_points: Mapped[float | None] = mapped_column(Float, nullable=True)

    # NCAA approval status
    is_ncaa_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    ncaa_course_code: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Status
    status: Mapped[str] = mapped_column(String(20), default="planned")  # planned, in_progress, completed
    is_core_course: Mapped[bool] = mapped_column(Boolean, default=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    athlete: Mapped["Athlete"] = relationship(
        "Athlete", back_populates="ncaa_courses"
    )


class FinancialProjection(Base):
    """Recruiting Reality Check: ROI and financial projections."""

    __tablename__ = "financial_projections"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    athlete_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("athletes.id", ondelete="CASCADE"), nullable=False
    )
    projection_date: Mapped[date] = mapped_column(Date, nullable=False)
    projection_type: Mapped[str] = mapped_column(String(30), nullable=False)  # youth_sports, college_projection

    # Youth sports costs (cumulative tracking)
    annual_travel_team_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    annual_training_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    annual_equipment_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    annual_travel_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    annual_tournament_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_annual_investment: Mapped[float | None] = mapped_column(Float, nullable=True)
    cumulative_investment: Mapped[float | None] = mapped_column(Float, nullable=True)

    # College projection
    target_school: Mapped[str | None] = mapped_column(String(255), nullable=True)
    target_division: Mapped[str | None] = mapped_column(String(20), nullable=True)
    annual_cost_of_attendance: Mapped[float | None] = mapped_column(Float, nullable=True)
    projected_scholarship_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    projected_annual_aid: Mapped[float | None] = mapped_column(Float, nullable=True)
    net_annual_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    four_year_total_cost: Mapped[float | None] = mapped_column(Float, nullable=True)

    # ROI calculation
    scholarship_probability: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0-100%
    expected_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    roi_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    assumptions: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    athlete: Mapped["Athlete"] = relationship(
        "Athlete", back_populates="financial_projections"
    )


class NILDeal(Base):
    """NIL Education Suite: Track NIL activities and education."""

    __tablename__ = "nil_deals"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    athlete_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("athletes.id", ondelete="CASCADE"), nullable=False
    )

    # Deal details
    brand_name: Mapped[str] = mapped_column(String(255), nullable=False)
    deal_type: Mapped[str] = mapped_column(String(50), nullable=False)  # endorsement, appearance, social_media, merchandise
    status: Mapped[str] = mapped_column(String(30), default="potential")  # potential, negotiating, active, completed, declined
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Financial terms
    total_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    payment_structure: Mapped[str | None] = mapped_column(String(50), nullable=True)  # one_time, monthly, per_post
    in_kind_value: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Requirements
    deliverables: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    exclusivity_terms: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Compliance
    disclosed_to_school: Mapped[bool] = mapped_column(Boolean, default=False)
    school_approval_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    compliant_with_state_law: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    athlete: Mapped["Athlete"] = relationship(
        "Athlete", back_populates="nil_deals"
    )


class KnowledgeDocument(Base):
    """AthleTEQ AI: RAG knowledge base documents."""

    __tablename__ = "knowledge_documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    source: Mapped[str] = mapped_column(String(255), nullable=False)  # NSCA, NCAA, AAP, etc.
    source_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    document_type: Mapped[str] = mapped_column(String(50), nullable=False)  # guideline, research, manual, faq

    # Content
    content: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Categorization
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # ltad, eligibility, nutrition, injury, mental, recruiting
    sport_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sports.id"), nullable=True
    )
    age_stage_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("athletic_age_stages.id"), nullable=True
    )
    tags: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    # Vector embedding for RAG (stored externally in vector DB, reference here)
    embedding_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    chunk_index: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Metadata
    publication_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    last_verified: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# Import Child for type hints (avoiding circular imports)
from app.models.child import Child
