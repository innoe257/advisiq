from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.student import Student
    from app.models.user import User


class Tenant(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "tenants"

    name: Mapped[str] = mapped_column(String(255), unique=True)

    users: Mapped[list["User"]] = relationship(back_populates="tenant")
    students: Mapped[list["Student"]] = relationship(back_populates="tenant")
