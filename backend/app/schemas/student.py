import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class StudentCreate(BaseModel):
    synth_student_code: str = Field(min_length=1, max_length=50, pattern=r"^SYNTH.*")
    programme: str = Field(min_length=1, max_length=255)
    year_of_study: int = Field(ge=1, le=8)
    gpa: float = Field(ge=0.0, le=4.0)
    attendance_rate: float = Field(ge=0.0, le=1.0)
    credits_attempted: int = Field(ge=0)
    credits_completed: int = Field(ge=0)
    age: int = Field(ge=15, le=100)
    extra_features: dict[str, Any] = Field(default_factory=dict)


class StudentUpdate(BaseModel):
    programme: str | None = Field(default=None, min_length=1, max_length=255)
    year_of_study: int | None = Field(default=None, ge=1, le=8)
    gpa: float | None = Field(default=None, ge=0.0, le=4.0)
    attendance_rate: float | None = Field(default=None, ge=0.0, le=1.0)
    credits_attempted: int | None = Field(default=None, ge=0)
    credits_completed: int | None = Field(default=None, ge=0)
    age: int | None = Field(default=None, ge=15, le=100)
    extra_features: dict[str, Any] | None = None


class StudentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    synth_student_code: str
    programme: str
    year_of_study: int
    gpa: float
    attendance_rate: float
    credits_attempted: int
    credits_completed: int
    age: int
    extra_features: dict[str, Any]
    created_at: datetime
