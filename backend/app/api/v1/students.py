import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import AdminUser, CurrentUser, DbSession, get_tenant_student_or_404
from app.models.student import Student
from app.schemas.student import StudentCreate, StudentRead, StudentUpdate

router = APIRouter(prefix="/students", tags=["students"])


@router.post("", response_model=StudentRead, status_code=status.HTTP_201_CREATED)
async def create_student(
    payload: StudentCreate,
    db: DbSession,
    current_user: AdminUser,
) -> Student:
    existing = await db.execute(
        select(Student).where(
            Student.tenant_id == current_user.tenant_id,
            Student.synth_student_code == payload.synth_student_code,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A student with this synth_student_code already exists for this tenant",
        )

    student = Student(tenant_id=current_user.tenant_id, **payload.model_dump())
    db.add(student)
    await db.commit()
    await db.refresh(student)
    return student


@router.get("", response_model=list[StudentRead])
async def list_students(
    db: DbSession,
    current_user: CurrentUser,
    programme: str | None = None,
    year_of_study: int | None = None,
) -> list[Student]:
    query = select(Student).where(Student.tenant_id == current_user.tenant_id)
    if programme is not None:
        query = query.where(Student.programme == programme)
    if year_of_study is not None:
        query = query.where(Student.year_of_study == year_of_study)

    result = await db.execute(query.order_by(Student.synth_student_code))
    return list(result.scalars().all())


@router.get("/{student_id}", response_model=StudentRead)
async def get_student(student_id: uuid.UUID, db: DbSession, current_user: CurrentUser) -> Student:
    return await get_tenant_student_or_404(db, student_id, current_user.tenant_id)


@router.patch("/{student_id}", response_model=StudentRead)
async def update_student(
    student_id: uuid.UUID,
    payload: StudentUpdate,
    db: DbSession,
    current_user: AdminUser,
) -> Student:
    student = await get_tenant_student_or_404(db, student_id, current_user.tenant_id)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(student, field, value)

    await db.commit()
    await db.refresh(student)
    return student


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_student(
    student_id: uuid.UUID,
    db: DbSession,
    current_user: AdminUser,
) -> None:
    student = await get_tenant_student_or_404(db, student_id, current_user.tenant_id)
    await db.delete(student)
    await db.commit()
