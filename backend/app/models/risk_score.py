import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, String, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.student import Student


class Tier(enum.StrEnum):
    low = "low"
    medium = "medium"
    high = "high"


class RiskScore(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "risk_scores"

    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id"), index=True
    )
    model_version: Mapped[str] = mapped_column(String(50))
    score: Mapped[float] = mapped_column(Float)
    tier: Mapped[Tier] = mapped_column(SAEnum(Tier, name="risk_tier"))
    scored_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    student: Mapped["Student"] = relationship(back_populates="risk_scores")
