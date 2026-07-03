import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select

from app.api.deps import AdminUser, CurrentUser, DbSession, get_tenant_student_or_404
from app.config import get_settings
from app.ml.model_loader import RiskModel, load_model
from app.models.risk_score import RiskScore, Tier
from app.models.student import Student
from app.schemas.risk import (
    BatchScoreRequest,
    BatchScoreResponse,
    CohortRiskSummary,
    CohortTierCounts,
    RiskScoreRead,
)
from app.services.prediction import score_students

router = APIRouter(tags=["risk"])

ModelDependency = Annotated[RiskModel, Depends(load_model)]


@router.post("/risk/score", response_model=BatchScoreResponse)
async def trigger_batch_scoring(
    payload: BatchScoreRequest,
    db: DbSession,
    current_user: AdminUser,
    model: ModelDependency,
) -> BatchScoreResponse:
    query = select(Student).where(Student.tenant_id == current_user.tenant_id)
    if payload.student_ids is not None:
        query = query.where(Student.id.in_(payload.student_ids))

    result = await db.execute(query)
    students = list(result.scalars().all())

    risk_scores = await score_students(db, students, model)
    await db.commit()

    return BatchScoreResponse(
        scored_count=len(risk_scores), model_version=get_settings().model_version
    )


@router.get("/students/{student_id}/risk-scores", response_model=list[RiskScoreRead])
async def get_student_risk_scores(
    student_id: uuid.UUID, db: DbSession, current_user: CurrentUser
) -> list[RiskScore]:
    student = await get_tenant_student_or_404(db, student_id, current_user.tenant_id)

    result = await db.execute(
        select(RiskScore)
        .where(RiskScore.student_id == student.id)
        .order_by(RiskScore.scored_at.desc())
    )
    return list(result.scalars().all())


@router.get("/risk/cohort", response_model=CohortRiskSummary)
async def get_cohort_risk_summary(
    db: DbSession,
    current_user: CurrentUser,
    programme: str | None = None,
    year_of_study: int | None = None,
) -> CohortRiskSummary:
    """Tier counts based on each student's most recent risk score only —
    students scored multiple times over time aren't double-counted."""
    latest_rank = func.row_number().over(
        partition_by=RiskScore.student_id, order_by=RiskScore.scored_at.desc()
    )

    ranked_scores = (
        select(RiskScore.tier, latest_rank.label("rank"))
        .join(Student, RiskScore.student_id == Student.id)
        .where(Student.tenant_id == current_user.tenant_id)
    )
    if programme is not None:
        ranked_scores = ranked_scores.where(Student.programme == programme)
    if year_of_study is not None:
        ranked_scores = ranked_scores.where(Student.year_of_study == year_of_study)
    subquery = ranked_scores.subquery()

    result = await db.execute(select(subquery.c.tier).where(subquery.c.rank == 1))
    tiers = list(result.scalars().all())

    counts = CohortTierCounts(
        low=tiers.count(Tier.low),
        medium=tiers.count(Tier.medium),
        high=tiers.count(Tier.high),
        total=len(tiers),
    )
    return CohortRiskSummary(tier_counts=counts, programme=programme, year_of_study=year_of_study)
