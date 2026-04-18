"""ORAT Readiness & Handover router.

Port of `meridian_track_a_10_orat_readiness_persistence.py` FastAPI handlers
into a single project-scoped APIRouter at `/projects/{project_id}/orat`.
Sub-resources live under the same project prefix:

- ``"/workstreams"``              — ORAT workstream register (progress & RAG)
- ``"/trials"``                   — trial log (tabletop / partial / integrated)
- ``"/training-groups"``          — staff training cohorts by function
- ``"/handover-items"``           — asset-group handover register
- ``"/summary"``                  — project-wide ORAT readiness rollup
- ``"/handover-pressure"``        — per-package handover heat-map

Tenant isolation via `get_project_for_view/edit`; audit-log on every mutation;
single commit per request. Patch routes are kept project-scoped (unlike the
loose Track A prototype's `/orat-workstreams/{id}` handlers) so tenant_id
can never be bypassed via a bare id.

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
from app.models.enums import (
    HandoverStatus,
    OratWorkstreamStatus,
    TrainingStatus,
    TrialStatus,
)
from app.models.orat import HandoverItem, OratTrial, OratWorkstream, TrainingGroup
from app.schemas.orat import (
    HandoverItemCreate,
    HandoverItemRead,
    HandoverItemUpdate,
    OratReadinessSummary,
    OratTrialCreate,
    OratTrialRead,
    OratTrialUpdate,
    OratWorkstreamCreate,
    OratWorkstreamRead,
    OratWorkstreamUpdate,
    PackageHandoverPressure,
    TrainingGroupCreate,
    TrainingGroupRead,
    TrainingGroupUpdate,
)
from app.services.audit import write_audit_log

router = APIRouter(prefix="/projects/{project_id}/orat")


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


def _validate_workstream(
    db: Session, tenant_id: str, project_id: str, workstream_id: str
) -> OratWorkstream:
    ws = (
        db.query(OratWorkstream)
        .filter(
            OratWorkstream.id == workstream_id,
            OratWorkstream.project_id == project_id,
            OratWorkstream.tenant_id == tenant_id,
        )
        .first()
    )
    if ws is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ORAT workstream {workstream_id} not found for project.",
        )
    return ws


# ---------------------------------------------------------------------------
# ORAT Workstreams
# ---------------------------------------------------------------------------


@router.get("/workstreams", response_model=List[OratWorkstreamRead])
def list_workstreams(
    status_filter: Optional[OratWorkstreamStatus] = Query(
        default=None, alias="status"
    ),
    project: Project = Depends(get_project_for_view),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> List[OratWorkstreamRead]:
    q = db.query(OratWorkstream).filter(
        OratWorkstream.project_id == project.id,
        OratWorkstream.tenant_id == principal.tenant_id,
    )
    if status_filter is not None:
        q = q.filter(OratWorkstream.status == status_filter)
    rows = q.order_by(
        OratWorkstream.due_month.asc(), OratWorkstream.name.asc()
    ).all()
    return [OratWorkstreamRead.model_validate(r) for r in rows]


@router.post(
    "/workstreams",
    response_model=OratWorkstreamRead,
    status_code=status.HTTP_201_CREATED,
)
def create_workstream(
    payload: OratWorkstreamCreate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> OratWorkstreamRead:
    duplicate = (
        db.query(OratWorkstream)
        .filter(
            OratWorkstream.project_id == project.id,
            OratWorkstream.tenant_id == principal.tenant_id,
            OratWorkstream.name == payload.name,
        )
        .first()
    )
    if duplicate is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"ORAT workstream {payload.name!r} already exists in project.",
        )

    item = OratWorkstream(
        tenant_id=principal.tenant_id,
        project_id=project.id,
        name=payload.name,
        owner=payload.owner,
        progress_pct=payload.progress_pct,
        status=payload.status,
        due_month=payload.due_month,
    )
    db.add(item)
    db.flush()
    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="OratWorkstream",
        entity_id=item.id,
        action="created",
        details={
            "name": item.name,
            "status": item.status.value,
            "due_month": item.due_month,
        },
    )
    db.commit()
    db.refresh(item)
    return OratWorkstreamRead.model_validate(item)


@router.patch("/workstreams/{workstream_id}", response_model=OratWorkstreamRead)
def update_workstream(
    workstream_id: str,
    payload: OratWorkstreamUpdate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> OratWorkstreamRead:
    item = (
        db.query(OratWorkstream)
        .filter(
            OratWorkstream.id == workstream_id,
            OratWorkstream.project_id == project.id,
            OratWorkstream.tenant_id == principal.tenant_id,
        )
        .first()
    )
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ORAT workstream not found.",
        )
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(item, field, value)
    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="OratWorkstream",
        entity_id=item.id,
        action="updated",
        details=data,
    )
    db.commit()
    db.refresh(item)
    return OratWorkstreamRead.model_validate(item)


# ---------------------------------------------------------------------------
# Trials
# ---------------------------------------------------------------------------


@router.get("/trials", response_model=List[OratTrialRead])
def list_trials(
    status_filter: Optional[TrialStatus] = Query(default=None, alias="status"),
    workstream_id: Optional[str] = Query(default=None),
    project: Project = Depends(get_project_for_view),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> List[OratTrialRead]:
    q = db.query(OratTrial).filter(
        OratTrial.project_id == project.id,
        OratTrial.tenant_id == principal.tenant_id,
    )
    if status_filter is not None:
        q = q.filter(OratTrial.status == status_filter)
    if workstream_id is not None:
        q = q.filter(OratTrial.workstream_id == workstream_id)
    rows = q.order_by(OratTrial.month.asc(), OratTrial.ref.asc()).all()
    return [OratTrialRead.model_validate(r) for r in rows]


@router.post(
    "/trials",
    response_model=OratTrialRead,
    status_code=status.HTTP_201_CREATED,
)
def create_trial(
    payload: OratTrialCreate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> OratTrialRead:
    if payload.workstream_id is not None:
        _validate_workstream(
            db, principal.tenant_id, project.id, payload.workstream_id
        )

    duplicate = (
        db.query(OratTrial)
        .filter(
            OratTrial.project_id == project.id,
            OratTrial.tenant_id == principal.tenant_id,
            OratTrial.ref == payload.ref,
        )
        .first()
    )
    if duplicate is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Trial ref {payload.ref!r} already exists in project.",
        )

    item = OratTrial(
        tenant_id=principal.tenant_id,
        project_id=project.id,
        workstream_id=payload.workstream_id,
        ref=payload.ref,
        title=payload.title,
        month=payload.month,
        participants=payload.participants,
        status=payload.status,
        observations=payload.observations,
    )
    db.add(item)
    db.flush()
    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="OratTrial",
        entity_id=item.id,
        action="created",
        details={
            "ref": item.ref,
            "status": item.status.value,
            "month": item.month,
        },
    )
    db.commit()
    db.refresh(item)
    return OratTrialRead.model_validate(item)


@router.patch("/trials/{trial_id}", response_model=OratTrialRead)
def update_trial(
    trial_id: str,
    payload: OratTrialUpdate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> OratTrialRead:
    item = (
        db.query(OratTrial)
        .filter(
            OratTrial.id == trial_id,
            OratTrial.project_id == project.id,
            OratTrial.tenant_id == principal.tenant_id,
        )
        .first()
    )
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="ORAT trial not found."
        )
    data = payload.model_dump(exclude_unset=True)
    if "workstream_id" in data and data["workstream_id"]:
        _validate_workstream(
            db, principal.tenant_id, project.id, data["workstream_id"]
        )
    for field, value in data.items():
        setattr(item, field, value)
    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="OratTrial",
        entity_id=item.id,
        action="updated",
        details=data,
    )
    db.commit()
    db.refresh(item)
    return OratTrialRead.model_validate(item)


# ---------------------------------------------------------------------------
# Training Groups
# ---------------------------------------------------------------------------


@router.get("/training-groups", response_model=List[TrainingGroupRead])
def list_training_groups(
    status_filter: Optional[TrainingStatus] = Query(
        default=None, alias="status"
    ),
    project: Project = Depends(get_project_for_view),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> List[TrainingGroupRead]:
    q = db.query(TrainingGroup).filter(
        TrainingGroup.project_id == project.id,
        TrainingGroup.tenant_id == principal.tenant_id,
    )
    if status_filter is not None:
        q = q.filter(TrainingGroup.status == status_filter)
    rows = q.order_by(TrainingGroup.function_name.asc()).all()
    return [TrainingGroupRead.model_validate(r) for r in rows]


@router.post(
    "/training-groups",
    response_model=TrainingGroupRead,
    status_code=status.HTTP_201_CREATED,
)
def create_training_group(
    payload: TrainingGroupCreate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> TrainingGroupRead:
    if payload.trained_headcount > payload.target_headcount:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Trained headcount cannot exceed target headcount.",
        )

    duplicate = (
        db.query(TrainingGroup)
        .filter(
            TrainingGroup.project_id == project.id,
            TrainingGroup.tenant_id == principal.tenant_id,
            TrainingGroup.function_name == payload.function_name,
        )
        .first()
    )
    if duplicate is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Training group {payload.function_name!r} already exists "
                "in project."
            ),
        )

    item = TrainingGroup(
        tenant_id=principal.tenant_id,
        project_id=project.id,
        function_name=payload.function_name,
        target_headcount=payload.target_headcount,
        trained_headcount=payload.trained_headcount,
        status=payload.status,
        owner=payload.owner,
    )
    db.add(item)
    db.flush()
    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="TrainingGroup",
        entity_id=item.id,
        action="created",
        details={
            "function_name": item.function_name,
            "target_headcount": item.target_headcount,
            "status": item.status.value,
        },
    )
    db.commit()
    db.refresh(item)
    return TrainingGroupRead.model_validate(item)


@router.patch(
    "/training-groups/{training_group_id}", response_model=TrainingGroupRead
)
def update_training_group(
    training_group_id: str,
    payload: TrainingGroupUpdate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> TrainingGroupRead:
    item = (
        db.query(TrainingGroup)
        .filter(
            TrainingGroup.id == training_group_id,
            TrainingGroup.project_id == project.id,
            TrainingGroup.tenant_id == principal.tenant_id,
        )
        .first()
    )
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Training group not found.",
        )
    data = payload.model_dump(exclude_unset=True)
    new_target = data.get("target_headcount", item.target_headcount)
    new_trained = data.get("trained_headcount", item.trained_headcount)
    if new_trained > new_target:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Trained headcount cannot exceed target headcount.",
        )
    for field, value in data.items():
        setattr(item, field, value)
    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="TrainingGroup",
        entity_id=item.id,
        action="updated",
        details=data,
    )
    db.commit()
    db.refresh(item)
    return TrainingGroupRead.model_validate(item)


# ---------------------------------------------------------------------------
# Handover Items
# ---------------------------------------------------------------------------


@router.get("/handover-items", response_model=List[HandoverItemRead])
def list_handover_items(
    status_filter: Optional[HandoverStatus] = Query(
        default=None, alias="status"
    ),
    project: Project = Depends(get_project_for_view),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> List[HandoverItemRead]:
    q = db.query(HandoverItem).filter(
        HandoverItem.project_id == project.id,
        HandoverItem.tenant_id == principal.tenant_id,
    )
    if status_filter is not None:
        q = q.filter(HandoverItem.status == status_filter)
    rows = q.order_by(HandoverItem.ref.asc()).all()
    return [HandoverItemRead.model_validate(r) for r in rows]


@router.post(
    "/handover-items",
    response_model=HandoverItemRead,
    status_code=status.HTTP_201_CREATED,
)
def create_handover_item(
    payload: HandoverItemCreate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> HandoverItemRead:
    if payload.package_id is not None:
        _validate_work_package(
            db, principal.tenant_id, project.id, payload.package_id
        )

    duplicate = (
        db.query(HandoverItem)
        .filter(
            HandoverItem.project_id == project.id,
            HandoverItem.tenant_id == principal.tenant_id,
            HandoverItem.ref == payload.ref,
        )
        .first()
    )
    if duplicate is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Handover ref {payload.ref!r} already exists in project.",
        )

    item = HandoverItem(
        tenant_id=principal.tenant_id,
        project_id=project.id,
        package_id=payload.package_id,
        ref=payload.ref,
        asset_group=payload.asset_group,
        status=payload.status,
        evidence_pct=payload.evidence_pct,
        owner=payload.owner,
    )
    db.add(item)
    db.flush()
    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="HandoverItem",
        entity_id=item.id,
        action="created",
        details={
            "ref": item.ref,
            "asset_group": item.asset_group,
            "status": item.status.value,
        },
    )
    db.commit()
    db.refresh(item)
    return HandoverItemRead.model_validate(item)


@router.patch(
    "/handover-items/{handover_id}", response_model=HandoverItemRead
)
def update_handover_item(
    handover_id: str,
    payload: HandoverItemUpdate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> HandoverItemRead:
    item = (
        db.query(HandoverItem)
        .filter(
            HandoverItem.id == handover_id,
            HandoverItem.project_id == project.id,
            HandoverItem.tenant_id == principal.tenant_id,
        )
        .first()
    )
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Handover item not found.",
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
        entity_type="HandoverItem",
        entity_id=item.id,
        action="updated",
        details=data,
    )
    db.commit()
    db.refresh(item)
    return HandoverItemRead.model_validate(item)


# ---------------------------------------------------------------------------
# Rollups
# ---------------------------------------------------------------------------


@router.get("/summary", response_model=OratReadinessSummary)
def orat_readiness_summary(
    project: Project = Depends(get_project_for_view),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> OratReadinessSummary:
    workstreams = (
        db.query(OratWorkstream)
        .filter(
            OratWorkstream.project_id == project.id,
            OratWorkstream.tenant_id == principal.tenant_id,
        )
        .all()
    )
    trials = (
        db.query(OratTrial)
        .filter(
            OratTrial.project_id == project.id,
            OratTrial.tenant_id == principal.tenant_id,
        )
        .all()
    )
    training = (
        db.query(TrainingGroup)
        .filter(
            TrainingGroup.project_id == project.id,
            TrainingGroup.tenant_id == principal.tenant_id,
        )
        .all()
    )
    handover = (
        db.query(HandoverItem)
        .filter(
            HandoverItem.project_id == project.id,
            HandoverItem.tenant_id == principal.tenant_id,
        )
        .all()
    )

    avg_progress = (
        round(sum(w.progress_pct for w in workstreams) / len(workstreams))
        if workstreams
        else 0
    )
    at_risk = sum(
        1 for w in workstreams if w.status == OratWorkstreamStatus.at_risk
    )
    passed_trials = sum(1 for t in trials if t.status == TrialStatus.passed)
    total_target = sum(g.target_headcount for g in training)
    total_done = sum(g.trained_headcount for g in training)
    training_pct = (
        round((total_done / total_target) * 100) if total_target > 0 else 0
    )
    accepted_handover = sum(
        1 for h in handover if h.status == HandoverStatus.accepted
    )
    blocked_handover = sum(
        1 for h in handover if h.status == HandoverStatus.blocked
    )

    return OratReadinessSummary(
        project_id=project.id,
        workstream_count=len(workstreams),
        trial_count=len(trials),
        training_group_count=len(training),
        handover_item_count=len(handover),
        average_workstream_progress_pct=avg_progress,
        at_risk_workstream_count=at_risk,
        passed_trial_count=passed_trials,
        training_completion_pct=training_pct,
        accepted_handover_count=accepted_handover,
        blocked_handover_count=blocked_handover,
    )


@router.get("/handover-pressure", response_model=List[PackageHandoverPressure])
def handover_pressure(
    project: Project = Depends(get_project_for_view),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> List[PackageHandoverPressure]:
    packages = (
        db.query(WorkPackage)
        .filter(
            WorkPackage.project_id == project.id,
            WorkPackage.tenant_id == principal.tenant_id,
        )
        .order_by(WorkPackage.code.asc())
        .all()
    )
    handover = (
        db.query(HandoverItem)
        .filter(
            HandoverItem.project_id == project.id,
            HandoverItem.tenant_id == principal.tenant_id,
        )
        .all()
    )

    results: List[PackageHandoverPressure] = []
    for pkg in packages:
        pkg_items = [h for h in handover if h.package_id == pkg.id]
        avg = (
            round(sum(h.evidence_pct for h in pkg_items) / len(pkg_items))
            if pkg_items
            else 0
        )
        results.append(
            PackageHandoverPressure(
                package_id=pkg.id,
                package_code=pkg.code,
                package_name=pkg.name,
                handover_count=len(pkg_items),
                accepted_count=sum(
                    1 for h in pkg_items if h.status == HandoverStatus.accepted
                ),
                blocked_count=sum(
                    1 for h in pkg_items if h.status == HandoverStatus.blocked
                ),
                pending_count=sum(
                    1
                    for h in pkg_items
                    if h.status
                    in {HandoverStatus.pending, HandoverStatus.in_verification}
                ),
                average_evidence_pct=avg,
            )
        )
    return results
