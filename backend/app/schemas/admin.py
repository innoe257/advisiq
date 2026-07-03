from pydantic import BaseModel, EmailStr, Field

from app.models.user import Role


class AdminUserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: Role
