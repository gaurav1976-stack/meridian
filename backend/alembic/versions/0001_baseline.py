"""baseline schema — tenants, users, projects, work packages, contracts,
numbering rules, metadata fields, workflows, schedule, risks, opportunities,
audit logs.

Revision ID: 0001_baseline
Revises:
Create Date: 2026-04-18

This is the first real migration — covers the tables defined in
`app.models.core`, `app.models.project_setup`, `app.models.schedule`,
`app.models.risk`. Remaining Track A domains (governance, commercial, design,
documents, accountability, orat, reporting, search) get their own baselines as
they are ported.

Meridian Airport PMO suite
(c) GV Softwares. Developed by Gaurav Vatsa. All rights reserved.
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001_baseline"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ---------------------------------------------------------------------------
# Enum string enumerations — emit once so every consuming column reuses them.
# We use SAEnum with `create_type=False` + explicit op.execute for Postgres to
# keep this migration portable to SQLite in tests.
# ---------------------------------------------------------------------------


def _enum(name: str, *values: str) -> sa.Enum:
    return sa.Enum(*values, name=name, native_enum=False)


def upgrade() -> None:
    # ---- tenants ----
    op.create_table(
        "tenants",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column("region", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ---- users ----
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True, index=True),
        sa.Column(
            "role",
            _enum(
                "user_role",
                "Super Admin",
                "Tenant Admin",
                "Programme Director",
                "PMO Director",
                "Project Director",
                "Controls Manager",
                "Document Controller",
                "Design Manager",
                "Commercial Manager",
                "Risk Manager",
                "ORAT Manager",
                "Package Manager",
                "Reviewer / Approver",
                "External Consultant",
                "Contractor User",
                "Viewer",
            ),
            nullable=False,
        ),
        sa.Column("external_subject", sa.String(255), nullable=True, index=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ---- projects ----
    op.create_table(
        "projects",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("code", sa.String(50), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False, index=True),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column(
            "status",
            _enum("project_status", "Active", "Planned", "On Hold", "Closed"),
            nullable=False,
        ),
        sa.Column("stage", sa.String(100), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "code", name="uq_projects_tenant_code"),
    )

    # ---- project_memberships ----
    op.create_table(
        "project_memberships",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id"), nullable=False, index=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("role", _enum("user_role_membership", "Super Admin", "Tenant Admin", "Programme Director", "PMO Director", "Project Director", "Controls Manager", "Document Controller", "Design Manager", "Commercial Manager", "Risk Manager", "ORAT Manager", "Package Manager", "Reviewer / Approver", "External Consultant", "Contractor User", "Viewer"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("project_id", "user_id", name="uq_project_memberships_project_user"),
    )

    # ---- work_packages ----
    op.create_table(
        "work_packages",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id"), nullable=False, index=True),
        sa.Column("code", sa.String(50), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("package_type", sa.String(50), nullable=True),
        sa.Column("status", sa.String(50), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("project_id", "code", name="uq_work_packages_project_code"),
    )

    # ---- contracts ----
    op.create_table(
        "contracts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id"), nullable=False, index=True),
        sa.Column("reference", sa.String(80), nullable=False, index=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("contractor", sa.String(255), nullable=True),
        sa.Column(
            "form",
            _enum(
                "contract_form",
                "NEC4 ECC",
                "NEC4 PSC",
                "NEC4 TSC",
                "FIDIC Red Book",
                "FIDIC Yellow Book",
                "FIDIC Silver Book",
                "JCT",
                "Bespoke",
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            _enum("contract_status", "Draft", "Awarded", "Active", "Completed", "Closed"),
            nullable=False,
        ),
        sa.Column("value_amount", sa.Float, nullable=True),
        sa.Column("value_currency", sa.String(8), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("project_id", "reference", name="uq_contracts_project_reference"),
    )

    # ---- numbering_rules ----
    op.create_table(
        "numbering_rules",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id"), nullable=False, index=True),
        sa.Column("entity", sa.String(50), nullable=False),
        sa.Column("pattern", sa.String(255), nullable=False),
        sa.Column("next_sequence", sa.Integer, nullable=False, server_default="1"),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ---- metadata_field_definitions ----
    op.create_table(
        "metadata_field_definitions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id"), nullable=False, index=True),
        sa.Column("entity", sa.String(50), nullable=False),
        sa.Column("field_key", sa.String(80), nullable=False),
        sa.Column("label", sa.String(255), nullable=False),
        sa.Column("field_type", sa.String(50), nullable=False),
        sa.Column("is_required", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("options_csv", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ---- workflow_definitions ----
    op.create_table(
        "workflow_definitions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id"), nullable=False, index=True),
        sa.Column("entity", sa.String(50), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("approval_mode", sa.String(50), nullable=False, server_default="Sequential"),
        sa.Column("states_csv", sa.Text, nullable=False),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ---- schedule_files ----
    op.create_table(
        "schedule_files",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id"), nullable=False, index=True),
        sa.Column("package_id", sa.String(36), sa.ForeignKey("work_packages.id"), nullable=True, index=True),
        sa.Column(
            "category",
            _enum(
                "schedule_file_category",
                "Programme Master",
                "Project Master",
                "Contractor Baseline",
                "Contractor Update",
                "Package",
                "Authority / Approval",
                "Look-Ahead",
                "Mitigation / Recovery",
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            _enum("schedule_file_status", "Draft", "Issued", "Archived"),
            nullable=False,
        ),
        sa.Column("revision", sa.String(20), nullable=False, server_default="R0"),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("issued_date", sa.Date, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("storage_key", sa.String(512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ---- schedule_activities ----
    op.create_table(
        "schedule_activities",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id"), nullable=False, index=True),
        sa.Column("schedule_file_id", sa.String(36), sa.ForeignKey("schedule_files.id"), nullable=True, index=True),
        sa.Column("package_id", sa.String(36), sa.ForeignKey("work_packages.id"), nullable=True, index=True),
        sa.Column("activity_id_external", sa.String(80), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column(
            "status",
            _enum("activity_status", "Not Started", "In Progress", "Completed", "On Hold"),
            nullable=False,
        ),
        sa.Column(
            "scenario",
            _enum("schedule_scenario", "Baseline", "Forecast", "Actual", "Mitigation"),
            nullable=False,
        ),
        sa.Column("planned_start", sa.Date, nullable=True),
        sa.Column("planned_finish", sa.Date, nullable=True),
        sa.Column("actual_start", sa.Date, nullable=True),
        sa.Column("actual_finish", sa.Date, nullable=True),
        sa.Column("duration_days", sa.Integer, nullable=True),
        sa.Column("total_float_days", sa.Integer, nullable=True),
        sa.Column("percent_complete", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_critical", sa.Boolean, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ---- activity_dependencies ----
    op.create_table(
        "activity_dependencies",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id"), nullable=False, index=True),
        sa.Column("predecessor_id", sa.String(36), sa.ForeignKey("schedule_activities.id"), nullable=False, index=True),
        sa.Column("successor_id", sa.String(36), sa.ForeignKey("schedule_activities.id"), nullable=False, index=True),
        sa.Column(
            "dependency_type",
            _enum("dependency_type", "FS", "SS", "FF", "SF"),
            nullable=False,
        ),
        sa.Column("lag_days", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ---- schedule_snapshots ----
    op.create_table(
        "schedule_snapshots",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id"), nullable=False, index=True),
        sa.Column("schedule_file_id", sa.String(36), sa.ForeignKey("schedule_files.id"), nullable=True, index=True),
        sa.Column("label", sa.String(255), nullable=False),
        sa.Column("snapshot_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metrics_json", sa.Text, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ---- risk_items ----
    op.create_table(
        "risk_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id"), nullable=False, index=True),
        sa.Column("package_id", sa.String(36), sa.ForeignKey("work_packages.id"), nullable=True, index=True),
        sa.Column("code", sa.String(40), nullable=False, index=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column(
            "category",
            _enum(
                "risk_category",
                "Technical",
                "Commercial",
                "Programme",
                "Regulatory / Political",
                "Operational",
                "Force Majeure",
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            _enum("risk_status", "Identified", "Assessed", "Mitigating", "Monitoring", "Closed"),
            nullable=False,
        ),
        sa.Column("likelihood", sa.Integer, nullable=False, server_default="3"),
        sa.Column("impact", sa.Integer, nullable=False, server_default="3"),
        sa.Column("mitigated_likelihood", sa.Integer, nullable=True),
        sa.Column("mitigated_impact", sa.Integer, nullable=True),
        sa.Column("owner", sa.String(255), nullable=True),
        sa.Column("mitigation", sa.Text, nullable=True),
        sa.Column("target_closure_date", sa.Date, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ---- opportunity_items ----
    op.create_table(
        "opportunity_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id"), nullable=False, index=True),
        sa.Column("code", sa.String(40), nullable=False, index=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column(
            "status",
            _enum("opportunity_status", "Identified", "Pursuing", "Realised", "Declined"),
            nullable=False,
        ),
        sa.Column("likelihood", sa.Integer, nullable=False, server_default="3"),
        sa.Column("benefit", sa.Integer, nullable=False, server_default="3"),
        sa.Column("owner", sa.String(255), nullable=True),
        sa.Column("target_realisation_date", sa.Date, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ---- audit_logs ----
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("actor_user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("entity_type", sa.String(100), nullable=False, index=True),
        sa.Column("entity_id", sa.String(36), nullable=False, index=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("details", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    for table in [
        "audit_logs",
        "opportunity_items",
        "risk_items",
        "schedule_snapshots",
        "activity_dependencies",
        "schedule_activities",
        "schedule_files",
        "workflow_definitions",
        "metadata_field_definitions",
        "numbering_rules",
        "contracts",
        "work_packages",
        "project_memberships",
        "projects",
        "users",
        "tenants",
    ]:
        op.drop_table(table)
