import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession, get_user_by_email
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.auth import AccessTokenResponse, RefreshRequest, RegisterRequest, TokenResponse
from app.schemas.user import UserRead
from app.security import (
    InvalidTokenError,
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


async def _get_or_create_tenant(db: DbSession, tenant_name: str) -> Tenant:
    result = await db.execute(select(Tenant).where(Tenant.name == tenant_name))
    tenant = result.scalar_one_or_none()
    if tenant is None:
        tenant = Tenant(name=tenant_name)
        db.add(tenant)
        await db.flush()
    return tenant


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: DbSession) -> TokenResponse:
    existing_user = await get_user_by_email(db, payload.email)
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists",
        )

    tenant = await _get_or_create_tenant(db, payload.tenant_name)

    user = User(
        tenant_id=tenant.id,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return TokenResponse(
        access_token=create_access_token(user_id=user.id, tenant_id=user.tenant_id, role=user.role),
        refresh_token=create_refresh_token(
            user_id=user.id, tenant_id=user.tenant_id, role=user.role
        ),
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    db: DbSession, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> TokenResponse:
    user = await get_user_by_email(db, form_data.username)
    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return TokenResponse(
        access_token=create_access_token(user_id=user.id, tenant_id=user.tenant_id, role=user.role),
        refresh_token=create_refresh_token(
            user_id=user.id, tenant_id=user.tenant_id, role=user.role
        ),
    )


@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh(payload: RefreshRequest, db: DbSession) -> AccessTokenResponse:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate refresh token",
    )
    try:
        token_payload = decode_token(payload.refresh_token, expected_type=TokenType.refresh)
    except InvalidTokenError as exc:
        raise credentials_error from exc

    user_id = token_payload.get("sub")
    if user_id is None:
        raise credentials_error

    user = await db.get(User, uuid.UUID(user_id))
    if user is None:
        raise credentials_error

    return AccessTokenResponse(
        access_token=create_access_token(user_id=user.id, tenant_id=user.tenant_id, role=user.role)
    )


@router.get("/me", response_model=UserRead)
async def me(current_user: CurrentUser) -> User:
    return current_user
