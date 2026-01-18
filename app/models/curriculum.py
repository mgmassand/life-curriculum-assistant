"""Curriculum models - AgeStage, DevelopmentDomain, Milestone, Activity."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AgeStage(Base):
    """Developmental age ranges for organizing curriculum."""

    __tablename__ = "age_stages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    min_age_months: Mapped[int] = mapped_column(Integer, nullable=False)
    max_age_months: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    order: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationships
    milestones: Mapped[list["Milestone"]] = relationship(
        "Milestone", back_populates="age_stage"
    )
    activities: Mapped[list["Activity"]] = relationship(
        "Activity", back_populates="age_stage"
    )


class DevelopmentDomain(Base):
    """Categories of development (physical, cognitive, social, etc.)."""

    __tablename__ = "development_domains"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True)
    color: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Relationships
    milestones: Mapped[list["Milestone"]] = relationship(
        "Milestone", back_populates="domain"
    )
    activities: Mapped[list["Activity"]] = relationship(
        "Activity", back_populates="domain"
    )


class Milestone(Base):
    """Developmental milestones children should achieve."""

    __tablename__ = "milestones"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    age_stage_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("age_stages.id"), nullable=False
    )
    domain_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("development_domains.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    typical_age_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    importance: Mapped[str] = mapped_column(String(20), default="normal")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    age_stage: Mapped["AgeStage"] = relationship("AgeStage", back_populates="milestones")
    domain: Mapped["DevelopmentDomain"] = relationship(
        "DevelopmentDomain", back_populates="milestones"
    )
    progress_entries: Mapped[list["ChildProgress"]] = relationship(
        "ChildProgress", back_populates="milestone"
    )


class Activity(Base):
    """Curriculum activities/exercises for parents to do with children."""

    __tablename__ = "activities"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    age_stage_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("age_stages.id"), nullable=False
    )
    domain_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("development_domains.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    instructions: Mapped[str] = mapped_column(Text, nullable=False)
    duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    materials_needed: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    difficulty: Mapped[str] = mapped_column(String(20), default="easy")
    week_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    age_stage: Mapped["AgeStage"] = relationship("AgeStage", back_populates="activities")
    domain: Mapped["DevelopmentDomain"] = relationship(
        "DevelopmentDomain", back_populates="activities"
    )
    related_milestones: Mapped[list["ActivityMilestone"]] = relationship(
        "ActivityMilestone", back_populates="activity"
    )
    progress_entries: Mapped[list["ChildProgress"]] = relationship(
        "ChildProgress", back_populates="activity"
    )


class ActivityMilestone(Base):
    """Many-to-many relationship between activities and milestones."""

    __tablename__ = "activity_milestones"

    activity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("activities.id"), primary_key=True
    )
    milestone_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("milestones.id"), primary_key=True
    )

    # Relationships
    activity: Mapped["Activity"] = relationship(
        "Activity", back_populates="related_milestones"
    )
    milestone: Mapped["Milestone"] = relationship("Milestone")
