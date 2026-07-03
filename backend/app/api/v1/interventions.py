import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import AdminUser, CurrentUser, DbSession, get_tenant_student_or_404
from app.models.intervention import Intervention
from app.models.student import Student
from app.schemas.intervention import InterventionCreate, InterventionRead, InterventionUpdate

router = APIRouter(tags=["interventions"])


async def _get_tenant_intervention_or_404(
    db: DbSession, intervention_id: uuid.UUID, tenant_id: uuid.UUID
) -> Intervention:
    result = await db.execute(
        select(Intervention)
        .join(Student, Intervention.student_id == Student.id)
        .where(Intervention.id == intervention_id, Student.tenant_id == tenant_id)
    )
    intervention = result.scalar_one_or_none()
    if intervention is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Intervention not found")
    return intervention


@router.post(
    "/students/{student_id}/interventions",
    response_model=InterventionRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_intervention(
    student_id: uuid.UUID,
    payload: InterventionCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> Intervention:
    student = await get_tenant_student_or_404(db, student_id, current_user.tenant_id)

    intervention = Intervention(
        student_id=student.id, advisor_id=current_user.id, **payload.model_dump()
    )
    db.add(intervention)
    await db.commit()
    await db.refresh(intervention)
    return intervention


@router.get("/students/{student_id}/interventions", response_model=list[InterventionRead])
async def list_student_interventions(
    student_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> list[Intervention]:
    student = await get_tenant_student_or_404(db, student_id, current_user.tenant_id)

    result = await db.execute(
        select(Intervention)
        .where(Intervention.student_id == student.id)
        .order_by(Intervention.created_at.desc())
    )
    return list(result.scalars().all())


@router.patch("/interventions/{intervention_id}", response_model=InterventionRead)
async def update_intervention(
    intervention_id: uuid.UUID,
    payload: InterventionUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> Intervention:
    intervention = await _get_tenant_intervention_or_404(
        db, intervention_id, current_user.tenant_id
    )

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(intervention, field, value)

    await db.commit()
    await db.refresh(intervention)
    return intervention


@router.delete("/interventions/{intervention_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_intervention(
    intervention_id: uuid.UUID,
    db: DbSession,
    current_user: AdminUser,
) -> None:
    intervention = await _get_tenant_intervention_or_404(
        db, intervention_id, current_user.tenant_id
    )
    await db.delete(intervention)
    await db.commit()
