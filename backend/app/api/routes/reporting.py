"""Reporting & Export router.

Port of `meridian_track_a_11_reporting_export_persistence.py` FastAPI
handlers into a single project-scoped APIRouter at
`/projects/{project_id}/reporting`. Sub-resources live under the same
project prefix:

- ``"/templates"``              — report template register (catalogue)
- ``"/export-jobs"``            — authored export jobs + live progress
- ``"/archive"``                — long-term artefact archive
- ``"/summary"``                — project-wide reporting rollup
- ``"/template-pressure"``      — per-template usage heat-map

Tenant isolation via `get_project_for_view/edit`; audit-log on every
mutation; single commit per request. Patch routes are kept project-scoped
(unlike the loose Track A prototype's `/report-templates/{id}` handlers)
so tenant_id can never be bypassed via a bare id. `ArchiveRecord.tags` is
exposed on the wire as `list[str]` but persisted as a comma-separated
string — `_archive_to_read` is the only ORM-to-schema adapter needed for
this module.

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
from app.models.core import Project
from app.models.enums import ExportJobStatus, ReportFormat, ReportTemplateType
from app.models.reporting import ArchiveRecord, ExportJob, ReportTemplate
from app.schemas.reporting import (
    ArchiveRecordCreate,
    ArchiveRecordRead,
    ArchiveRecordUpdate,
    ExportJobCreate,
    ExportJobRead,
    ExportJobUpdate,
    ReportingSummary,
    ReportTemplateCreate,
    ReportTemplateRead,
    ReportTemplateUpdate,
    TemplateUsagePressure,
)
from app.services.audit import write_audit_log

router = APIRouter(prefix="/projects/{project_id}/reporting")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _tags_to_csv(tags: Optional[List[str]]) -> Optional[str]:
    if tags is None:
        return None
    cleaned = [t.strip() for t in tags if t and t.strip()]
    return ", ".join(cleaned) if cleaned else None


def _csv_to_tags(value: Optional[str]) -> List[str]:
    if not value:
        return []
    return [t.strip() for t in value.split(",") if t.strip()]


def _archive_to_read(item: ArchiveRecord) -> ArchiveRecordRead:
    """Adapt an ORM row to the public schema — tag CSV → list."""
    return ArchiveRecordRead(
        id=item.id,
        project_id=item.project_id,
        tenant_id=item.tenant_id,
        export_job_id=item.export_job_id,
        ref=item.ref,
        title=item.title,
        format=item.format,
        generated_month=item.generated_month,
        size_mb=item.size_mb,
        tags=_csv_to_tags(item.tags_csv),
        artifact_url=item.artifact_url,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def _validate_template(
    db: Session, tenant_id: str, project_id: str, template_id: str
) -> ReportTemplate:
    tpl = (
        db.query(ReportTemplate)
        .filter(
            ReportTemplate.id == template_id,
            ReportTemplate.project_id == project_id,
            ReportTemplate.tenant_id == tenant_id,
        )
        .first()
    )
    if tpl is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report template {template_id} not found for project.",
        )
    return tpl


def _validate_export_job(
    db: Session, tenant_id: str, project_id: str, job_id: str
) -> ExportJob:
    job = (
        db.query(ExportJob)
        .filter(
            ExportJob.id == job_id,
            ExportJob.project_id == project_id,
            ExportJob.tenant_id == tenant_id,
        )
        .first()
    )
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Export job {job_id} not found for project.",
        )
    return job


# ---------------------------------------------------------------------------
# Report Templates
# ---------------------------------------------------------------------------


@router.get("/templates", response_model=List[ReportTemplateRead])
def list_report_templates(
    template_type: Optional[ReportTemplateType] = Query(default=None),
    enabled: Optional[bool] = Query(default=None),
    project: Project = Depends(get_project_for_view),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> List[ReportTemplateRead]:
    q = db.query(ReportTemplate).filter(
        ReportTemplate.project_id == project.id,
        ReportTemplate.tenant_id == principal.tenant_id,
    )
    if template_type is not None:
        q = q.filter(ReportTemplate.template_type == template_type)
    if enabled is not None:
        q = q.filter(ReportTemplate.enabled == enabled)
    rows = q.order_by(ReportTemplate.name.asc()).all()
    return [ReportTemplateRead.model_validate(r) for r in rows]


@router.post(
    "/templates",
    response_model=ReportTemplateRead,
    status_code=status.HTTP_201_CREATED,
)
def create_report_template(
    payload: ReportTemplateCreate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> ReportTemplateRead:
    duplicate = (
        db.query(ReportTemplate)
        .filter(
            ReportTemplate.project_id == project.id,
            ReportTemplate.tenant_id == principal.tenant_id,
            ReportTemplate.name == payload.name,
        )
        .first()
    )
    if duplicate is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Report template {payload.name!r} already exists in project.",
        )

    item = ReportTemplate(
        tenant_id=principal.tenant_id,
        project_id=project.id,
        name=payload.name,
        template_type=payload.template_type,
        audience=payload.audience,
        section_count=payload.section_count,
        default_format=payload.default_format,
        enabled=payload.enabled,
    )
    db.add(item)
    db.flush()
    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="ReportTemplate",
        entity_id=item.id,
        action="created",
        details={
            "name": item.name,
            "template_type": item.template_type.value,
            "default_format": item.default_format.value,
        },
    )
    db.commit()
    db.refresh(item)
    return ReportTemplateRead.model_validate(item)


@router.patch("/templates/{template_id}", response_model=ReportTemplateRead)
def update_report_template(
    template_id: str,
    payload: ReportTemplateUpdate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> ReportTemplateRead:
    item = _validate_template(
        db, principal.tenant_id, project.id, template_id
    )
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(item, field, value)
    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="ReportTemplate",
        entity_id=item.id,
        action="updated",
        details=data,
    )
    db.commit()
    db.refresh(item)
    return ReportTemplateRead.model_validate(item)


# ---------------------------------------------------------------------------
# Export Jobs
# ---------------------------------------------------------------------------


@router.get("/export-jobs", response_model=List[ExportJobRead])
def list_export_jobs(
    status_filter: Optional[ExportJobStatus] = Query(
        default=None, alias="status"
    ),
    template_id: Optional[str] = Query(default=None),
    project: Project = Depends(get_project_for_view),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> List[ExportJobRead]:
    q = db.query(ExportJob).filter(
        ExportJob.project_id == project.id,
        ExportJob.tenant_id == principal.tenant_id,
    )
    if status_filter is not None:
        q = q.filter(ExportJob.status == status_filter)
    if template_id is not None:
        q = q.filter(ExportJob.template_id == template_id)
    rows = q.order_by(
        ExportJob.created_month.desc(), ExportJob.ref.asc()
    ).all()
    return [ExportJobRead.model_validate(r) for r in rows]


@router.post(
    "/export-jobs",
    response_model=ExportJobRead,
    status_code=status.HTTP_201_CREATED,
)
def create_export_job(
    payload: ExportJobCreate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> ExportJobRead:
    if payload.template_id is not None:
        _validate_template(
            db, principal.tenant_id, project.id, payload.template_id
        )

    duplicate = (
        db.query(ExportJob)
        .filter(
            ExportJob.project_id == project.id,
            ExportJob.tenant_id == principal.tenant_id,
            ExportJob.ref == payload.ref,
        )
        .first()
    )
    if duplicate is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Export job ref {payload.ref!r} already exists in project.",
        )

    item = ExportJob(
        tenant_id=principal.tenant_id,
        project_id=project.id,
        template_id=payload.template_id,
        ref=payload.ref,
        title=payload.title,
        format=payload.format,
        created_by=payload.created_by,
        created_month=payload.created_month,
        status=payload.status,
        progress_pct=payload.progress_pct,
        artifact_url=payload.artifact_url,
        error_message=payload.error_message,
    )
    db.add(item)
    db.flush()
    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="ExportJob",
        entity_id=item.id,
        action="created",
        details={
            "ref": item.ref,
            "format": item.format.value,
            "status": item.status.value,
        },
    )
    db.commit()
    db.refresh(item)
    return ExportJobRead.model_validate(item)


@router.patch("/export-jobs/{job_id}", response_model=ExportJobRead)
def update_export_job(
    job_id: str,
    payload: ExportJobUpdate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> ExportJobRead:
    item = _validate_export_job(
        db, principal.tenant_id, project.id, job_id
    )
    data = payload.model_dump(exclude_unset=True)
    if "template_id" in data and data["template_id"]:
        _validate_template(
            db, principal.tenant_id, project.id, data["template_id"]
        )
    for field, value in data.items():
        setattr(item, field, value)
    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="ExportJob",
        entity_id=item.id,
        action="updated",
        details=data,
    )
    db.commit()
    db.refresh(item)
    return ExportJobRead.model_validate(item)


# ---------------------------------------------------------------------------
# Archive Records
# ---------------------------------------------------------------------------


@router.get("/archive", response_model=List[ArchiveRecordRead])
def list_archive_records(
    format_filter: Optional[ReportFormat] = Query(
        default=None, alias="format"
    ),
    project: Project = Depends(get_project_for_view),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> List[ArchiveRecordRead]:
    q = db.query(ArchiveRecord).filter(
        ArchiveRecord.project_id == project.id,
        ArchiveRecord.tenant_id == principal.tenant_id,
    )
    if format_filter is not None:
        q = q.filter(ArchiveRecord.format == format_filter)
    rows = q.order_by(
        ArchiveRecord.generated_month.desc(), ArchiveRecord.ref.asc()
    ).all()
    return [_archive_to_read(r) for r in rows]


@router.post(
    "/archive",
    response_model=ArchiveRecordRead,
    status_code=status.HTTP_201_CREATED,
)
def create_archive_record(
    payload: ArchiveRecordCreate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> ArchiveRecordRead:
    if payload.export_job_id is not None:
        _validate_export_job(
            db, principal.tenant_id, project.id, payload.export_job_id
        )

    duplicate = (
        db.query(ArchiveRecord)
        .filter(
            ArchiveRecord.project_id == project.id,
            ArchiveRecord.tenant_id == principal.tenant_id,
            ArchiveRecord.ref == payload.ref,
        )
        .first()
    )
    if duplicate is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Archive ref {payload.ref!r} already exists in project.",
        )

    item = ArchiveRecord(
        tenant_id=principal.tenant_id,
        project_id=project.id,
        export_job_id=payload.export_job_id,
        ref=payload.ref,
        title=payload.title,
        format=payload.format,
        generated_month=payload.generated_month,
        size_mb=payload.size_mb,
        tags_csv=_tags_to_csv(payload.tags),
        artifact_url=payload.artifact_url,
    )
    db.add(item)
    db.flush()
    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="ArchiveRecord",
        entity_id=item.id,
        action="created",
        details={
            "ref": item.ref,
            "format": item.format.value,
            "size_mb": item.size_mb,
        },
    )
    db.commit()
    db.refresh(item)
    return _archive_to_read(item)


@router.patch("/archive/{archive_id}", response_model=ArchiveRecordRead)
def update_archive_record(
    archive_id: str,
    payload: ArchiveRecordUpdate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> ArchiveRecordRead:
    item = (
        db.query(ArchiveRecord)
        .filter(
            ArchiveRecord.id == archive_id,
            ArchiveRecord.project_id == project.id,
            ArchiveRecord.tenant_id == principal.tenant_id,
        )
        .first()
    )
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Archive record not found.",
        )
    data = payload.model_dump(exclude_unset=True)
    if "export_job_id" in data and data["export_job_id"]:
        _validate_export_job(
            db, principal.tenant_id, project.id, data["export_job_id"]
        )
    # `tags` flips back to tags_csv on the ORM.
    if "tags" in data:
        tags_value = data.pop("tags")
        item.tags_csv = _tags_to_csv(tags_value)
    for field, value in data.items():
        setattr(item, field, value)
    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="ArchiveRecord",
        entity_id=item.id,
        action="updated",
        details=data,
    )
    db.commit()
    db.refresh(item)
    return _archive_to_read(item)


# ---------------------------------------------------------------------------
# Rollups
# ---------------------------------------------------------------------------


@router.get("/summary", response_model=ReportingSummary)
def reporting_summary(
    project: Project = Depends(get_project_for_view),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> ReportingSummary:
    templates = (
        db.query(ReportTemplate)
        .filter(
            ReportTemplate.project_id == project.id,
            ReportTemplate.tenant_id == principal.tenant_id,
        )
        .all()
    )
    jobs = (
        db.query(ExportJob)
        .filter(
            ExportJob.project_id == project.id,
            ExportJob.tenant_id == principal.tenant_id,
        )
        .all()
    )
    archives = (
        db.query(ArchiveRecord)
        .filter(
            ArchiveRecord.project_id == project.id,
            ArchiveRecord.tenant_id == principal.tenant_id,
        )
        .all()
    )

    active_statuses = {ExportJobStatus.queued, ExportJobStatus.generating}
    active_jobs = sum(1 for j in jobs if j.status in active_statuses)
    ready_jobs = sum(1 for j in jobs if j.status == ExportJobStatus.ready)
    failed_jobs = sum(1 for j in jobs if j.status == ExportJobStatus.failed)
    enabled_templates = sum(1 for t in templates if t.enabled)
    avg_progress = (
        round(sum(j.progress_pct for j in jobs) / len(jobs)) if jobs else 0
    )

    return ReportingSummary(
        project_id=project.id,
        template_count=len(templates),
        enabled_template_count=enabled_templates,
        job_count=len(jobs),
        active_job_count=active_jobs,
        ready_job_count=ready_jobs,
        failed_job_count=failed_jobs,
        archive_count=len(archives),
        average_job_progress_pct=avg_progress,
    )


@router.get(
    "/template-pressure", response_model=List[TemplateUsagePressure]
)
def template_pressure(
    project: Project = Depends(get_project_for_view),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> List[TemplateUsagePressure]:
    templates = (
        db.query(ReportTemplate)
        .filter(
            ReportTemplate.project_id == project.id,
            ReportTemplate.tenant_id == principal.tenant_id,
        )
        .order_by(ReportTemplate.name.asc())
        .all()
    )
    jobs = (
        db.query(ExportJob)
        .filter(
            ExportJob.project_id == project.id,
            ExportJob.tenant_id == principal.tenant_id,
        )
        .all()
    )

    active_statuses = {ExportJobStatus.queued, ExportJobStatus.generating}
    results: List[TemplateUsagePressure] = []
    for tpl in templates:
        tpl_jobs = [j for j in jobs if j.template_id == tpl.id]
        results.append(
            TemplateUsagePressure(
                template_id=tpl.id,
                template_name=tpl.name,
                template_type=tpl.template_type,
                enabled=tpl.enabled,
                job_count=len(tpl_jobs),
                active_count=sum(
                    1 for j in tpl_jobs if j.status in active_statuses
                ),
                ready_count=sum(
                    1 for j in tpl_jobs if j.status == ExportJobStatus.ready
                ),
                failed_count=sum(
                    1 for j in tpl_jobs if j.status == ExportJobStatus.failed
                ),
            )
        )
    return results
