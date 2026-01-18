"""Child model - children being tracked in the curriculum."""

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Child(Base):
    """Child being tracked in the curriculum."""

    __tablename__ = "children"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    family_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("families.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    gender: Mapped[str | None] = mapped_column(String(20), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    family: Mapped["Family"] = relationship("Family", back_populates="children")
    progress_entries: Mapped[list["ChildProgress"]] = relationship(
        "ChildProgress", back_populates="child", cascade="all, delete-orphan"
    )

    @property
    def age_in_months(self) -> int:
        """Calculate current age in months."""
        today = date.today()
        return (today.year - self.date_of_birth.year) * 12 + (
            today.month - self.date_of_birth.month
        )

    @property
    def age_description(self) -> str:
        """Human-readable age description."""
        months = self.age_in_months
        if months < 12:
            return f"{months} month{'s' if months != 1 else ''}"
        years = months // 12
        remaining_months = months % 12
        if remaining_months == 0:
            return f"{years} year{'s' if years != 1 else ''}"
        return f"{years} year{'s' if years != 1 else ''}, {remaining_months} month{'s' if remaining_months != 1 else ''}"
