"""Meetings, Actions & Compliance router.

Port of `meridian_track_a_9_meetings_actions_compliance_persistence.py` FastAPI
handlers into a single project-scoped APIRouter at
`/projects/{project_id}/meetings`. Sub-resources live under the same project
prefix:

- ``""``                     — meeting register (list, create, patch)
- ``"/actions"``             — cross-module action tracker
- ``"/compliance-items"``    — compliance register
- ``"/summary"``             — project-wide accountability rollup
- ``"/action-pressure"``     — per-package action load heat-map

Tenant isolation via `get_project_for_view/edit`; audit-log on every mutation;
single commit per request. Patch routes are kept project-scoped (unlike the
loose Track A prototype) so tenant_id can never be bypassed via a bare id.

Meridian Airport PMO suite
(c) GV Softwares. Developed by Gaurav Vatsa. All rights reserved.
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import (
    CurrentPrincipal,
    get_current_principal,
    get_project_for_edit,
    get_project_for_view,
)
from app.db.session import get_db
from app.models.accountability import ActionItem, ComplianceItem, MeetingRecord
from app.models.core import Project, WorkPackage
from app.models.enums import (
    ActionPriority,
    ActionStatus,
    ComplianceDomain,
    ComplianceStatus,
    MeetingType,
)
from app.schemas.accountability import (
    AccountabilitySummary,
    ActionItemCreate,
    ActionItemRead,
    ActionItemUpdate,
    ComplianceItemCreate,
    ComplianceItemRead,
    ComplianceItemUpdate,
    MeetingRecordCreate,
    MeetingRecordRead,
    MeetingRecordUpdate,
    PackageActionPressure,
)
from app.services.audit import write_audit_log

router = APIRouter(prefix="/projects/{project_id}/meetings")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _validate_work_package(
    db: Session, tenant_id: str, project_id: str, package_id: str
) -> WorkPackage:
    pkg = (
        db.query(WorkPackage)
        .filter(
            WorkPackage.id == package_id,
            WorkPackage.project_id == project_id,
            WorkPackage.tenant_id == tenant_id,
        )
        .first()
    )
    if pkg is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Work package {package_id} not found for project.",
        )
    return pkg


# ---------------------------------------------------------------------------
# Meeting register
# ---------------------------------------------------------------------------


@router.get("", response_model=List[MeetingRecordRead])
def list_meetings(
    meeting_type: Optional[MeetingType] = Query(default=None),
    project: Project = Depends(get_project_for_view),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> List[MeetingRecordRead]:
    q = db.query(MeetingRecord).filter(
        MeetingRecord.project_id == project.id,
        MeetingRecord.tenant_id == principal.tenant_id,
    )
    if meeting_type is not None:
        q = q.filter(MeetingRecord.meeting_type == meeting_type)
    rows = q.order_by(MeetingRecord.month.desc(), MeetingRecord.ref.asc()).all()
    return [MeetingRecordRead.model_validate(r) for r in rows]


@router.post(
    "",
    response_model=MeetingRecordRead,
    status_code=status.HTTP_201_CREATED,
)
def create_meeting(
    payload: MeetingRecordCreate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> MeetingRecordRead:
    duplicate = (
        db.query(MeetingRecord)
        .filter(
            MeetingRecord.project_id == project.id,
            MeetingRecord.tenant_id == principal.tenant_id,
            MeetingRecord.ref == payload.ref,
        )
        .first()
    )
    if duplicate is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Meeting ref {payload.ref!r} already exists in project.",
        )

    item = MeetingRecord(
        tenant_id=principal.tenant_id,
        project_id=project.id,
        ref=payload.ref,
        title=payload.title,
        meeting_type=payload.meeting_type,
        month=payload.month,
        chair=payload.chair,
        attendee_count=payload.attendee_count,
        linked_module=payload.linked_module,
    )
    db.add(item)
    db.flush()
    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="MeetingRecord",
        entity_id=item.id,
        action="created",
        details={
            "ref": item.ref,
            "meeting_type": item.meeting_type.value,
            "month": item.month,
        },
    )
    db.commit()
    db.refresh(item)
    return MeetingRecordRead.model_validate(item)


@router.patch("/{meeting_id}", response_model=MeetingRecordRead)
def update_meeting(
    meeting_id: str,
    payload: MeetingRecordUpdate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> MeetingRecordRead:
    item = (
        db.query(MeetingRecord)
        .filter(
            MeetingRecord.id == meeting_id,
            MeetingRecord.project_id == project.id,
            MeetingRecord.tenant_id == principal.tenant_id,
        )
        .first()
    )
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found."
        )
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(item, field, value)
    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="MeetingRecord",
        entity_id=item.id,
        action="updated",
        details=data,
    )
    db.commit()
    db.refresh(item)
    return MeetingRecordRead.model_validate(item)


# ---------------------------------------------------------------------------
# Action tracker
# ---------------------------------------------------------------------------


@router.get("/actions", response_model=List[ActionItemRead])
def list_actions(
    status_filter: Optional[ActionStatus] = Query(default=None, alias="status"),
    priority: Optional[ActionPriority] = Query(default=None),
    project: Project = Depends(get_project_for_view),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> List[ActionItemRead]:
    q = db.query(ActionItem).filter(
        ActionItem.project_id == project.id,
        ActionItem.tenant_id == principal.tenant_id,
    )
    if status_filter is not None:
        q = q.filter(ActionItem.status == status_filter)
    if priority is not None:
        q = q.filter(ActionItem.priority == priority)
    rows = q.order_by(ActionItem.due_month.asc(), ActionItem.ref.asc()).all()
    return [ActionItemRead.model_validate(r) for r in rows]


@router.post(
    "/actions",
    response_model=ActionItemRead,
    status_code=status.HTTP_201_CREATED,
)
def create_action(
    payload: ActionItemCreate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> ActionItemRead:
    if payload.package_id is not None:
        _validate_work_package(
            db, principal.tenant_id, project.id, payload.package_id
        )

    duplicate = (
        db.query(ActionItem)
        .filter(
            ActionItem.project_id == project.id,
            ActionItem.tenant_id == principal.tenant_id,
            ActionItem.ref == payload.ref,
        )
        .first()
    )
    if duplicate is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Action ref {payload.ref!r} already exists in project.",
        )

    item = ActionItem(
        tenant_id=principal.tenant_id,
        project_id=project.id,
        package_id=payload.package_id,
        ref=payload.ref,
        title=payload.title,
        owner=payload.owner,
        source_type=payload.source_type,
        source_ref=payload.source_ref,
        priority=payload.priority,
        due_month=payload.due_month,
        status=payload.status,
        closure_evidence_pct=payload.closure_evidence_pct,
    )
    db.add(item)
    db.flush()
    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="ActionItem",
        entity_id=item.id,
        action="created",
        details={
            "ref": item.ref,
            "source_type": item.source_type.value,
            "priority": item.priority.value,
        },
    )
    db.commit()
    db.refresh(item)
    return ActionItemRead.model_validate(item)


@router.patch("/actions/{action_id}", response_model=ActionItemRead)
def update_action(
    action_id: str,
    payload: ActionItemUpdate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> ActionItemRead:
    item = (
        db.query(ActionItem)
        .filter(
            ActionItem.id == action_id,
            ActionItem.project_id == project.id,
            ActionItem.tenant_id == principal.tenant_id,
        )
        .first()
    )
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Action not found."
        )
    data = payload.model_dump(exclude_unset=True)
    if "package_id" in data and data["package_id"]:
        _validate_work_package(
            db, principal.tenant_id, project.id, data["package_id"]
        )
    for field, value in data.items():
        setattr(item, field, value)
    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="ActionItem",
        entity_id=item.id,
        action="updated",
        details=data,
    )
    db.commit()
    db.refresh(item)
    return ActionItemRead.model_validate(item)


# ---------------------------------------------------------------------------
# Compliance register
# ---------------------------------------------------------------------------


@router.get("/compliance-items", response_model=List[ComplianceItemRead])
def list_compliance_items(
    status_filter: Optional[ComplianceStatus] = Query(default=None, alias="status"),
    domain: Optional[ComplianceDomain] = Query(default=None),
    project: Project = Depends(get_project_for_view),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> List[ComplianceItemRead]:
    q = db.query(ComplianceItem).filter(
        ComplianceItem.project_id == project.id,
        ComplianceItem.tenant_id == principal.tenant_id,
    )
    if status_filter is not None:
        q = q.filter(ComplianceItem.status == status_filter)
    if domain is not None:
        q = q.filter(ComplianceItem.domain == domain)
    rows = q.order_by(ComplianceItem.due_month.asc(), ComplianceItem.ref.asc()).all()
    return [ComplianceItemRead.model_validate(r) for r in rows]


@router.post(
    "/compliance-items",
    response_model=ComplianceItemRead,
    status_code=status.HTTP_201_CREATED,
)
def create_compliance_item(
    payload: ComplianceItemCreate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> ComplianceItemRead:
    if payload.package_id is not None:
        _validate_work_package(
            db, principal.tenant_id, project.id, payload.package_id
        )

    duplicate = (
        db.query(ComplianceItem)
        .filter(
            ComplianceItem.project_id == project.id,
            ComplianceItem.tenant_id == principal.tenant_id,
            ComplianceItem.ref == payload.ref,
        )
        .first()
    )
    if duplicate is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Compliance ref {payload.ref!r} already exists in project.",
        )

    item = ComplianceItem(
        tenant_id=principal.tenant_id,
        project_id=project.id,
        package_id=payload.package_id,
        ref=payload.ref,
        title=payload.title,
        domain=payload.domain,
        owner=payload.owner,
        due_month=payload.due_month,
        status=payload.status,
        evidence_pct=payload.evidence_pct,
    )
    db.add(item)
    db.flush()
    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="ComplianceItem",
        entity_id=item.id,
        action="created",
        details={
            "ref": item.ref,
            "domain": item.domain.value,
            "owner": item.owner,
        },
    )
    db.commit()
    db.refresh(item)
    return ComplianceItemRead.model_validate(item)


@router.patch("/compliance-items/{compliance_id}", response_model=ComplianceItemRead)
def update_compliance_item(
    compliance_id: str,
    payload: ComplianceItemUpdate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> ComplianceItemRead:
    item = (
        db.query(ComplianceItem)
        .filter(
            ComplianceItem.id == compliance_id,
            ComplianceItem.project_id == project.id,
            ComplianceItem.tenant_id == principal.tenant_id,
        )
        .first()
    )
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Compliance item not found."
        )
    data = payload.model_dump(exclude_unset=True)
    if "package_id" in data and data["package_id"]:
        _validate_work_package(
            db, principal.tenant_id, project.id, data["package_id"]
        )
    for field, value in data.items():
        setattr(item, field, value)
    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="ComplianceItem",
        entity_id=item.id,
        action="updated",
        details=data,
    )
    db.commit()
    db.refresh(item)
    return ComplianceItemRead.model_validate(item)


# ---------------------------------------------------------------------------
# Rollups
# ---------------------------------------------------------------------------


@router.get("/summary", response_model=AccountabilitySummary)
def accountability_summary(
    project: Project = Depends(get_project_for_view),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> AccountabilitySummary:
    meetings = (
        db.query(MeetingRecord)
        .filter(
            MeetingRecord.project_id == project.id,
            MeetingRecord.tenant_id == principal.tenant_id,
        )
        .all()
    )
    actions = (
        db.query(ActionItem)
        .filter(
            ActionItem.project_id == project.id,
            ActionItem.tenant_id == principal.tenant_id,
        )
        .all()
    )
    compliance = (
        db.query(ComplianceItem)
        .filter(
            ComplianceItem.project_id == project.id,
            ComplianceItem.tenant_id == principal.tenant_id,
        )
        .all()
    )

    open_actions = sum(
        1
        for a in actions
        if a.status
        in {
            ActionStatus.open,
            ActionStatus.in_progress,
            ActionStatus.awaiting_review,
        }
    )
    overdue_actions = sum(1 for a in actions if a.status == ActionStatus.overdue)
    avg_closure = (
        round(sum(a.closure_evidence_pct for a in actions) / len(actions))
        if actions
        else 0
    )
    non_compliant = sum(
        1
        for c in compliance
        if c.status in {ComplianceStatus.non_compliant, ComplianceStatus.overdue}
    )
    compliant = sum(1 for c in compliance if c.status == ComplianceStatus.compliant)

    return AccountabilitySummary(
        project_id=project.id,
        meeting_count=len(meetings),
        action_count=len(actions),
        compliance_count=len(compliance),
        open_action_count=open_actions,
        overdue_action_count=overdue_actions,
        average_closure_evidence_pct=avg_closure,
        compliant_count=compliant,
        non_compliant_count=non_compliant,
    )


@router.get("/action-pressure", response_model=List[PackageActionPressure])
def action_pressure(
    project: Project = Depends(get_project_for_view),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> List[PackageActionPressure]:
    packages = (
        db.query(WorkPackage)
        .filter(
            WorkPackage.project_id == project.id,
            WorkPackage.tenant_id == principal.tenant_id,
        )
        .order_by(WorkPackage.code.asc())
        .all()
    )
    actions = (
        db.query(ActionItem)
        .filter(
            ActionItem.project_id == project.id,
            ActionItem.tenant_id == principal.tenant_id,
        )
        .all()
    )

    results: List[PackageActionPressure] = []
    for pkg in packages:
        pkg_actions = [a for a in actions if a.package_id == pkg.id]
        avg = (
            round(sum(a.closure_evidence_pct for a in pkg_actions) / len(pkg_actions))
            if pkg_actions
            else 0
        )
        results.append(
            PackageActionPressure(
                package_id=pkg.id,
                package_code=pkg.code,
                package_name=pkg.name,
                action_count=len(pkg_actions),
                overdue_count=sum(
                    1 for a in pkg_actions if a.status == ActionStatus.overdue
                ),
                critical_count=sum(
                    1
                    for a in pkg_actions
                    if a.priority == ActionPriority.critical
                ),
                average_closure_evidence_pct=avg,
            )
        )
    return results
