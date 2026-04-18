"""Role-aware project access helpers.

Convention:
- `assert_project_view_access`  — any member (incl. Viewer, External Consultant)
- `assert_project_edit_access`  — any member with write role
- `assert_project_admin_access` — Tenant Admin, Programme Director, PMO Director
"""
from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.enums import UserRole

VIEW_ROLES = {
    UserRole.super_admin,
    UserRole.tenant_admin,
    UserRole.programme_director,
    UserRole.pmo_director,
    UserRole.project_director,
    UserRole.controls_manager,
    UserRole.document_controller,
    UserRole.design_manager,
    UserRole.commercial_manager,
    UserRole.risk_manager,
    UserRole.orat_manager,
    UserRole.package_manager,
    UserRole.reviewer_approver,
    UserRole.external_consultant,
    UserRole.contractor_user,
    UserRole.viewer,
}

EDIT_ROLES = VIEW_ROLES - {UserRole.viewer, UserRole.external_consultant, UserRole.contractor_user}

ADMIN_ROLES = {
    UserRole.super_admin,
    UserRole.tenant_admin,
    UserRole.programme_director,
    UserRole.pmo_director,
    UserRole.project_director,
}


def _assert_tenant_match(user_tenant_id: str, project_tenant_id: str) -> None:
    if user_tenant_id != project_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cross-tenant access denied.",
        )


def assert_project_view_access(
    db: Session, *, user_role: UserRole, user_tenant_id: str, project_tenant_id: str
) -> None:
    _ = db  # membership check hook — expand once ProjectMembership is populated
    _assert_tenant_match(user_tenant_id, project_tenant_id)
    if user_role not in VIEW_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="View access denied.")


def assert_project_edit_access(
    db: Session, *, user_role: UserRole, user_tenant_id: str, project_tenant_id: str
) -> None:
    _ = db
    _assert_tenant_match(user_tenant_id, project_tenant_id)
    if user_role not in EDIT_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Edit access denied.")


def assert_project_admin_access(
    db: Session, *, user_role: UserRole, user_tenant_id: str, project_tenant_id: str
) -> None:
    _ = db
    _assert_tenant_match(user_tenant_id, project_tenant_id)
    if user_role not in ADMIN_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access denied.")
