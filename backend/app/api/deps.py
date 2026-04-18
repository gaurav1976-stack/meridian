"""Shared FastAPI dependencies — DB session, current principal, project lookups."""
from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.security import decode_and_validate_token, dev_bypass_enabled, extract_bearer
from app.db.session import get_db
from app.models.core import Project, Tenant, User
from app.models.enums import UserRole


@dataclass
class CurrentPrincipal:
    user_id: str
    tenant_id: str
    email: str
    role: UserRole


def get_current_principal(
    request: Request,
    db: Session = Depends(get_db),
) -> CurrentPrincipal:
    """Resolve the authenticated principal.

    In dev-bypass mode, returns the first seeded admin/tenant.
    In prod mode, validates the bearer JWT and resolves the matching User record.
    """
    token = extract_bearer(request)

    if token is None:
        if not dev_bypass_enabled():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header missing.",
            )
        tenant = db.query(Tenant).first()
        user = db.query(User).filter(User.role == UserRole.tenant_admin).first() or db.query(User).first()
        if tenant is None or user is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Seed state missing — run `python -m app.seed`.",
            )
        return CurrentPrincipal(
            user_id=user.id,
            tenant_id=tenant.id,
            email=user.email,
            role=UserRole(user.role),
        )

    claims = decode_and_validate_token(token)
    user = db.query(User).filter(User.email == claims.email).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No Meridian user mapped to this identity.",
        )
    return CurrentPrincipal(
        user_id=user.id,
        tenant_id=user.tenant_id,
        email=user.email,
        role=UserRole(user.role),
    )


def get_project_for_view(
    project_id: str,
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    if project.tenant_id != principal.tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cross-tenant access denied.")
    return project


def get_project_for_edit(
    project_id: str,
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> Project:
    from app.core.permissions import assert_project_edit_access

    project = get_project_for_view(project_id, db, principal)
    assert_project_edit_access(
        db,
        user_role=principal.role,
        user_tenant_id=principal.tenant_id,
        project_tenant_id=project.tenant_id,
    )
    return project


def get_project_for_admin(
    project_id: str,
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> Project:
    from app.core.permissions import assert_project_admin_access

    project = get_project_for_view(project_id, db, principal)
    assert_project_admin_access(
        db,
        user_role=principal.role,
        user_tenant_id=principal.tenant_id,
        project_tenant_id=project.tenant_id,
    )
    return project
