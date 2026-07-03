import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.intervention import Intervention
    from app.models.risk_score import RiskScore
    from app.models.tenant import Tenant


class Student(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "students"
    __table_args__ = (
        UniqueConstraint("tenant_id", "synth_student_code", name="uq_student_tenant_code"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), index=True
    )
    synth_student_code: Mapped[str] = mapped_column(String(50), index=True)
    programme: Mapped[str] = mapped_column(String(255))
    year_of_study: Mapped[int] = mapped_column(Integer)

    # Representative academic/demographic features used by the risk model.
    gpa: Mapped[float] = mapped_column(Float)
    attendance_rate: Mapped[float] = mapped_column(Float)
    credits_attempted: Mapped[int] = mapped_column(Integer)
    credits_completed: Mapped[int] = mapped_column(Integer)
    age: Mapped[int] = mapped_column(Integer)

    # Catch-all for additional model features without a schema migration per new column.
    extra_features: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)

    tenant: Mapped["Tenant"] = relationship(back_populates="students")
    risk_scores: Mapped[list["RiskScore"]] = relationship(
        back_populates="student", cascade="all, delete-orphan"
    )
    interventions: Mapped[list["Intervention"]] = relationship(
        back_populates="student", cascade="all, delete-orphan"
    )
