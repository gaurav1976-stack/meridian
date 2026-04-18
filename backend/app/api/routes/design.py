"""Design Management router.

Port of `meridian_track_a_7_design_management_persistence.py` FastAPI handlers
into a single project-scoped APIRouter at `/projects/{project_id}/design`.
Exposes design packages (with RIBA stage + maturity + freeze-control fields),
design deliverables, design interfaces between packages, and BIM coordination
rollups; plus project-level summary and freeze-control endpoints.

Tenant isolation via `get_project_for_view/edit`; audit-log on every mutation;
single commit per request.

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
from app.models.design import (
    BimCoordinationItem,
    DesignDeliverable,
    DesignInterfaceItem,
    DesignPackage,
)
from app.models.enums import (
    DeliverableStatus,
    DeliverableType,
    DesignPackageStatus,
    InterfaceStatus,
    RibaStage,
)
from app.schemas.design import (
    BimItemCreate,
    BimItemRead,
    BimItemUpdate,
    DeliverableCreate,
    DeliverableRead,
    DeliverableUpdate,
    DesignPackageCreate,
    DesignPackageRead,
    DesignPackageUpdate,
    DesignSummary,
    FreezeControlEntry,
    FreezeControlReport,
    InterfaceCreate,
    InterfaceRead,
    InterfaceUpdate,
)
from app.services.audit import write_audit_log

router = APIRouter(prefix="/projects/{project_id}/design")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _freeze_variance(planned_month: int, current_month: int) -> int:
    """Positive value indicates slippage of the design freeze."""
    return current_month - planned_month


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


def _validate_design_package(
    db: Session, tenant_id: str, project_id: str, design_package_id: str
) -> DesignPackage:
    dp = (
        db.query(DesignPackage)
        .filter(
            DesignPackage.id == design_package_id,
            DesignPackage.project_id == project_id,
            DesignPackage.tenant_id == tenant_id,
        )
        .first()
    )
    if dp is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Design package {design_package_id} not found for project.",
        )
    return dp


# ---------------------------------------------------------------------------
# Design Packages
# ---------------------------------------------------------------------------


@router.get("/design-packages", response_model=List[DesignPackageRead])
def list_design_packages(
    status_filter: Optional[DesignPackageStatus] = Query(default=None, alias="status"),
    stage: Optional[RibaStage] = Query(default=None),
    project: Project = Depends(get_project_for_view),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> List[DesignPackageRead]:
    q = db.query(DesignPackage).filter(
        DesignPackage.project_id == project.id,
        DesignPackage.tenant_id == principal.tenant_id,
    )
    if status_filter is not None:
        q = q.filter(DesignPackage.status == status_filter)
    if stage is not None:
        q = q.filter(DesignPackage.stage == stage)
    rows = q.order_by(DesignPackage.code.asc()).all()
    return [DesignPackageRead.model_validate(r) for r in rows]


@router.post(
    "/design-packages",
    response_model=DesignPackageRead,
    status_code=status.HTTP_201_CREATED,
)
def create_design_package(
    payload: DesignPackageCreate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> DesignPackageRead:
    if payload.package_id is not None:
        _validate_work_package(db, principal.tenant_id, project.id, payload.package_id)

    duplicate = (
        db.query(DesignPackage)
        .filter(
            DesignPackage.project_id == project.id,
            DesignPackage.tenant_id == principal.tenant_id,
            DesignPackage.code == payload.code,
        )
        .first()
    )
    if duplicate is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Design package code {payload.code!r} already exists in project.",
        )

    item = DesignPackage(
        tenant_id=principal.tenant_id,
        project_id=project.id,
        package_id=payload.package_id,
        code=payload.code,
        name=payload.name,
        lead_discipline=payload.lead_discipline,
        stage=payload.stage,
        maturity_pct=payload.maturity_pct,
        status=payload.status,
        freeze_planned_month=payload.freeze_planned_month,
        freeze_current_month=payload.freeze_current_month,
    )
    db.add(item)
    db.flush()
    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="DesignPackage",
        entity_id=item.id,
        action="created",
        details={"code": item.code, "stage": item.stage.value},
    )
    db.commit()
    db.refresh(item)
    return DesignPackageRead.model_validate(item)


@router.patch(
    "/design-packages/{design_package_id}", response_model=DesignPackageRead
)
def update_design_package(
    design_package_id: str,
    payload: DesignPackageUpdate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> DesignPackageRead:
    item = _validate_design_package(
        db, principal.tenant_id, project.id, design_package_id
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
        entity_type="DesignPackage",
        entity_id=item.id,
        action="updated",
        details=data,
    )
    db.commit()
    db.refresh(item)
    return DesignPackageRead.model_validate(item)


# ---------------------------------------------------------------------------
# Deliverables
# ---------------------------------------------------------------------------


@router.get("/deliverables", response_model=List[DeliverableRead])
def list_deliverables(
    status_filter: Optional[DeliverableStatus] = Query(default=None, alias="status"),
    deliverable_type: Optional[DeliverableType] = Query(default=None),
    stage: Optional[RibaStage] = Query(default=None),
    project: Project = Depends(get_project_for_view),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> List[DeliverableRead]:
    q = db.query(DesignDeliverable).filter(
        DesignDeliverable.project_id == project.id,
        DesignDeliverable.tenant_id == principal.tenant_id,
    )
    if status_filter is not None:
        q = q.filter(DesignDeliverable.status == status_filter)
    if deliverable_type is not None:
        q = q.filter(DesignDeliverable.deliverable_type == deliverable_type)
    if stage is not None:
        q = q.filter(DesignDeliverable.stage == stage)
    rows = q.order_by(DesignDeliverable.due_month.asc()).all()
    return [DeliverableRead.model_validate(r) for r in rows]


@router.post(
    "/deliverables",
    response_model=DeliverableRead,
    status_code=status.HTTP_201_CREATED,
)
def create_deliverable(
    payload: DeliverableCreate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> DeliverableRead:
    if payload.design_package_id is not None:
        _validate_design_package(
            db, principal.tenant_id, project.id, payload.design_package_id
        )
    if payload.package_id is not None:
        _validate_work_package(db, principal.tenant_id, project.id, payload.package_id)

    duplicate = (
        db.query(DesignDeliverable)
        .filter(
            DesignDeliverable.project_id == project.id,
            DesignDeliverable.tenant_id == principal.tenant_id,
            DesignDeliverable.ref == payload.ref,
        )
        .first()
    )
    if duplicate is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Deliverable ref {payload.ref!r} already exists in project.",
        )

    item = DesignDeliverable(
        tenant_id=principal.tenant_id,
        project_id=project.id,
        design_package_id=payload.design_package_id,
        package_id=payload.package_id,
        ref=payload.ref,
        title=payload.title,
        discipline=payload.discipline,
        deliverable_type=payload.deliverable_type,
        stage=payload.stage,
        due_month=payload.due_month,
        status=payload.status,
        owner=payload.owner,
    )
    db.add(item)
    db.flush()
    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="DesignDeliverable",
        entity_id=item.id,
        action="created",
        details={
            "ref": item.ref,
            "type": item.deliverable_type.value,
            "stage": item.stage.value,
        },
    )
    db.commit()
    db.refresh(item)
    return DeliverableRead.model_validate(item)


@router.patch("/deliverables/{deliverable_id}", response_model=DeliverableRead)
def update_deliverable(
    deliverable_id: str,
    payload: DeliverableUpdate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> DeliverableRead:
    item = (
        db.query(DesignDeliverable)
        .filter(
            DesignDeliverable.id == deliverable_id,
            DesignDeliverable.project_id == project.id,
            DesignDeliverable.tenant_id == principal.tenant_id,
        )
        .first()
    )
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Deliverable not found."
        )
    data = payload.model_dump(exclude_unset=True)
    if "design_package_id" in data and data["design_package_id"]:
        _validate_design_package(
            db, principal.tenant_id, project.id, data["design_package_id"]
        )
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
        entity_type="DesignDeliverable",
        entity_id=item.id,
        action="updated",
        details=data,
    )
    db.commit()
    db.refresh(item)
    return DeliverableRead.model_validate(item)


# ---------------------------------------------------------------------------
# Interfaces
# ---------------------------------------------------------------------------


@router.get("/interfaces", response_model=List[InterfaceRead])
def list_interfaces(
    status_filter: Optional[InterfaceStatus] = Query(default=None, alias="status"),
    project: Project = Depends(get_project_for_view),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> List[InterfaceRead]:
    q = db.query(DesignInterfaceItem).filter(
        DesignInterfaceItem.project_id == project.id,
        DesignInterfaceItem.tenant_id == principal.tenant_id,
    )
    if status_filter is not None:
        q = q.filter(DesignInterfaceItem.status == status_filter)
    rows = q.order_by(DesignInterfaceItem.severity.desc()).all()
    return [InterfaceRead.model_validate(r) for r in rows]


@router.post(
    "/interfaces",
    response_model=InterfaceRead,
    status_code=status.HTTP_201_CREATED,
)
def create_interface(
    payload: InterfaceCreate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> InterfaceRead:
    _validate_work_package(db, principal.tenant_id, project.id, payload.package_a_id)
    _validate_work_package(db, principal.tenant_id, project.id, payload.package_b_id)

    duplicate = (
        db.query(DesignInterfaceItem)
        .filter(
            DesignInterfaceItem.project_id == project.id,
            DesignInterfaceItem.tenant_id == principal.tenant_id,
            DesignInterfaceItem.ref == payload.ref,
        )
        .first()
    )
    if duplicate is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Interface ref {payload.ref!r} already exists in project.",
        )

    item = DesignInterfaceItem(
        tenant_id=principal.tenant_id,
        project_id=project.id,
        ref=payload.ref,
        title=payload.title,
        package_a_id=payload.package_a_id,
        package_b_id=payload.package_b_id,
        owner=payload.owner,
        severity=payload.severity,
        status=payload.status,
        due_month=payload.due_month,
    )
    db.add(item)
    db.flush()
    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="DesignInterfaceItem",
        entity_id=item.id,
        action="created",
        details={"ref": item.ref, "severity": item.severity},
    )
    db.commit()
    db.refresh(item)
    return InterfaceRead.model_validate(item)


@router.patch("/interfaces/{interface_id}", response_model=InterfaceRead)
def update_interface(
    interface_id: str,
    payload: InterfaceUpdate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> InterfaceRead:
    item = (
        db.query(DesignInterfaceItem)
        .filter(
            DesignInterfaceItem.id == interface_id,
            DesignInterfaceItem.project_id == project.id,
            DesignInterfaceItem.tenant_id == principal.tenant_id,
        )
        .first()
    )
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Interface item not found."
        )
    data = payload.model_dump(exclude_unset=True)
    for key in ("package_a_id", "package_b_id"):
        if key in data and data[key]:
            _validate_work_package(
                db, principal.tenant_id, project.id, data[key]
            )
    for field, value in data.items():
        setattr(item, field, value)
    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="DesignInterfaceItem",
        entity_id=item.id,
        action="updated",
        details=data,
    )
    db.commit()
    db.refresh(item)
    return InterfaceRead.model_validate(item)


# ---------------------------------------------------------------------------
# BIM Coordination
# ---------------------------------------------------------------------------


@router.get("/bim-items", response_model=List[BimItemRead])
def list_bim_items(
    project: Project = Depends(get_project_for_view),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> List[BimItemRead]:
    rows = (
        db.query(BimCoordinationItem)
        .filter(
            BimCoordinationItem.project_id == project.id,
            BimCoordinationItem.tenant_id == principal.tenant_id,
        )
        .order_by(BimCoordinationItem.workstream.asc())
        .all()
    )
    return [BimItemRead.model_validate(r) for r in rows]


@router.post(
    "/bim-items", response_model=BimItemRead, status_code=status.HTTP_201_CREATED
)
def create_bim_item(
    payload: BimItemCreate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> BimItemRead:
    item = BimCoordinationItem(
        tenant_id=principal.tenant_id,
        project_id=project.id,
        workstream=payload.workstream,
        clash_open=payload.clash_open,
        clash_critical=payload.clash_critical,
        federation_ready=payload.federation_ready,
        model_share_status=payload.model_share_status,
    )
    db.add(item)
    db.flush()
    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="BimCoordinationItem",
        entity_id=item.id,
        action="created",
        details={"workstream": item.workstream, "clash_critical": item.clash_critical},
    )
    db.commit()
    db.refresh(item)
    return BimItemRead.model_validate(item)


@router.patch("/bim-items/{bim_item_id}", response_model=BimItemRead)
def update_bim_item(
    bim_item_id: str,
    payload: BimItemUpdate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> BimItemRead:
    item = (
        db.query(BimCoordinationItem)
        .filter(
            BimCoordinationItem.id == bim_item_id,
            BimCoordinationItem.project_id == project.id,
            BimCoordinationItem.tenant_id == principal.tenant_id,
        )
        .first()
    )
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="BIM item not found."
        )
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(item, field, value)
    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="BimCoordinationItem",
        entity_id=item.id,
        action="updated",
        details=data,
    )
    db.commit()
    db.refresh(item)
    return BimItemRead.model_validate(item)


# ---------------------------------------------------------------------------
# Rollups
# ---------------------------------------------------------------------------


@router.get("/summary", response_model=DesignSummary)
def design_summary(
    project: Project = Depends(get_project_for_view),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> DesignSummary:
    packages = (
        db.query(DesignPackage)
        .filter(
            DesignPackage.project_id == project.id,
            DesignPackage.tenant_id == principal.tenant_id,
        )
        .all()
    )
    deliverables = (
        db.query(DesignDeliverable)
        .filter(
            DesignDeliverable.project_id == project.id,
            DesignDeliverable.tenant_id == principal.tenant_id,
        )
        .all()
    )
    interfaces = (
        db.query(DesignInterfaceItem)
        .filter(
            DesignInterfaceItem.project_id == project.id,
            DesignInterfaceItem.tenant_id == principal.tenant_id,
        )
        .all()
    )
    bim_items = (
        db.query(BimCoordinationItem)
        .filter(
            BimCoordinationItem.project_id == project.id,
            BimCoordinationItem.tenant_id == principal.tenant_id,
        )
        .all()
    )

    avg_maturity = (
        round(sum(p.maturity_pct for p in packages) / len(packages))
        if packages
        else 0
    )
    avg_freeze_variance = (
        round(
            sum(
                _freeze_variance(p.freeze_planned_month, p.freeze_current_month)
                for p in packages
            )
            / len(packages)
        )
        if packages
        else 0
    )

    return DesignSummary(
        project_id=project.id,
        design_package_count=len(packages),
        deliverable_count=len(deliverables),
        interface_count=len(interfaces),
        bim_item_count=len(bim_items),
        average_maturity_pct=avg_maturity,
        overdue_deliverable_count=sum(
            1 for d in deliverables if d.status == DeliverableStatus.overdue
        ),
        frozen_package_count=sum(
            1 for p in packages if p.status == DesignPackageStatus.frozen
        ),
        escalated_interface_count=sum(
            1 for i in interfaces if i.status == InterfaceStatus.escalated
        ),
        critical_clash_count=sum(b.clash_critical for b in bim_items),
        average_freeze_variance_months=avg_freeze_variance,
    )


@router.get("/freeze-control", response_model=FreezeControlReport)
def freeze_control(
    project: Project = Depends(get_project_for_view),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> FreezeControlReport:
    packages = (
        db.query(DesignPackage)
        .filter(
            DesignPackage.project_id == project.id,
            DesignPackage.tenant_id == principal.tenant_id,
        )
        .order_by(DesignPackage.code.asc())
        .all()
    )
    entries = [
        FreezeControlEntry(
            design_package_id=p.id,
            code=p.code,
            name=p.name,
            status=p.status,
            stage=p.stage,
            maturity_pct=p.maturity_pct,
            freeze_planned_month=p.freeze_planned_month,
            freeze_current_month=p.freeze_current_month,
            variance_months=_freeze_variance(
                p.freeze_planned_month, p.freeze_current_month
            ),
        )
        for p in packages
    ]
    return FreezeControlReport(project_id=project.id, entries=entries)
