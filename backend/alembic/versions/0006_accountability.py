"""accountability — meetings, action items, compliance items.

Revision ID: 0006_accountability
Revises: 0005_documents
Create Date: 2026-04-18

Adds the Meetings, Actions & Compliance domain (Module 09). Non-native enums
keep SQLite (test) and Postgres (prod) on the same DDL path. `package_id` is
nullable for both action_items and compliance_items — a handful of obligations
(e.g. programme-level governance) do not belong to any single package.

Meridian Airport PMO suite
(c) GV Softwares. Developed by Gaurav Vatsa. All rights reserved.
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0006_accountability"
down_revision: Union[str, None] = "0005_documents"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _enum(name: str, *values: str) -> sa.Enum:
    return sa.Enum(*values, name=name, native_enum=False)


def upgrade() -> None:
    # ---- meeting_records ----
    op.create_table(
        "meeting_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id"), nullable=False, index=True),
        sa.Column("ref", sa.String(100), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column(
            "meeting_type",
            _enum(
                "meeting_type",
                "Governance Board",
                "Package Review",
                "Design Review",
                "Commercial Review",
                "ORAT Review",
                "Coordination",
            ),
            nullable=False,
        ),
        sa.Column("month", sa.Integer, nullable=False),
        sa.Column("chair", sa.String(255), nullable=False),
        sa.Column("attendee_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "linked_module",
            _enum(
                "linked_module",
                "Gate",
                "Risk",
                "Document",
                "Commercial",
                "Programme",
                "ORAT",
            ),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint(
            "project_id", "ref", name="uq_meeting_records_project_ref"
        ),
    )

    # ---- action_items ----
    op.create_table(
        "action_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id"), nullable=False, index=True),
        sa.Column("package_id", sa.String(36), sa.ForeignKey("work_packages.id"), nullable=True, index=True),
        sa.Column("ref", sa.String(100), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("owner", sa.String(255), nullable=False),
        sa.Column(
            "source_type",
            _enum(
                "action_source_type",
                "Meeting",
                "Gate",
                "Risk",
                "Document",
                "Commercial",
                "ORAT",
            ),
            nullable=False,
        ),
        sa.Column("source_ref", sa.String(255), nullable=False),
        sa.Column(
            "priority",
            _enum("action_priority", "Critical", "High", "Medium", "Low"),
            nullable=False,
        ),
        sa.Column("due_month", sa.Integer, nullable=False),
        sa.Column(
            "status",
            _enum(
                "action_status",
                "Open",
                "In Progress",
                "Awaiting Review",
                "Closed",
                "Overdue",
            ),
            nullable=False,
        ),
        sa.Column(
            "closure_evidence_pct", sa.Integer, nullable=False, server_default="0"
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint(
            "project_id", "ref", name="uq_action_items_project_ref"
        ),
    )

    # ---- compliance_items ----
    op.create_table(
        "compliance_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id"), nullable=False, index=True),
        sa.Column("package_id", sa.String(36), sa.ForeignKey("work_packages.id"), nullable=True, index=True),
        sa.Column("ref", sa.String(100), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column(
            "domain",
            _enum(
                "compliance_domain",
                "Governance",
                "Document Control",
                "Commercial",
                "Design",
                "ORAT",
                "Programme",
            ),
            nullable=False,
        ),
        sa.Column("owner", sa.String(255), nullable=False),
        sa.Column("due_month", sa.Integer, nullable=False),
        sa.Column(
            "status",
            _enum(
                "compliance_status",
                "Open",
                "In Progress",
                "Compliant",
                "Non-Compliant",
                "Overdue",
            ),
            nullable=False,
        ),
        sa.Column("evidence_pct", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint(
            "project_id", "ref", name="uq_compliance_items_project_ref"
        ),
    )


def downgrade() -> None:
    for table in ["compliance_items", "action_items", "meeting_records"]:
        op.drop_table(table)
