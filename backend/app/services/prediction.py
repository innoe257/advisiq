from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.ml.model_loader import RiskModel, build_feature_vector
from app.models.risk_score import RiskScore, Tier
from app.models.student import Student


def score_to_tier(score: float) -> Tier:
    settings = get_settings()
    if score >= settings.high_risk_threshold:
        return Tier.high
    if score >= settings.medium_risk_threshold:
        return Tier.medium
    return Tier.low


async def score_students(
    db: AsyncSession, students: list[Student], model: RiskModel
) -> list[RiskScore]:
    """Scores a batch of students and stages a RiskScore row for each.

    Does not commit — the caller owns the transaction boundary.
    """
    if not students:
        return []

    settings = get_settings()
    feature_rows = [
        build_feature_vector(
            gpa=student.gpa,
            attendance_rate=student.attendance_rate,
            year_of_study=student.year_of_study,
            age=student.age,
            credits_attempted=student.credits_attempted,
            credits_completed=student.credits_completed,
        )
        for student in students
    ]
    scores = model.predict_proba(feature_rows)

    risk_scores = []
    for student, score in zip(students, scores, strict=True):
        risk_score = RiskScore(
            student_id=student.id,
            model_version=settings.model_version,
            score=score,
            tier=score_to_tier(score),
        )
        db.add(risk_score)
        risk_scores.append(risk_score)

    await db.flush()
    return risk_scores


async def score_student(db: AsyncSession, student: Student, model: RiskModel) -> RiskScore:
    (risk_score,) = await score_students(db, [student], model)
    return risk_score
