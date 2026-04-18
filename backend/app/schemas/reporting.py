"""Reporting & Export — Pydantic schemas.

Mirrors the Track A.11 prototype but typed end-to-end against the shared
enum classes in `app.models.enums`. `ArchiveRecord` persists tags as a CSV
string in the database; the schema surface exposes them as `list[str]` via
`tags` (an `_archive_to_read` helper in the router joins / splits at the
ORM boundary).

Meridian Airport PMO suite
(c) GV Softwares. Developed by Gaurav Vatsa. All rights reserved.
Proprietary — unauthorised copying, distribution, modification or use prohibited.
"""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.enums import ExportJobStatus, ReportFormat, ReportTemplateType
from app.schemas.common import TimestampedOrm


# ---------------------------------------------------------------------------
# Report Template
# ---------------------------------------------------------------------------


class ReportTemplateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    template_type: ReportTemplateType
    audience: str = Field(min_length=1, max_length=255)
    section_count: int = Field(ge=1, le=100, default=1)
    default_format: ReportFormat
    enabled: bool = True


class ReportTemplateUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    template_type: Optional[ReportTemplateType] = None
    audience: Optional[str] = Field(default=None, min_length=1, max_length=255)
    section_count: Optional[int] = Field(default=None, ge=1, le=100)
    default_format: Optional[ReportFormat] = None
    enabled: Optional[bool] = None


class ReportTemplateRead(TimestampedOrm):
    id: str
    project_id: str
    tenant_id: str
    name: str
    template_type: ReportTemplateType
    audience: str
    section_count: int
    default_format: ReportFormat
    enabled: bool


# ---------------------------------------------------------------------------
# Export Job
# ---------------------------------------------------------------------------


class ExportJobCreate(BaseModel):
    template_id: Optional[str] = None
    ref: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=255)
    format: ReportFormat
    created_by: str = Field(min_length=1, max_length=255)
    created_month: int = Field(ge=1, le=240)
    status: ExportJobStatus = ExportJobStatus.queued
    progress_pct: int = Field(ge=0, le=100, default=0)
    artifact_url: Optional[str] = Field(default=None, max_length=1024)
    error_message: Optional[str] = None


class ExportJobUpdate(BaseModel):
    template_id: Optional[str] = None
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    format: Optional[ReportFormat] = None
    created_by: Optional[str] = Field(default=None, min_length=1, max_length=255)
    created_month: Optional[int] = Field(default=None, ge=1, le=240)
    status: Optional[ExportJobStatus] = None
    progress_pct: Optional[int] = Field(default=None, ge=0, le=100)
    artifact_url: Optional[str] = Field(default=None, max_length=1024)
    error_message: Optional[str] = None


class ExportJobRead(TimestampedOrm):
    id: str
    project_id: str
    tenant_id: str
    template_id: Optional[str]
    ref: str
    title: str
    format: ReportFormat
    created_by: str
    created_month: int
    status: ExportJobStatus
    progress_pct: int
    artifact_url: Optional[str]
    error_message: Optional[str]


# ---------------------------------------------------------------------------
# Archive Record
# ---------------------------------------------------------------------------


class ArchiveRecordCreate(BaseModel):
    export_job_id: Optional[str] = None
    ref: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=255)
    format: ReportFormat
    generated_month: int = Field(ge=1, le=240)
    size_mb: int = Field(ge=1)
    tags: List[str] = Field(default_factory=list)
    artifact_url: Optional[str] = Field(default=None, max_length=1024)


class ArchiveRecordUpdate(BaseModel):
    export_job_id: Optional[str] = None
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    format: Optional[ReportFormat] = None
    generated_month: Optional[int] = Field(default=None, ge=1, le=240)
    size_mb: Optional[int] = Field(default=None, ge=1)
    tags: Optional[List[str]] = None
    artifact_url: Optional[str] = Field(default=None, max_length=1024)


class ArchiveRecordRead(TimestampedOrm):
    id: str
    project_id: str
    tenant_id: str
    export_job_id: Optional[str]
    ref: str
    title: str
    format: ReportFormat
    generated_month: int
    size_mb: int
    tags: List[str]
    artifact_url: Optional[str]


# ---------------------------------------------------------------------------
# Rollups
# ---------------------------------------------------------------------------


class ReportingSummary(BaseModel):
    """Project-wide reporting telemetry rollup.

    `active_job_count` aggregates `Queued` + `Generating` (jobs the worker
    queue is responsible for). `ready_job_count` and `failed_job_count` are
    the terminal states reported on the dashboard. `average_job_progress_pct`
    is a blunt indicator of pipeline throughput across all jobs.
    """

    project_id: str
    template_count: int
    enabled_template_count: int
    job_count: int
    active_job_count: int
    ready_job_count: int
    failed_job_count: int
    archive_count: int
    average_job_progress_pct: int


class TemplateUsagePressure(BaseModel):
    """Per-template usage heat-map.

    Shows how many jobs have been authored from each template, how many are
    currently in-flight (`Queued` + `Generating`), and how many terminated
    in `Failed`. Templates with recurring failures surface here as a
    data-quality signal to the PMO.
    """

    template_id: str
    template_name: str
    template_type: ReportTemplateType
    enabled: bool
    job_count: int
    active_count: int
    ready_count: int
    failed_count: int
