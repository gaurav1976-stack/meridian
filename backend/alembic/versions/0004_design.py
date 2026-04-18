"""design — design packages, deliverables, interfaces, BIM coordination items.

Revision ID: 0004_design
Revises: 0003_commercial
Create Date: 2026-04-18

Adds the Design Management domain. Non-native enums keep SQLite (test) and
Postgres (prod) on the same DDL path. RIBA stage is stored as the bare digit
("0".."6") to match the IATA ADRM / RIBA Plan of Work alignment.

Meridian Airport PMO suite
(c) GV Softwares. Developed by Gaurav Vatsa. All rights reserved.
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0004_design"
down_revision: Union[str, None] = "0003_commercial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _enum(name: str, *values: str) -> sa.Enum:
    return sa.Enum(*values, name=name, native_enum=False)


def upgrade() -> None:
    # ---- design_packages ----
    op.create_table(
        "design_packages",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id"), nullable=False, index=True),
        sa.Column("package_id", sa.String(36), sa.ForeignKey("work_packages.id"), nullable=True, index=True),
        sa.Column("code", sa.String(100), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("lead_discipline", sa.String(100), nullable=False),
        sa.Column(
            "stage",
            _enum("riba_stage", "0", "1", "2", "3", "4", "5", "6"),
            nullable=False,
        ),
        sa.Column("maturity_pct", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "status",
            _enum(
                "design_package_status",
                "Draft",
                "In Review",
                "Coordinating",
                "Ready for Issue",
                "Frozen",
            ),
            nullable=False,
        ),
        sa.Column("freeze_planned_month", sa.Integer, nullable=False),
        sa.Column("freeze_current_month", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint(
            "project_id", "code", name="uq_design_packages_project_code"
        ),
    )

    # ---- design_deliverables ----
    op.create_table(
        "design_deliverables",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id"), nullable=False, index=True),
        sa.Column("design_package_id", sa.String(36), sa.ForeignKey("design_packages.id"), nullable=True, index=True),
        sa.Column("package_id", sa.String(36), sa.ForeignKey("work_packages.id"), nullable=True, index=True),
        sa.Column("ref", sa.String(100), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("discipline", sa.String(100), nullable=False),
        sa.Column(
            "deliverable_type",
            _enum(
                "deliverable_type",
                "Drawing",
                "Report",
                "Calculation",
                "Specification",
                "Schedule",
            ),
            nullable=False,
        ),
        sa.Column(
            "stage",
            _enum("riba_stage", "0", "1", "2", "3", "4", "5", "6"),
            nullable=False,
        ),
        sa.Column("due_month", sa.Integer, nullable=False),
        sa.Column(
            "status",
            _enum(
                "deliverable_status",
                "WIP",
                "Shared",
                "Published",
                "Accepted",
                "Overdue",
            ),
            nullable=False,
        ),
        sa.Column("owner", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint(
            "project_id", "ref", name="uq_design_deliverables_project_ref"
        ),
    )

    # ---- design_interface_items ----
    op.create_table(
        "design_interface_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id"), nullable=False, index=True),
        sa.Column("ref", sa.String(100), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("package_a_id", sa.String(36), sa.ForeignKey("work_packages.id"), nullable=False, index=True),
        sa.Column("package_b_id", sa.String(36), sa.ForeignKey("work_packages.id"), nullable=False, index=True),
        sa.Column("owner", sa.String(255), nullable=False),
        sa.Column("severity", sa.Integer, nullable=False, server_default="1"),
        sa.Column(
            "status",
            _enum(
                "interface_status",
                "Open",
                "Assigned",
                "Resolving",
                "Closed",
                "Escalated",
            ),
            nullable=False,
        ),
        sa.Column("due_month", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint(
            "project_id", "ref", name="uq_design_interface_items_project_ref"
        ),
    )

    # ---- bim_coordination_items ----
    op.create_table(
        "bim_coordination_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id"), nullable=False, index=True),
        sa.Column("workstream", sa.String(100), nullable=False),
        sa.Column("clash_open", sa.Integer, nullable=False, server_default="0"),
        sa.Column("clash_critical", sa.Integer, nullable=False, server_default="0"),
        sa.Column("federation_ready", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column(
            "model_share_status",
            _enum("model_share_status", "WIP", "Shared", "Published"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    for table in [
        "bim_coordination_items",
        "design_interface_items",
        "design_deliverables",
        "design_packages",
    ]:
        op.drop_table(table)
