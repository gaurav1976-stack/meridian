"""Auth router — currently just `/auth/me` which the frontend uses to bootstrap.

Token issuance is delegated to the upstream IdP (Cognito / Entra ID / Keycloak);
Meridian only validates tokens server-side (see `app.core.security`).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import CurrentPrincipal, get_current_principal
from app.db.session import get_db
from app.models.core import User
from app.schemas.auth import MeResponse

router = APIRouter()


@router.get("/me", response_model=MeResponse)
def me(
    principal: CurrentPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
) -> MeResponse:
    user = db.query(User).filter(User.id == principal.user_id).one()
    return MeResponse(
        user_id=user.id,
        tenant_id=user.tenant_id,
        email=user.email,
        name=user.name,
        role=principal.role,
    )
