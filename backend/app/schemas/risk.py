import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.risk_score import Tier


class RiskScoreRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    student_id: uuid.UUID
    model_version: str
    score: float
    tier: Tier
    scored_at: datetime


class BatchScoreRequest(BaseModel):
    student_ids: list[uuid.UUID] | None = None
    """Score only these students. Omit to score every student in the tenant."""


class BatchScoreResponse(BaseModel):
    scored_count: int
    model_version: str


class CohortTierCounts(BaseModel):
    low: int
    medium: int
    high: int
    total: int


class CohortRiskSummary(BaseModel):
    tier_counts: CohortTierCounts
    programme: str | None = None
    year_of_study: int | None = None
