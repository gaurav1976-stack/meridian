"""Stage Gate Governance router — gates, evidence, approvals, decisions + readiness rollups.

Port of `meridian_track_a_4_stage_gate_governance_persistence.py` FastAPI handlers
into a single project-scoped APIRouter with tenant isolation through
`get_project_for_view/edit` and audit logging on every write.

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
from app.models.core import Project, WorkPackage
from app.models.enums import EvidenceStatus, GateStatus
from app.models.governance import (
    GateApproval,
    GateDecision,
    GateDefinition,
    GateEvidenceItem,
    GatePackageLink,
)
from app.schemas.governance import (
    GateApprovalCreate,
    GateApprovalRead,
    GateApprovalUpdate,
    GateDecisionCreate,
    GateDecisionRead,
    GateDefinitionCreate,
    GateDefinitionRead,
    GateDefinitionUpdate,
    GateEvidenceCreate,
    GateEvidenceRead,
    GateEvidenceUpdate,
    GateReadinessSummary,
    GovernanceSummary,
)
from app.services.audit import write_audit_log

router = APIRouter(prefix="/projects/{project_id}/stage-gates")


# ---------------------------------------------------------------------------
# Readiness helpers
# ---------------------------------------------------------------------------


def _readiness_score(evidence_items: List[GateEvidenceItem]) -> int:
    """% ready based on required evidence. Accepted = 1.0, Submitted = 0.6, else 0."""
    required = [e for e in evidence_items if e.required]
    if not required:
        return 0
    accepted = sum(1 for e in required if e.status == EvidenceStatus.accepted)
    submitted = sum(1 for e in required if e.status == EvidenceStatus.submitted)
    return round(((accepted + submitted * 0.6) / len(required)) * 100)


def _approval_progress(approvals: List[GateApproval]) -> int:
    if not approvals:
        return 0
    from app.models.enums import ApprovalStatus

    approved = sum(1 for a in approvals if a.status == ApprovalStatus.approved)
    return round((approved / len(approvals)) * 100)


def _get_gate(
    db: Session, tenant_id: str, project_id: str, gate_id: str
) -> GateDefinition:
    gate = (
        db.query(GateDefinition)
        .filter(
            GateDefinition.id == gate_id,
            GateDefinition.tenant_id == tenant_id,
            GateDefinition.project_id == project_id,
        )
        .first()
    )
    if gate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gate not found.")
    return gate


# ---------------------------------------------------------------------------
# Gate definitions
# ---------------------------------------------------------------------------


@router.get("", response_model=List[GateDefinitionRead])
def list_gates(
    status_filter: Optional[GateStatus] = Query(default=None, alias="status"),
    project: Project = Depends(get_project_for_view),
    db: Session = Depends(get_db),
) -> List[GateDefinitionRead]:
    q = db.query(GateDefinition).filter(GateDefinition.project_id == project.id)
    if status_filter is not None:
        q = q.filter(GateDefinition.status == status_filter)
    rows = q.order_by(GateDefinition.target_month.asc()).all()
    return [GateDefinitionRead.model_validate(g) for g in rows]


@router.post("", response_model=GateDefinitionRead, status_code=status.HTTP_201_CREATED)
def create_gate(
    payload: GateDefinitionCreate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> GateDefinitionRead:
    duplicate = (
        db.query(GateDefinition)
        .filter(
            GateDefinition.project_id == project.id,
            GateDefinition.tenant_id == principal.tenant_id,
            GateDefinition.code == payload.code,
        )
        .first()
    )
    if duplicate is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Gate code {payload.code!r} already exists in project.",
        )

    gate = GateDefinition(
        tenant_id=principal.tenant_id,
        project_id=project.id,
        code=payload.code,
        name=payload.name,
        purpose=payload.purpose,
        target_month=payload.target_month,
        status=payload.status,
    )
    db.add(gate)
    db.flush()

    for package_id in payload.package_ids:
        pkg = (
            db.query(WorkPackage)
            .filter(
                WorkPackage.id == package_id,
                WorkPackage.project_id == project.id,
                WorkPackage.tenant_id == principal.tenant_id,
            )
            .first()
        )
        if pkg is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Package {package_id} not found for project.",
            )
        db.add(
            GatePackageLink(
                tenant_id=principal.tenant_id,
                project_id=project.id,
                gate_definition_id=gate.id,
                package_id=package_id,
            )
        )

    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="GateDefinition",
        entity_id=gate.id,
        action="created",
        details={"code": gate.code, "name": gate.name},
    )
    db.commit()
    db.refresh(gate)
    return GateDefinitionRead.model_validate(gate)


@router.patch("/{gate_id}", response_model=GateDefinitionRead)
def update_gate(
    gate_id: str,
    payload: GateDefinitionUpdate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> GateDefinitionRead:
    gate = _get_gate(db, principal.tenant_id, project.id, gate_id)
    changes = payload.model_dump(exclude_unset=True)
    for key, value in changes.items():
        setattr(gate, key, value)
    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="GateDefinition",
        entity_id=gate.id,
        action="updated",
        details=changes,
    )
    db.commit()
    db.refresh(gate)
    return GateDefinitionRead.model_validate(gate)


# ---------------------------------------------------------------------------
# Evidence
# ---------------------------------------------------------------------------


@router.get("/evidence", response_model=List[GateEvidenceRead])
def list_evidence(
    gate_definition_id: Optional[str] = None,
    project: Project = Depends(get_project_for_view),
    db: Session = Depends(get_db),
) -> List[GateEvidenceRead]:
    q = db.query(GateEvidenceItem).filter(GateEvidenceItem.project_id == project.id)
    if gate_definition_id is not None:
        q = q.filter(GateEvidenceItem.gate_definition_id == gate_definition_id)
    rows = q.order_by(GateEvidenceItem.created_at.desc()).all()
    return [GateEvidenceRead.model_validate(r) for r in rows]


@router.post(
    "/evidence",
    response_model=GateEvidenceRead,
    status_code=status.HTTP_201_CREATED,
)
def create_evidence(
    payload: GateEvidenceCreate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> GateEvidenceRead:
    _get_gate(db, principal.tenant_id, project.id, payload.gate_definition_id)
    item = GateEvidenceItem(
        tenant_id=principal.tenant_id,
        project_id=project.id,
        gate_definition_id=payload.gate_definition_id,
        package_id=payload.package_id,
        title=payload.title,
        category=payload.category,
        required=payload.required,
        status=payload.status,
        owner=payload.owner,
    )
    db.add(item)
    db.flush()
    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="GateEvidenceItem",
        entity_id=item.id,
        action="created",
        details={"title": item.title, "gate_definition_id": item.gate_definition_id},
    )
    db.commit()
    db.refresh(item)
    return GateEvidenceRead.model_validate(item)


@router.patch("/evidence/{evidence_id}", response_model=GateEvidenceRead)
def update_evidence(
    evidence_id: str,
    payload: GateEvidenceUpdate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> GateEvidenceRead:
    item = (
        db.query(GateEvidenceItem)
        .filter(
            GateEvidenceItem.id == evidence_id,
            GateEvidenceItem.project_id == project.id,
            GateEvidenceItem.tenant_id == principal.tenant_id,
        )
        .first()
    )
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence item not found.")
    changes = payload.model_dump(exclude_unset=True)
    for key, value in changes.items():
        setattr(item, key, value)
    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="GateEvidenceItem",
        entity_id=item.id,
        action="updated",
        details=changes,
    )
    db.commit()
    db.refresh(item)
    return GateEvidenceRead.model_validate(item)


# ---------------------------------------------------------------------------
# Approvals
# ---------------------------------------------------------------------------


@router.get("/approvals", response_model=List[GateApprovalRead])
def list_approvals(
    gate_definition_id: Optional[str] = None,
    project: Project = Depends(get_project_for_view),
    db: Session = Depends(get_db),
) -> List[GateApprovalRead]:
    q = db.query(GateApproval).filter(GateApproval.project_id == project.id)
    if gate_definition_id is not None:
        q = q.filter(GateApproval.gate_definition_id == gate_definition_id)
    rows = q.order_by(GateApproval.created_at.desc()).all()
    return [GateApprovalRead.model_validate(r) for r in rows]


@router.post(
    "/approvals",
    response_model=GateApprovalRead,
    status_code=status.HTTP_201_CREATED,
)
def create_approval(
    payload: GateApprovalCreate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> GateApprovalRead:
    _get_gate(db, principal.tenant_id, project.id, payload.gate_definition_id)
    item = GateApproval(
        tenant_id=principal.tenant_id,
        project_id=project.id,
        gate_definition_id=payload.gate_definition_id,
        approver=payload.approver,
        role=payload.role,
        status=payload.status,
        response_date=payload.response_date,
    )
    db.add(item)
    db.flush()
    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="GateApproval",
        entity_id=item.id,
        action="created",
        details={"approver": item.approver, "role": item.role},
    )
    db.commit()
    db.refresh(item)
    return GateApprovalRead.model_validate(item)


@router.patch("/approvals/{approval_id}", response_model=GateApprovalRead)
def update_approval(
    approval_id: str,
    payload: GateApprovalUpdate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> GateApprovalRead:
    item = (
        db.query(GateApproval)
        .filter(
            GateApproval.id == approval_id,
            GateApproval.project_id == project.id,
            GateApproval.tenant_id == principal.tenant_id,
        )
        .first()
    )
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval not found.")
    changes = payload.model_dump(exclude_unset=True)
    for key, value in changes.items():
        setattr(item, key, value)
    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="GateApproval",
        entity_id=item.id,
        action="updated",
        details=changes,
    )
    db.commit()
    db.refresh(item)
    return GateApprovalRead.model_validate(item)


# ---------------------------------------------------------------------------
# Decisions
# ---------------------------------------------------------------------------


@router.get("/decisions", response_model=List[GateDecisionRead])
def list_decisions(
    gate_definition_id: Optional[str] = None,
    project: Project = Depends(get_project_for_view),
    db: Session = Depends(get_db),
) -> List[GateDecisionRead]:
    q = db.query(GateDecision).filter(GateDecision.project_id == project.id)
    if gate_definition_id is not None:
        q = q.filter(GateDecision.gate_definition_id == gate_definition_id)
    rows = q.order_by(GateDecision.decision_date.desc()).all()
    return [GateDecisionRead.model_validate(r) for r in rows]


@router.post(
    "/decisions",
    response_model=GateDecisionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_decision(
    payload: GateDecisionCreate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> GateDecisionRead:
    _get_gate(db, principal.tenant_id, project.id, payload.gate_definition_id)
    item = GateDecision(
        tenant_id=principal.tenant_id,
        project_id=project.id,
        gate_definition_id=payload.gate_definition_id,
        meeting_ref=payload.meeting_ref,
        decision_date=payload.decision_date,
        outcome=payload.outcome,
        summary=payload.summary,
    )
    db.add(item)
    db.flush()
    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="GateDecision",
        entity_id=item.id,
        action="created",
        details={
            "outcome": item.outcome.value,
            "meeting_ref": item.meeting_ref,
        },
    )
    db.commit()
    db.refresh(item)
    return GateDecisionRead.model_validate(item)


# ---------------------------------------------------------------------------
# Rollups
# ---------------------------------------------------------------------------


@router.get("/{gate_id}/readiness", response_model=GateReadinessSummary)
def gate_readiness(
    gate_id: str,
    project: Project = Depends(get_project_for_view),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> GateReadinessSummary:
    gate = _get_gate(db, principal.tenant_id, project.id, gate_id)
    evidence_items = (
        db.query(GateEvidenceItem)
        .filter(
            GateEvidenceItem.project_id == project.id,
            GateEvidenceItem.gate_definition_id == gate_id,
        )
        .all()
    )
    approvals = (
        db.query(GateApproval)
        .filter(
            GateApproval.project_id == project.id,
            GateApproval.gate_definition_id == gate_id,
        )
        .all()
    )
    decisions = (
        db.query(GateDecision)
        .filter(
            GateDecision.project_id == project.id,
            GateDecision.gate_definition_id == gate_id,
        )
        .order_by(GateDecision.decision_date.desc())
        .all()
    )
    package_links = (
        db.query(GatePackageLink)
        .filter(
            GatePackageLink.project_id == project.id,
            GatePackageLink.gate_definition_id == gate_id,
        )
        .all()
    )

    return GateReadinessSummary(
        gate_id=gate.id,
        gate_code=gate.code,
        gate_name=gate.name,
        status=gate.status,
        target_month=gate.target_month,
        readiness_score=_readiness_score(evidence_items),
        approval_progress=_approval_progress(approvals),
        blocker_count=sum(
            1
            for e in evidence_items
            if e.required and e.status in {EvidenceStatus.missing, EvidenceStatus.draft}
        ),
        required_evidence_count=sum(1 for e in evidence_items if e.required),
        accepted_evidence_count=sum(1 for e in evidence_items if e.status == EvidenceStatus.accepted),
        submitted_evidence_count=sum(1 for e in evidence_items if e.status == EvidenceStatus.submitted),
        approval_count=len(approvals),
        decision_count=len(decisions),
        linked_package_count=len(package_links),
        latest_decision=decisions[0].outcome.value if decisions else None,
    )


@router.get("/summary", response_model=GovernanceSummary)
def governance_summary(
    project: Project = Depends(get_project_for_view),
    db: Session = Depends(get_db),
) -> GovernanceSummary:
    gates = (
        db.query(GateDefinition)
        .filter(GateDefinition.project_id == project.id)
        .all()
    )
    evidence = (
        db.query(GateEvidenceItem)
        .filter(GateEvidenceItem.project_id == project.id)
        .all()
    )
    approvals = (
        db.query(GateApproval)
        .filter(GateApproval.project_id == project.id)
        .all()
    )
    decisions = (
        db.query(GateDecision)
        .filter(GateDecision.project_id == project.id)
        .all()
    )

    active_gates = sum(1 for g in gates if g.status == GateStatus.active)
    blocked_gates = sum(1 for g in gates if g.status == GateStatus.blocked)
    readiness_avg = (
        round(
            sum(
                _readiness_score([e for e in evidence if e.gate_definition_id == g.id])
                for g in gates
            )
            / len(gates)
        )
        if gates
        else 0
    )

    return GovernanceSummary(
        project_id=project.id,
        gate_count=len(gates),
        active_gates=active_gates,
        blocked_gates=blocked_gates,
        evidence_count=len(evidence),
        approval_count=len(approvals),
        decision_count=len(decisions),
        average_readiness_score=readiness_avg,
    )
