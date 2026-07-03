import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.user import Role


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    email: str
    role: Role
    created_at: datetime
