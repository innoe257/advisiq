from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import AdminUser, DbSession, get_user_by_email
from app.models.user import User
from app.schemas.admin import AdminUserCreate
from app.schemas.user import UserRead
from app.security import hash_password

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=list[UserRead])
async def list_users(db: DbSession, current_user: AdminUser) -> list[User]:
    result = await db.execute(
        select(User).where(User.tenant_id == current_user.tenant_id).order_by(User.email)
    )
    return list(result.scalars().all())


@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(payload: AdminUserCreate, db: DbSession, current_user: AdminUser) -> User:
    existing_user = await get_user_by_email(db, payload.email)
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists",
        )

    user = User(
        tenant_id=current_user.tenant_id,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
