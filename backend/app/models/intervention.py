import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.student import Student
    from app.models.user import User


class InterventionStatus(enum.StrEnum):
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"


class Intervention(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "interventions"

    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id"), index=True
    )
    advisor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), index=True
    )
    type: Mapped[str] = mapped_column(String(100))
    notes: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[InterventionStatus] = mapped_column(
        SAEnum(InterventionStatus, name="intervention_status"),
        default=InterventionStatus.open,
    )

    student: Mapped["Student"] = relationship(back_populates="interventions")
    advisor: Mapped["User"] = relationship(back_populates="interventions")
