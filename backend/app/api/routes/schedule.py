"""Schedule router — files, activities, dependencies, plus a `health` rollup.

Health metrics intentionally trivial here (counts + averages). Replace with the
full TIA / EVM service once Track A schedule analytics are migrated.
"""
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
from app.models.enums import ActivityStatus
from app.models.schedule import ActivityDependency, ScheduleActivity, ScheduleFile
from app.schemas.schedule import (
    ActivityDependencyCreate,
    ActivityDependencyRead,
    ScheduleActivityCreate,
    ScheduleActivityRead,
    ScheduleActivityUpdate,
    ScheduleFileCreate,
    ScheduleFileRead,
    ScheduleHealth,
)
from app.services.audit import write_audit_log

router = APIRouter(prefix="/projects/{project_id}/schedule")


# ---------------------------------------------------------------------------
# Schedule files
# ---------------------------------------------------------------------------


@router.get("/files", response_model=List[ScheduleFileRead])
def list_schedule_files(
    project: Project = Depends(get_project_for_view),
    db: Session = Depends(get_db),
) -> List[ScheduleFileRead]:
    rows = (
        db.query(ScheduleFile)
        .filter(ScheduleFile.project_id == project.id)
        .order_by(ScheduleFile.created_at.desc())
        .all()
    )
    return [ScheduleFileRead.model_validate(r) for r in rows]


@router.post("/files", response_model=ScheduleFileRead, status_code=status.HTTP_201_CREATED)
def create_schedule_file(
    payload: ScheduleFileCreate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> ScheduleFileRead:
    sf = ScheduleFile(
        tenant_id=principal.tenant_id, project_id=project.id, **payload.model_dump()
    )
    db.add(sf)
    db.flush()
    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="ScheduleFile",
        entity_id=sf.id,
        action="created",
        details=payload.model_dump(),
    )
    db.commit()
    db.refresh(sf)
    return ScheduleFileRead.model_validate(sf)


# ---------------------------------------------------------------------------
# Activities
# ---------------------------------------------------------------------------


@router.get("/activities", response_model=List[ScheduleActivityRead])
def list_activities(
    project: Project = Depends(get_project_for_view),
    db: Session = Depends(get_db),
    schedule_file_id: str | None = None,
) -> List[ScheduleActivityRead]:
    q = db.query(ScheduleActivity).filter(ScheduleActivity.project_id == project.id)
    if schedule_file_id is not None:
        q = q.filter(ScheduleActivity.schedule_file_id == schedule_file_id)
    rows = q.order_by(ScheduleActivity.activity_id_external).all()
    return [ScheduleActivityRead.model_validate(r) for r in rows]


@router.post(
    "/activities", response_model=ScheduleActivityRead, status_code=status.HTTP_201_CREATED
)
def create_activity(
    payload: ScheduleActivityCreate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> ScheduleActivityRead:
    act = ScheduleActivity(
        tenant_id=principal.tenant_id, project_id=project.id, **payload.model_dump()
    )
    db.add(act)
    db.flush()
    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="ScheduleActivity",
        entity_id=act.id,
        action="created",
        details=payload.model_dump(),
    )
    db.commit()
    db.refresh(act)
    return ScheduleActivityRead.model_validate(act)


@router.patch("/activities/{activity_id}", response_model=ScheduleActivityRead)
def update_activity(
    activity_id: str,
    payload: ScheduleActivityUpdate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> ScheduleActivityRead:
    act = (
        db.query(ScheduleActivity)
        .filter(ScheduleActivity.id == activity_id, ScheduleActivity.project_id == project.id)
        .first()
    )
    if act is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found.")
    changes = payload.model_dump(exclude_unset=True)
    for key, value in changes.items():
        setattr(act, key, value)
    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="ScheduleActivity",
        entity_id=act.id,
        action="updated",
        details=changes,
    )
    db.commit()
    db.refresh(act)
    return ScheduleActivityRead.model_validate(act)


# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------


@router.get("/dependencies", response_model=List[ActivityDependencyRead])
def list_dependencies(
    project: Project = Depends(get_project_for_view),
    db: Session = Depends(get_db),
) -> List[ActivityDependencyRead]:
    rows = (
        db.query(ActivityDependency)
        .filter(ActivityDependency.project_id == project.id)
        .all()
    )
    return [ActivityDependencyRead.model_validate(r) for r in rows]


@router.post(
    "/dependencies",
    response_model=ActivityDependencyRead,
    status_code=status.HTTP_201_CREATED,
)
def create_dependency(
    payload: ActivityDependencyCreate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> ActivityDependencyRead:
    # Both activities must belong to the same project.
    pred = db.query(ScheduleActivity).filter(ScheduleActivity.id == payload.predecessor_id).first()
    succ = db.query(ScheduleActivity).filter(ScheduleActivity.id == payload.successor_id).first()
    if pred is None or succ is None or pred.project_id != project.id or succ.project_id != project.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Predecessor and successor must both belong to this project.",
        )
    dep = ActivityDependency(
        tenant_id=principal.tenant_id, project_id=project.id, **payload.model_dump()
    )
    db.add(dep)
    db.flush()
    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="ActivityDependency",
        entity_id=dep.id,
        action="created",
        details=payload.model_dump(),
    )
    db.commit()
    db.refresh(dep)
    return ActivityDependencyRead.model_validate(dep)


# ---------------------------------------------------------------------------
# Health rollup — quick stats; replace with real EVM service later.
# ---------------------------------------------------------------------------


@router.get("/health", response_model=ScheduleHealth)
def schedule_health(
    project: Project = Depends(get_project_for_view),
    db: Session = Depends(get_db),
) -> ScheduleHealth:
    rows = (
        db.query(ScheduleActivity)
        .filter(ScheduleActivity.project_id == project.id)
        .all()
    )
    total = len(rows)
    if total == 0:
        return ScheduleHealth(
            total_activities=0,
            completed=0,
            in_progress=0,
            not_started=0,
            on_hold=0,
            critical_activities=0,
            low_float_activities=0,
            percent_complete_avg=0.0,
        )
    counts = {s: 0 for s in ActivityStatus}
    critical = 0
    low_float = 0
    pct_sum = 0
    for r in rows:
        counts[r.status] = counts.get(r.status, 0) + 1
        if r.is_critical:
            critical += 1
        if r.total_float_days is not None and r.total_float_days < 20:
            low_float += 1
        pct_sum += r.percent_complete or 0
    return ScheduleHealth(
        total_activities=total,
        completed=counts.get(ActivityStatus.completed, 0),
        in_progress=counts.get(ActivityStatus.in_progress, 0),
        not_started=counts.get(ActivityStatus.not_started, 0),
        on_hold=counts.get(ActivityStatus.on_hold, 0),
        critical_activities=critical,
        low_float_activities=low_float,
        percent_complete_avg=round(pct_sum / total, 2),
    )
