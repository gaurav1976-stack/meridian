"""Risk + opportunity router with a 5x5 heatmap rollup."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import (
    CurrentPrincipal,
    get_current_principal,
    get_project_for_edit,
    get_project_for_view,
)
from app.db.session import get_db
from app.models.core import Project
from app.models.enums import RiskStatus
from app.models.risk import OpportunityItem, RiskItem
from app.schemas.risks import (
    OpportunityCreate,
    OpportunityRead,
    RiskCreate,
    RiskHeatmap,
    RiskHeatmapCell,
    RiskRead,
    RiskUpdate,
)
from app.services.audit import write_audit_log

router = APIRouter(prefix="/projects/{project_id}/risks")


def _to_read(r: RiskItem) -> RiskRead:
    """Inject computed scores — the model exposes them as @property."""
    return RiskRead.model_validate(
        {
            **{
                c.name: getattr(r, c.name)
                for c in r.__table__.columns
            },
            "gross_score": r.gross_score,
            "residual_score": r.residual_score,
        }
    )


# ---------------------------------------------------------------------------
# Risks
# ---------------------------------------------------------------------------


@router.get("", response_model=List[RiskRead])
def list_risks(
    project: Project = Depends(get_project_for_view),
    db: Session = Depends(get_db),
    status_filter: RiskStatus | None = None,
) -> List[RiskRead]:
    q = db.query(RiskItem).filter(RiskItem.project_id == project.id)
    if status_filter is not None:
        q = q.filter(RiskItem.status == status_filter)
    rows = q.order_by(RiskItem.code).all()
    return [_to_read(r) for r in rows]


@router.post("", response_model=RiskRead, status_code=status.HTTP_201_CREATED)
def create_risk(
    payload: RiskCreate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> RiskRead:
    risk = RiskItem(
        tenant_id=principal.tenant_id, project_id=project.id, **payload.model_dump()
    )
    db.add(risk)
    db.flush()
    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="RiskItem",
        entity_id=risk.id,
        action="created",
        details=payload.model_dump(),
    )
    db.commit()
    db.refresh(risk)
    return _to_read(risk)


@router.patch("/{risk_id}", response_model=RiskRead)
def update_risk(
    risk_id: str,
    payload: RiskUpdate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> RiskRead:
    risk = (
        db.query(RiskItem)
        .filter(RiskItem.id == risk_id, RiskItem.project_id == project.id)
        .first()
    )
    if risk is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Risk not found.")
    changes = payload.model_dump(exclude_unset=True)
    for key, value in changes.items():
        setattr(risk, key, value)
    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="RiskItem",
        entity_id=risk.id,
        action="updated",
        details=changes,
    )
    db.commit()
    db.refresh(risk)
    return _to_read(risk)


# ---------------------------------------------------------------------------
# Heatmap
# ---------------------------------------------------------------------------


@router.get("/heatmap", response_model=RiskHeatmap)
def risk_heatmap(
    project: Project = Depends(get_project_for_view),
    db: Session = Depends(get_db),
) -> RiskHeatmap:
    rows = (
        db.query(RiskItem)
        .filter(RiskItem.project_id == project.id, RiskItem.status != RiskStatus.closed)
        .all()
    )
    grid: dict[tuple[int, int], int] = {}
    for r in rows:
        l = r.mitigated_likelihood or r.likelihood
        i = r.mitigated_impact or r.impact
        grid[(l, i)] = grid.get((l, i), 0) + 1
    cells = [
        RiskHeatmapCell(likelihood=l, impact=i, count=c) for (l, i), c in sorted(grid.items())
    ]
    top = sorted(rows, key=lambda r: r.residual_score, reverse=True)[:5]
    return RiskHeatmap(cells=cells, top_residual=[_to_read(r) for r in top])


# ---------------------------------------------------------------------------
# Opportunities — separate top-level router, mounted alongside `router` in
# `app.api.router` so the two share the same tag but not the same URL prefix.
# ---------------------------------------------------------------------------


opportunities_router = APIRouter(prefix="/projects/{project_id}/opportunities")


@opportunities_router.get("", response_model=List[OpportunityRead])
def list_opportunities(
    project: Project = Depends(get_project_for_view),
    db: Session = Depends(get_db),
) -> List[OpportunityRead]:
    rows = (
        db.query(OpportunityItem)
        .filter(OpportunityItem.project_id == project.id)
        .order_by(OpportunityItem.code)
        .all()
    )
    return [OpportunityRead.model_validate(r) for r in rows]


@opportunities_router.post("", response_model=OpportunityRead, status_code=status.HTTP_201_CREATED)
def create_opportunity(
    payload: OpportunityCreate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> OpportunityRead:
    opp = OpportunityItem(
        tenant_id=principal.tenant_id, project_id=project.id, **payload.model_dump()
    )
    db.add(opp)
    db.flush()
    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="OpportunityItem",
        entity_id=opp.id,
        action="created",
        details=payload.model_dump(),
    )
    db.commit()
    db.refresh(opp)
    return OpportunityRead.model_validate(opp)
