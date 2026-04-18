"""commercial — package cost controls, commercial change items, contract notices.

Revision ID: 0003_commercial
Revises: 0002_governance
Create Date: 2026-04-18

Adds the Commercial / Cost & Change Control domain. Monetary values are
stored in minor units (integers) to avoid floating-point drift. Non-native
enums keep SQLite (test) and Postgres (prod) on the same DDL path.

Meridian Airport PMO suite
(c) GV Softwares. Developed by Gaurav Vatsa. All rights reserved.
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0003_commercial"
down_revision: Union[str, None] = "0002_governance"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _enum(name: str, *values: str) -> sa.Enum:
    return sa.Enum(*values, name=name, native_enum=False)


def upgrade() -> None:
    # ---- package_cost_controls ----
    op.create_table(
        "package_cost_controls",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id"), nullable=False, index=True),
        sa.Column("package_id", sa.String(36), sa.ForeignKey("work_packages.id"), nullable=False, index=True),
        sa.Column("budget_minor", sa.Integer, nullable=False, server_default="0"),
        sa.Column("committed_minor", sa.Integer, nullable=False, server_default="0"),
        sa.Column("forecast_minor", sa.Integer, nullable=False, server_default="0"),
        sa.Column("actual_minor", sa.Integer, nullable=False, server_default="0"),
        sa.Column("percent_complete", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint(
            "project_id", "package_id", name="uq_package_cost_controls_project_package"
        ),
    )

    # ---- commercial_change_items ----
    op.create_table(
        "commercial_change_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id"), nullable=False, index=True),
        sa.Column("package_id", sa.String(36), sa.ForeignKey("work_packages.id"), nullable=True, index=True),
        sa.Column("ref", sa.String(100), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column(
            "change_type",
            _enum(
                "change_type",
                "Compensation Event",
                "Variation",
                "Client Change",
                "Authority Change",
                "Claim",
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            _enum(
                "change_status",
                "Identified",
                "Notified",
                "Quoted",
                "Approved",
                "Rejected",
                "Implemented",
            ),
            nullable=False,
        ),
        sa.Column("cost_impact_minor", sa.Integer, nullable=False, server_default="0"),
        sa.Column("time_impact_weeks", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "entitlement",
            _enum("entitlement_strength", "Strong", "Moderate", "Weak"),
            nullable=False,
        ),
        sa.Column("owner", sa.String(255), nullable=False),
        sa.Column("cause", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint(
            "project_id", "ref", name="uq_commercial_change_items_project_ref"
        ),
    )

    # ---- commercial_notice_items ----
    op.create_table(
        "commercial_notice_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id"), nullable=False, index=True),
        sa.Column("package_id", sa.String(36), sa.ForeignKey("work_packages.id"), nullable=True, index=True),
        sa.Column("ref", sa.String(100), nullable=False),
        sa.Column("contract_ref", sa.String(100), nullable=False),
        sa.Column(
            "kind",
            _enum(
                "notice_kind",
                "EWN",
                "Notice",
                "CE Notification",
                "Claim Notice",
            ),
            nullable=False,
        ),
        sa.Column("due_days", sa.Integer, nullable=False),
        sa.Column(
            "status",
            _enum("notice_status", "Open", "Issued", "Overdue", "Closed"),
            nullable=False,
        ),
        sa.Column("owner", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint(
            "project_id", "ref", name="uq_commercial_notice_items_project_ref"
        ),
    )


def downgrade() -> None:
    for table in [
        "commercial_notice_items",
        "commercial_change_items",
        "package_cost_controls",
    ]:
        op.drop_table(table)
