"""Commercial / Cost & Change Control router.

Port of `meridian_track_a_6_cost_change_commercial_persistence.py` FastAPI
handlers into a single project-scoped APIRouter at
`/projects/{project_id}/commercial`. Exposes per-package cost controls,
Compensation Events / Variations / Claims, contract notices (EWN etc.),
plus rollups for commercial summary, EVM (BAC/EV/AC/PV/CPI/SPI) and
per-package exposure.

Tenant isolation via `get_project_for_view/edit`; audit-log on every
mutation; single commit per request.

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
from app.models.commercial import (
    CommercialChangeItem,
    CommercialNoticeItem,
    PackageCostControl,
)
from app.models.core import Project, WorkPackage
from app.models.enums import (
    ChangeStatus,
    ChangeType,
    EntitlementStrength,
    NoticeKind,
    NoticeStatus,
)
from app.schemas.commercial import (
    ChangeCreate,
    ChangeRead,
    ChangeUpdate,
    CommercialSummary,
    EvmSummary,
    NoticeCreate,
    NoticeRead,
    NoticeUpdate,
    PackageCommercialExposure,
    PackageCostCreate,
    PackageCostRead,
    PackageCostUpdate,
)
from app.services.audit import write_audit_log

router = APIRouter(prefix="/projects/{project_id}/commercial")


# ---------------------------------------------------------------------------
# EVM helpers
# ---------------------------------------------------------------------------


def _calc_ev(budget_minor: int, percent_complete: int) -> int:
    """Earned Value for a single cost line."""
    return int(budget_minor * (max(0, min(100, percent_complete)) / 100))


def _validate_package(
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
            detail=f"Package {package_id} not found for project.",
        )
    return pkg


# ---------------------------------------------------------------------------
# Package cost controls
# ---------------------------------------------------------------------------


@router.get("/cost-controls", response_model=List[PackageCostRead])
def list_cost_controls(
    project: Project = Depends(get_project_for_view),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> List[PackageCostRead]:
    rows = (
        db.query(PackageCostControl)
        .filter(
            PackageCostControl.project_id == project.id,
            PackageCostControl.tenant_id == principal.tenant_id,
        )
        .all()
    )
    return [PackageCostRead.model_validate(r) for r in rows]


@router.post(
    "/cost-controls",
    response_model=PackageCostRead,
    status_code=status.HTTP_201_CREATED,
)
def create_cost_control(
    payload: PackageCostCreate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> PackageCostRead:
    _validate_package(db, principal.tenant_id, project.id, payload.package_id)

    duplicate = (
        db.query(PackageCostControl)
        .filter(
            PackageCostControl.project_id == project.id,
            PackageCostControl.tenant_id == principal.tenant_id,
            PackageCostControl.package_id == payload.package_id,
        )
        .first()
    )
    if duplicate is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cost control already exists for this package.",
        )

    item = PackageCostControl(
        tenant_id=principal.tenant_id,
        project_id=project.id,
        package_id=payload.package_id,
        budget_minor=payload.budget_minor,
        committed_minor=payload.committed_minor,
        forecast_minor=payload.forecast_minor,
        actual_minor=payload.actual_minor,
        percent_complete=payload.percent_complete,
    )
    db.add(item)
    db.flush()
    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="PackageCostControl",
        entity_id=item.id,
        action="created",
        details={"package_id": item.package_id, "budget_minor": item.budget_minor},
    )
    db.commit()
    db.refresh(item)
    return PackageCostRead.model_validate(item)


@router.patch("/cost-controls/{cost_control_id}", response_model=PackageCostRead)
def update_cost_control(
    cost_control_id: str,
    payload: PackageCostUpdate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> PackageCostRead:
    item = (
        db.query(PackageCostControl)
        .filter(
            PackageCostControl.id == cost_control_id,
            PackageCostControl.project_id == project.id,
            PackageCostControl.tenant_id == principal.tenant_id,
        )
        .first()
    )
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cost control not found."
        )
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="PackageCostControl",
        entity_id=item.id,
        action="updated",
        details=payload.model_dump(exclude_unset=True),
    )
    db.commit()
    db.refresh(item)
    return PackageCostRead.model_validate(item)


# ---------------------------------------------------------------------------
# Commercial changes
# ---------------------------------------------------------------------------


@router.get("/changes", response_model=List[ChangeRead])
def list_changes(
    status_filter: Optional[ChangeStatus] = Query(default=None, alias="status"),
    change_type: Optional[ChangeType] = Query(default=None),
    project: Project = Depends(get_project_for_view),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> List[ChangeRead]:
    q = db.query(CommercialChangeItem).filter(
        CommercialChangeItem.project_id == project.id,
        CommercialChangeItem.tenant_id == principal.tenant_id,
    )
    if status_filter is not None:
        q = q.filter(CommercialChangeItem.status == status_filter)
    if change_type is not None:
        q = q.filter(CommercialChangeItem.change_type == change_type)
    rows = q.order_by(CommercialChangeItem.created_at.desc()).all()
    return [ChangeRead.model_validate(r) for r in rows]


@router.post(
    "/changes", response_model=ChangeRead, status_code=status.HTTP_201_CREATED
)
def create_change(
    payload: ChangeCreate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> ChangeRead:
    if payload.package_id is not None:
        _validate_package(db, principal.tenant_id, project.id, payload.package_id)

    duplicate = (
        db.query(CommercialChangeItem)
        .filter(
            CommercialChangeItem.project_id == project.id,
            CommercialChangeItem.tenant_id == principal.tenant_id,
            CommercialChangeItem.ref == payload.ref,
        )
        .first()
    )
    if duplicate is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Change ref {payload.ref!r} already exists in project.",
        )

    item = CommercialChangeItem(
        tenant_id=principal.tenant_id,
        project_id=project.id,
        package_id=payload.package_id,
        ref=payload.ref,
        title=payload.title,
        change_type=payload.change_type,
        status=payload.status,
        cost_impact_minor=payload.cost_impact_minor,
        time_impact_weeks=payload.time_impact_weeks,
        entitlement=payload.entitlement,
        owner=payload.owner,
        cause=payload.cause,
    )
    db.add(item)
    db.flush()
    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="CommercialChangeItem",
        entity_id=item.id,
        action="created",
        details={"ref": item.ref, "type": item.change_type.value, "cost_impact_minor": item.cost_impact_minor},
    )
    db.commit()
    db.refresh(item)
    return ChangeRead.model_validate(item)


@router.patch("/changes/{change_id}", response_model=ChangeRead)
def update_change(
    change_id: str,
    payload: ChangeUpdate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> ChangeRead:
    item = (
        db.query(CommercialChangeItem)
        .filter(
            CommercialChangeItem.id == change_id,
            CommercialChangeItem.project_id == project.id,
            CommercialChangeItem.tenant_id == principal.tenant_id,
        )
        .first()
    )
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Change item not found."
        )
    data = payload.model_dump(exclude_unset=True)
    if "package_id" in data and data["package_id"]:
        _validate_package(db, principal.tenant_id, project.id, data["package_id"])
    for field, value in data.items():
        setattr(item, field, value)
    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="CommercialChangeItem",
        entity_id=item.id,
        action="updated",
        details=data,
    )
    db.commit()
    db.refresh(item)
    return ChangeRead.model_validate(item)


# ---------------------------------------------------------------------------
# Commercial notices
# ---------------------------------------------------------------------------


@router.get("/notices", response_model=List[NoticeRead])
def list_notices(
    status_filter: Optional[NoticeStatus] = Query(default=None, alias="status"),
    kind: Optional[NoticeKind] = Query(default=None),
    project: Project = Depends(get_project_for_view),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> List[NoticeRead]:
    q = db.query(CommercialNoticeItem).filter(
        CommercialNoticeItem.project_id == project.id,
        CommercialNoticeItem.tenant_id == principal.tenant_id,
    )
    if status_filter is not None:
        q = q.filter(CommercialNoticeItem.status == status_filter)
    if kind is not None:
        q = q.filter(CommercialNoticeItem.kind == kind)
    rows = q.order_by(CommercialNoticeItem.created_at.desc()).all()
    return [NoticeRead.model_validate(r) for r in rows]


@router.post(
    "/notices", response_model=NoticeRead, status_code=status.HTTP_201_CREATED
)
def create_notice(
    payload: NoticeCreate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> NoticeRead:
    if payload.package_id is not None:
        _validate_package(db, principal.tenant_id, project.id, payload.package_id)

    duplicate = (
        db.query(CommercialNoticeItem)
        .filter(
            CommercialNoticeItem.project_id == project.id,
            CommercialNoticeItem.tenant_id == principal.tenant_id,
            CommercialNoticeItem.ref == payload.ref,
        )
        .first()
    )
    if duplicate is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Notice ref {payload.ref!r} already exists in project.",
        )

    item = CommercialNoticeItem(
        tenant_id=principal.tenant_id,
        project_id=project.id,
        package_id=payload.package_id,
        ref=payload.ref,
        contract_ref=payload.contract_ref,
        kind=payload.kind,
        due_days=payload.due_days,
        status=payload.status,
        owner=payload.owner,
    )
    db.add(item)
    db.flush()
    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="CommercialNoticeItem",
        entity_id=item.id,
        action="created",
        details={"ref": item.ref, "kind": item.kind.value},
    )
    db.commit()
    db.refresh(item)
    return NoticeRead.model_validate(item)


@router.patch("/notices/{notice_id}", response_model=NoticeRead)
def update_notice(
    notice_id: str,
    payload: NoticeUpdate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> NoticeRead:
    item = (
        db.query(CommercialNoticeItem)
        .filter(
            CommercialNoticeItem.id == notice_id,
            CommercialNoticeItem.project_id == project.id,
            CommercialNoticeItem.tenant_id == principal.tenant_id,
        )
        .first()
    )
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Notice item not found."
        )
    data = payload.model_dump(exclude_unset=True)
    if "package_id" in data and data["package_id"]:
        _validate_package(db, principal.tenant_id, project.id, data["package_id"])
    for field, value in data.items():
        setattr(item, field, value)
    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="CommercialNoticeItem",
        entity_id=item.id,
        action="updated",
        details=data,
    )
    db.commit()
    db.refresh(item)
    return NoticeRead.model_validate(item)


# ---------------------------------------------------------------------------
# Rollups
# ---------------------------------------------------------------------------


@router.get("/summary", response_model=CommercialSummary)
def commercial_summary(
    project: Project = Depends(get_project_for_view),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> CommercialSummary:
    cost_items = (
        db.query(PackageCostControl)
        .filter(
            PackageCostControl.project_id == project.id,
            PackageCostControl.tenant_id == principal.tenant_id,
        )
        .all()
    )
    change_items = (
        db.query(CommercialChangeItem)
        .filter(
            CommercialChangeItem.project_id == project.id,
            CommercialChangeItem.tenant_id == principal.tenant_id,
        )
        .all()
    )
    notice_items = (
        db.query(CommercialNoticeItem)
        .filter(
            CommercialNoticeItem.project_id == project.id,
            CommercialNoticeItem.tenant_id == principal.tenant_id,
        )
        .all()
    )

    budget = sum(i.budget_minor for i in cost_items)
    committed = sum(i.committed_minor for i in cost_items)
    forecast = sum(i.forecast_minor for i in cost_items)
    actual = sum(i.actual_minor for i in cost_items)

    return CommercialSummary(
        project_id=project.id,
        budget_minor=budget,
        committed_minor=committed,
        forecast_minor=forecast,
        actual_minor=actual,
        forecast_variance_minor=forecast - budget,
        change_exposure_minor=sum(c.cost_impact_minor for c in change_items),
        notice_count=len(notice_items),
        overdue_notice_count=sum(
            1 for n in notice_items if n.status == NoticeStatus.overdue
        ),
        strong_entitlement_count=sum(
            1 for c in change_items if c.entitlement == EntitlementStrength.strong
        ),
    )


@router.get("/evm-summary", response_model=EvmSummary)
def evm_summary(
    project: Project = Depends(get_project_for_view),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> EvmSummary:
    cost_items = (
        db.query(PackageCostControl)
        .filter(
            PackageCostControl.project_id == project.id,
            PackageCostControl.tenant_id == principal.tenant_id,
        )
        .all()
    )
    if not cost_items:
        return EvmSummary(
            project_id=project.id,
            bac_minor=0,
            pv_minor=0,
            ev_minor=0,
            ac_minor=0,
            cpi=0.0,
            spi=0.0,
            cv_minor=0,
            sv_minor=0,
            average_percent_complete=0,
        )

    bac = sum(i.budget_minor for i in cost_items)
    avg_complete = round(sum(i.percent_complete for i in cost_items) / len(cost_items))
    ev = sum(_calc_ev(i.budget_minor, i.percent_complete) for i in cost_items)
    ac = sum(i.actual_minor for i in cost_items)
    # Planned value heuristic: assume schedule is 10 points ahead of earned
    # progress (i.e. the baseline expected progress exceeds actuals).
    pv = round(((avg_complete + 10) / 100) * bac)
    cpi = round(ev / ac, 4) if ac > 0 else 0.0
    spi = round(ev / pv, 4) if pv > 0 else 0.0

    return EvmSummary(
        project_id=project.id,
        bac_minor=bac,
        pv_minor=pv,
        ev_minor=ev,
        ac_minor=ac,
        cpi=cpi,
        spi=spi,
        cv_minor=ev - ac,
        sv_minor=ev - pv,
        average_percent_complete=avg_complete,
    )


@router.get("/exposure", response_model=List[PackageCommercialExposure])
def package_commercial_exposure(
    project: Project = Depends(get_project_for_view),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> List[PackageCommercialExposure]:
    packages = (
        db.query(WorkPackage)
        .filter(
            WorkPackage.project_id == project.id,
            WorkPackage.tenant_id == principal.tenant_id,
        )
        .all()
    )
    cost_items = (
        db.query(PackageCostControl)
        .filter(
            PackageCostControl.project_id == project.id,
            PackageCostControl.tenant_id == principal.tenant_id,
        )
        .all()
    )
    changes = (
        db.query(CommercialChangeItem)
        .filter(
            CommercialChangeItem.project_id == project.id,
            CommercialChangeItem.tenant_id == principal.tenant_id,
        )
        .all()
    )
    notices = (
        db.query(CommercialNoticeItem)
        .filter(
            CommercialNoticeItem.project_id == project.id,
            CommercialNoticeItem.tenant_id == principal.tenant_id,
        )
        .all()
    )

    out: list[PackageCommercialExposure] = []
    for pkg in packages:
        cost = next((c for c in cost_items if c.package_id == pkg.id), None)
        pkg_changes = [c for c in changes if c.package_id == pkg.id]
        pkg_notices = [n for n in notices if n.package_id == pkg.id]
        out.append(
            PackageCommercialExposure(
                package_id=pkg.id,
                package_code=pkg.code,
                package_name=pkg.name,
                budget_minor=cost.budget_minor if cost else 0,
                forecast_minor=cost.forecast_minor if cost else 0,
                actual_minor=cost.actual_minor if cost else 0,
                change_exposure_minor=sum(c.cost_impact_minor for c in pkg_changes),
                notice_count=len(pkg_notices),
                overdue_notice_count=sum(
                    1 for n in pkg_notices if n.status == NoticeStatus.overdue
                ),
            )
        )
    return out
