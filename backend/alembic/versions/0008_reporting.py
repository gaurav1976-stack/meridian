"""reporting — report templates, export jobs, archive records.

Revision ID: 0008_reporting
Revises: 0007_orat
Create Date: 2026-04-18

Adds the Reporting & Export domain (Module 11). Non-native enums keep
SQLite (test) and Postgres (prod) on the same DDL path.

Nullable FKs:
- ``export_jobs.template_id`` — ad-hoc exports that are not authored from a
  catalogued template remain representable.
- ``archive_records.export_job_id`` — externally-sourced / uploaded
  artefacts can be logged without a parent ExportJob.

Per-project natural keys are enforced via ``(project_id, <natural_key>)``
uniqueness constraints so references remain human-addressable.

Meridian Airport PMO suite
(c) GV Softwares. Developed by Gaurav Vatsa. All rights reserved.
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0008_reporting"
down_revision: Union[str, None] = "0007_orat"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _enum(name: str, *values: str) -> sa.Enum:
    return sa.Enum(*values, name=name, native_enum=False)


def upgrade() -> None:
    # ---- report_templates ----
    op.create_table(
        "report_templates",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "tenant_id",
            sa.String(36),
            sa.ForeignKey("tenants.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "project_id",
            sa.String(36),
            sa.ForeignKey("projects.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column(
            "template_type",
            _enum(
                "report_template_type",
                "Board Pack",
                "Monthly PMO Report",
                "Gate Evidence Pack",
                "Risk Report",
                "Commercial Summary",
                "Document Control Report",
                "ORAT Readiness Pack",
            ),
            nullable=False,
        ),
        sa.Column("audience", sa.String(255), nullable=False),
        sa.Column(
            "section_count", sa.Integer, nullable=False, server_default="1"
        ),
        sa.Column(
            "default_format",
            _enum("report_format", "PDF", "Excel", "PDF + Excel"),
            nullable=False,
        ),
        sa.Column(
            "enabled",
            sa.Boolean,
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "project_id", "name", name="uq_report_templates_project_name"
        ),
    )

    # ---- export_jobs ----
    op.create_table(
        "export_jobs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "tenant_id",
            sa.String(36),
            sa.ForeignKey("tenants.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "project_id",
            sa.String(36),
            sa.ForeignKey("projects.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "template_id",
            sa.String(36),
            sa.ForeignKey("report_templates.id"),
            nullable=True,
            index=True,
        ),
        sa.Column("ref", sa.String(100), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column(
            "format",
            _enum(
                "export_job_format",
                "PDF",
                "Excel",
                "PDF + Excel",
            ),
            nullable=False,
        ),
        sa.Column("created_by", sa.String(255), nullable=False),
        sa.Column("created_month", sa.Integer, nullable=False),
        sa.Column(
            "status",
            _enum(
                "export_job_status",
                "Draft",
                "Queued",
                "Generating",
                "Ready",
                "Failed",
            ),
            nullable=False,
        ),
        sa.Column(
            "progress_pct", sa.Integer, nullable=False, server_default="0"
        ),
        sa.Column("artifact_url", sa.Text, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "project_id", "ref", name="uq_export_jobs_project_ref"
        ),
    )

    # ---- archive_records ----
    op.create_table(
        "archive_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "tenant_id",
            sa.String(36),
            sa.ForeignKey("tenants.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "project_id",
            sa.String(36),
            sa.ForeignKey("projects.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "export_job_id",
            sa.String(36),
            sa.ForeignKey("export_jobs.id"),
            nullable=True,
            index=True,
        ),
        sa.Column("ref", sa.String(100), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column(
            "format",
            _enum(
                "archive_record_format",
                "PDF",
                "Excel",
                "PDF + Excel",
            ),
            nullable=False,
        ),
        sa.Column("generated_month", sa.Integer, nullable=False),
        sa.Column(
            "size_mb", sa.Integer, nullable=False, server_default="1"
        ),
        sa.Column("tags_csv", sa.Text, nullable=True),
        sa.Column("artifact_url", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "project_id", "ref", name="uq_archive_records_project_ref"
        ),
    )


def downgrade() -> None:
    # Drop in dependency-safe order:
    # archive_records references export_jobs, which references report_templates.
    for table in ["archive_records", "export_jobs", "report_templates"]:
        op.drop_table(table)
