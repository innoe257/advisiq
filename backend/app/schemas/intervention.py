import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.intervention import InterventionStatus


class InterventionCreate(BaseModel):
    type: str = Field(min_length=1, max_length=100)
    notes: str = Field(default="", max_length=5000)
    status: InterventionStatus = InterventionStatus.open


class InterventionUpdate(BaseModel):
    type: str | None = Field(default=None, min_length=1, max_length=100)
    notes: str | None = Field(default=None, max_length=5000)
    status: InterventionStatus | None = None


class InterventionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    student_id: uuid.UUID
    advisor_id: uuid.UUID
    type: str
    notes: str
    status: InterventionStatus
    created_at: datetime
