"""Progress tracking model."""

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ChildProgress(Base):
    """Track child's completion of activities and milestones."""

    __tablename__ = "child_progress"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    child_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("children.id"), nullable=False
    )
    milestone_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("milestones.id"), nullable=True
    )
    activity_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("activities.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="not_started")
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    photo_urls: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    recorded_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    child: Mapped["Child"] = relationship("Child", back_populates="progress_entries")
    milestone: Mapped["Milestone | None"] = relationship(
        "Milestone", back_populates="progress_entries"
    )
    activity: Mapped["Activity | None"] = relationship(
        "Activity", back_populates="progress_entries"
    )

    __table_args__ = (
        CheckConstraint(
            "(milestone_id IS NOT NULL AND activity_id IS NULL) OR "
            "(milestone_id IS NULL AND activity_id IS NOT NULL)",
            name="check_progress_type",
        ),
    )
