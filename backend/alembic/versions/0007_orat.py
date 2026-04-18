"""orat — ORAT workstreams, trials, training groups, handover items.

Revision ID: 0007_orat
Revises: 0006_accountability
Create Date: 2026-04-18

Adds the ORAT Readiness & Handover domain (Module 10). Non-native enums keep
SQLite (test) and Postgres (prod) on the same DDL path.

Nullable FKs:
- `orat_trials.workstream_id` — integrated / cross-workstream trials do not
  belong to a single workstream.
- `handover_items.package_id` — some handovers (ATC, regulatory artefacts)
  are not mapped to a single work package.

Per-project natural keys are enforced via `(project_id, <natural_key>)`
uniqueness constraints so references remain human-addressable.

Meridian Airport PMO suite
(c) GV Softwares. Developed by Gaurav Vatsa. All rights reserved.
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0007_orat"
down_revision: Union[str, None] = "0006_accountability"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _enum(name: str, *values: str) -> sa.Enum:
    return sa.Enum(*values, name=name, native_enum=False)


def upgrade() -> None:
    # ---- orat_workstreams ----
    op.create_table(
        "orat_workstreams",
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
        sa.Column("owner", sa.String(255), nullable=False),
        sa.Column(
            "progress_pct", sa.Integer, nullable=False, server_default="0"
        ),
        sa.Column(
            "status",
            _enum(
                "orat_workstream_status",
                "Not Started",
                "In Progress",
                "At Risk",
                "Ready",
            ),
            nullable=False,
        ),
        sa.Column("due_month", sa.Integer, nullable=False),
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
            "project_id", "name", name="uq_orat_workstreams_project_name"
        ),
    )

    # ---- orat_trials ----
    op.create_table(
        "orat_trials",
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
            "workstream_id",
            sa.String(36),
            sa.ForeignKey("orat_workstreams.id"),
            nullable=True,
            index=True,
        ),
        sa.Column("ref", sa.String(100), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("month", sa.Integer, nullable=False),
        sa.Column(
            "participants", sa.Integer, nullable=False, server_default="0"
        ),
        sa.Column(
            "status",
            _enum(
                "trial_status",
                "Planned",
                "Prepared",
                "Executed",
                "Passed",
                "Failed",
            ),
            nullable=False,
        ),
        sa.Column("observations", sa.Text, nullable=False),
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
            "project_id", "ref", name="uq_orat_trials_project_ref"
        ),
    )

    # ---- training_groups ----
    op.create_table(
        "training_groups",
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
        sa.Column("function_name", sa.String(255), nullable=False),
        sa.Column(
            "target_headcount", sa.Integer, nullable=False, server_default="0"
        ),
        sa.Column(
            "trained_headcount", sa.Integer, nullable=False, server_default="0"
        ),
        sa.Column(
            "status",
            _enum(
                "training_status",
                "Not Started",
                "Scheduled",
                "In Delivery",
                "Complete",
            ),
            nullable=False,
        ),
        sa.Column("owner", sa.String(255), nullable=False),
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
            "project_id",
            "function_name",
            name="uq_training_groups_project_function",
        ),
    )

    # ---- handover_items ----
    op.create_table(
        "handover_items",
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
            "package_id",
            sa.String(36),
            sa.ForeignKey("work_packages.id"),
            nullable=True,
            index=True,
        ),
        sa.Column("ref", sa.String(100), nullable=False),
        sa.Column("asset_group", sa.String(255), nullable=False),
        sa.Column(
            "status",
            _enum(
                "handover_status",
                "Pending",
                "In Verification",
                "Accepted",
                "Blocked",
            ),
            nullable=False,
        ),
        sa.Column(
            "evidence_pct", sa.Integer, nullable=False, server_default="0"
        ),
        sa.Column("owner", sa.String(255), nullable=False),
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
            "project_id", "ref", name="uq_handover_items_project_ref"
        ),
    )


def downgrade() -> None:
    for table in [
        "handover_items",
        "training_groups",
        "orat_trials",
        "orat_workstreams",
    ]:
        op.drop_table(table)
