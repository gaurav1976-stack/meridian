"""Projects + work-package CRUD + dashboard summary.

Reference router for the conversion playbook — every other domain follows
this exact shape: list / create (admin) / get / update / delete + a
domain-specific roll-up endpoint.
"""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import (
    CurrentPrincipal,
    get_current_principal,
    get_project_for_admin,
    get_project_for_edit,
    get_project_for_view,
)
from app.core.permissions import assert_project_admin_access
from app.db.session import get_db
from app.models.core import Project, WorkPackage
from app.models.project_setup import Contract
from app.models.risk import RiskItem
from app.models.schedule import ScheduleActivity
from app.models.enums import RiskStatus
from app.schemas.projects import (
    DashboardCounts,
    ProjectCreate,
    ProjectDashboard,
    ProjectRead,
    ProjectUpdate,
    WorkPackageCreate,
    WorkPackageRead,
    WorkPackageUpdate,
)
from app.services.audit import write_audit_log

router = APIRouter()


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------


@router.get("", response_model=List[ProjectRead])
def list_projects(
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> List[ProjectRead]:
    rows = (
        db.query(Project)
        .filter(Project.tenant_id == principal.tenant_id)
        .order_by(Project.code)
        .all()
    )
    return [ProjectRead.model_validate(r) for r in rows]


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> ProjectRead:
    # Project creation is an admin-only action — no project_id yet so we use the
    # tenant-scoped admin check.
    assert_project_admin_access(
        db,
        user_role=principal.role,
        user_tenant_id=principal.tenant_id,
        project_tenant_id=principal.tenant_id,
    )
    duplicate = (
        db.query(Project)
        .filter(Project.tenant_id == principal.tenant_id, Project.code == payload.code)
        .first()
    )
    if duplicate is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Project code '{payload.code}' already exists in this tenant.",
        )
    project = Project(tenant_id=principal.tenant_id, **payload.model_dump())
    db.add(project)
    db.flush()
    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="Project",
        entity_id=project.id,
        action="created",
        details=payload.model_dump(),
    )
    db.commit()
    db.refresh(project)
    return ProjectRead.model_validate(project)


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(project: Project = Depends(get_project_for_view)) -> ProjectRead:
    return ProjectRead.model_validate(project)


@router.patch("/{project_id}", response_model=ProjectRead)
def update_project(
    payload: ProjectUpdate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> ProjectRead:
    changes = payload.model_dump(exclude_unset=True)
    for key, value in changes.items():
        setattr(project, key, value)
    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="Project",
        entity_id=project.id,
        action="updated",
        details=changes,
    )
    db.commit()
    db.refresh(project)
    return ProjectRead.model_validate(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project: Project = Depends(get_project_for_admin),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> None:
    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="Project",
        entity_id=project.id,
        action="deleted",
    )
    db.delete(project)
    db.commit()


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------


@router.get("/{project_id}/dashboard", response_model=ProjectDashboard)
def project_dashboard(
    project: Project = Depends(get_project_for_view),
    db: Session = Depends(get_db),
) -> ProjectDashboard:
    counts = DashboardCounts(
        work_packages=db.query(WorkPackage).filter(WorkPackage.project_id == project.id).count(),
        contracts=db.query(Contract).filter(Contract.project_id == project.id).count(),
        open_risks=db.query(RiskItem)
        .filter(RiskItem.project_id == project.id, RiskItem.status != RiskStatus.closed)
        .count(),
        schedule_activities=db.query(ScheduleActivity)
        .filter(ScheduleActivity.project_id == project.id)
        .count(),
        activities_critical=db.query(ScheduleActivity)
        .filter(ScheduleActivity.project_id == project.id, ScheduleActivity.is_critical.is_(True))
        .count(),
    )
    return ProjectDashboard(project=ProjectRead.model_validate(project), counts=counts)


# ---------------------------------------------------------------------------
# Work packages (nested under projects)
# ---------------------------------------------------------------------------


@router.get("/{project_id}/work-packages", response_model=List[WorkPackageRead])
def list_work_packages(
    project: Project = Depends(get_project_for_view),
    db: Session = Depends(get_db),
) -> List[WorkPackageRead]:
    rows = (
        db.query(WorkPackage)
        .filter(WorkPackage.project_id == project.id)
        .order_by(WorkPackage.code)
        .all()
    )
    return [WorkPackageRead.model_validate(r) for r in rows]


@router.post(
    "/{project_id}/work-packages",
    response_model=WorkPackageRead,
    status_code=status.HTTP_201_CREATED,
)
def create_work_package(
    payload: WorkPackageCreate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> WorkPackageRead:
    duplicate = (
        db.query(WorkPackage)
        .filter(WorkPackage.project_id == project.id, WorkPackage.code == payload.code)
        .first()
    )
    if duplicate is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Work package code '{payload.code}' already exists for this project.",
        )
    data = payload.model_dump()
    # Persist enum values as raw strings to keep the simple String column happy.
    if data.get("package_type") is not None:
        data["package_type"] = data["package_type"].value
    if data.get("status") is not None:
        data["status"] = data["status"].value
    pkg = WorkPackage(tenant_id=principal.tenant_id, project_id=project.id, **data)
    db.add(pkg)
    db.flush()
    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="WorkPackage",
        entity_id=pkg.id,
        action="created",
        details=data,
    )
    db.commit()
    db.refresh(pkg)
    return WorkPackageRead.model_validate(pkg)


@router.patch(
    "/{project_id}/work-packages/{package_id}", response_model=WorkPackageRead
)
def update_work_package(
    package_id: str,
    payload: WorkPackageUpdate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> WorkPackageRead:
    pkg = (
        db.query(WorkPackage)
        .filter(WorkPackage.id == package_id, WorkPackage.project_id == project.id)
        .first()
    )
    if pkg is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Work package not found.")
    changes = payload.model_dump(exclude_unset=True)
    if "package_type" in changes and changes["package_type"] is not None:
        changes["package_type"] = changes["package_type"].value
    if "status" in changes and changes["status"] is not None:
        changes["status"] = changes["status"].value
    for key, value in changes.items():
        setattr(pkg, key, value)
    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="WorkPackage",
        entity_id=pkg.id,
        action="updated",
        details=changes,
    )
    db.commit()
    db.refresh(pkg)
    return WorkPackageRead.model_validate(pkg)
