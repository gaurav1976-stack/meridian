"""Auth / session schemas."""
from __future__ import annotations

from app.models.enums import UserRole
from app.schemas.common import OrmBase


class MeResponse(OrmBase):
    user_id: str
    tenant_id: str
    email: str
    name: str
    role: UserRole
