"""Reporting & Export models.

Distilled from `meridian_track_a_11_reporting_export_persistence.py`.
Covers the three pillars of Module 11:

- `ReportTemplate` — the catalogue of consumable templates (Board Pack,
  Monthly PMO, Gate Evidence Pack, etc.) available to an individual project.
- `ExportJob` — a user-authored instance of a template that the worker will
  render into a PDF / Excel / combined artefact. Carries a live progress
  percentage and a final `artifact_url` once the job is `Ready`.
- `ArchiveRecord` — the long-term register of previously-issued artefacts
  (after a job has been superseded or rolled off the live queue) with a
  denormalised comma-separated tag list for search/filter.

All three are project- and tenant-scoped with `(project_id, <natural key>)`
uniqueness so that the human-addressable reference ids stay stable per
project. `ExportJob.template_id` and `ArchiveRecord.export_job_id` are both
nullable — ad-hoc exports that were not spawned from a template (or archive
rows that were uploaded manually) remain representable.

`ArchiveRecord.tags_csv` is persisted as a comma-joined string to avoid a
join table for the MVP; the schema and router flatten this into a list
of strings on the wire.

Meridian Airport PMO suite
(c) GV Softwares. Developed by Gaurav Vatsa. All rights reserved.
Proprietary — unauthorised copying, distribution, modification or use prohibited.
"""
from __future__ import annotations

from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TenantScopedMixin, TimestampMixin
from app.models.enums import ExportJobStatus, ReportFormat, ReportTemplateType


class ReportTemplate(Base, TimestampMixin, TenantScopedMixin):
    """Reusable template definition for the reporting suite.

    `section_count` is the count of sections the template composes — acts as a
    lightweight proxy for template complexity on the dashboard. `enabled`
    toggles whether the template is selectable when authoring a new export
    job (disabled templates remain on the register so historic jobs keep
    their reference intact).
    """

    __tablename__ = "report_templates"
    __table_args__ = (
        UniqueConstraint(
            "project_id", "name", name="uq_report_templates_project_name"
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    template_type: Mapped[ReportTemplateType] = mapped_column(
        SAEnum(ReportTemplateType), nullable=False
    )
    audience: Mapped[str] = mapped_column(String(255), nullable=False)
    section_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    default_format: Mapped[ReportFormat] = mapped_column(
        SAEnum(ReportFormat), nullable=False
    )
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class ExportJob(Base, TimestampMixin, TenantScopedMixin):
    """A single authored export instance driven through the generation queue.

    `template_id` is nullable so one-off exports (not derived from a catalogued
    template) still fit on the same register. `progress_pct` is the live
    heartbeat a worker updates as generation advances; `artifact_url` is
    populated once the job has reached ``Ready``; `error_message` carries the
    reason on ``Failed``.
    """

    __tablename__ = "export_jobs"
    __table_args__ = (
        UniqueConstraint(
            "project_id", "ref", name="uq_export_jobs_project_ref"
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id"), index=True, nullable=False
    )
    template_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("report_templates.id"),
        nullable=True,
        index=True,
    )
    ref: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    format: Mapped[ReportFormat] = mapped_column(
        SAEnum(ReportFormat), nullable=False
    )
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    created_month: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[ExportJobStatus] = mapped_column(
        SAEnum(ExportJobStatus), nullable=False, default=ExportJobStatus.draft
    )
    progress_pct: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    artifact_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class ArchiveRecord(Base, TimestampMixin, TenantScopedMixin):
    """Long-term archive of exported artefacts.

    An archive row can optionally reference the `ExportJob` it originated
    from (``export_job_id``) but uploaded / externally-sourced artefacts are
    also allowed with a null reference. Tags are stored as a CSV string for
    MVP simplicity — the schema layer normalises them to a list on ingress
    and egress.
    """

    __tablename__ = "archive_records"
    __table_args__ = (
        UniqueConstraint(
            "project_id", "ref", name="uq_archive_records_project_ref"
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id"), index=True, nullable=False
    )
    export_job_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("export_jobs.id"), nullable=True, index=True
    )
    ref: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    format: Mapped[ReportFormat] = mapped_column(
        SAEnum(ReportFormat), nullable=False
    )
    generated_month: Mapped[int] = mapped_column(Integer, nullable=False)
    size_mb: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    tags_csv: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    artifact_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
