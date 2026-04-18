"""governance — stage gate definitions, evidence, approvals, decisions,
and gate↔package links.

Revision ID: 0002_governance
Revises: 0001_baseline
Create Date: 2026-04-18

Adds the Stage Gate Governance domain on top of the baseline schema. Uses
non-native enums to keep SQLite (test) and Postgres (prod) on the same
DDL path.

Meridian Airport PMO suite
(c) GV Softwares. Developed by Gaurav Vatsa. All rights reserved.
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002_governance"
down_revision: Union[str, None] = "0001_baseline"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _enum(name: str, *values: str) -> sa.Enum:
    return sa.Enum(*values, name=name, native_enum=False)


def upgrade() -> None:
    # ---- gate_definitions ----
    op.create_table(
        "gate_definitions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id"), nullable=False, index=True),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("purpose", sa.Text, nullable=False),
        sa.Column("target_month", sa.Integer, nullable=False),
        sa.Column(
            "status",
            _enum("gate_status", "Complete", "Active", "Upcoming", "Blocked"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("project_id", "code", name="uq_gate_definitions_project_code"),
    )

    # ---- gate_package_links ----
    op.create_table(
        "gate_package_links",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id"), nullable=False, index=True),
        sa.Column("gate_definition_id", sa.String(36), sa.ForeignKey("gate_definitions.id"), nullable=False, index=True),
        sa.Column("package_id", sa.String(36), sa.ForeignKey("work_packages.id"), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("gate_definition_id", "package_id", name="uq_gate_package_links_gate_package"),
    )

    # ---- gate_evidence_items ----
    op.create_table(
        "gate_evidence_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id"), nullable=False, index=True),
        sa.Column("gate_definition_id", sa.String(36), sa.ForeignKey("gate_definitions.id"), nullable=False, index=True),
        sa.Column("package_id", sa.String(36), sa.ForeignKey("work_packages.id"), nullable=True, index=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column(
            "category",
            _enum(
                "evidence_category",
                "Strategy",
                "Commercial",
                "Design",
                "Controls",
                "Readiness",
                "Authority",
            ),
            nullable=False,
        ),
        sa.Column("required", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column(
            "status",
            _enum("evidence_status", "Missing", "Draft", "Submitted", "Accepted"),
            nullable=False,
        ),
        sa.Column("owner", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ---- gate_approvals ----
    op.create_table(
        "gate_approvals",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id"), nullable=False, index=True),
        sa.Column("gate_definition_id", sa.String(36), sa.ForeignKey("gate_definitions.id"), nullable=False, index=True),
        sa.Column("approver", sa.String(255), nullable=False),
        sa.Column("role", sa.String(255), nullable=False),
        sa.Column(
            "status",
            _enum("approval_status", "Pending", "Approved", "Rejected"),
            nullable=False,
        ),
        sa.Column("response_date", sa.String(25), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ---- gate_decisions ----
    op.create_table(
        "gate_decisions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id"), nullable=False, index=True),
        sa.Column("gate_definition_id", sa.String(36), sa.ForeignKey("gate_definitions.id"), nullable=False, index=True),
        sa.Column("meeting_ref", sa.String(100), nullable=False),
        sa.Column("decision_date", sa.String(25), nullable=False),
        sa.Column(
            "outcome",
            _enum(
                "decision_outcome",
                "Proceed",
                "Proceed with Conditions",
                "Hold",
                "Rejected",
            ),
            nullable=False,
        ),
        sa.Column("summary", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    for table in [
        "gate_decisions",
        "gate_approvals",
        "gate_evidence_items",
        "gate_package_links",
        "gate_definitions",
    ]:
        op.drop_table(table)
