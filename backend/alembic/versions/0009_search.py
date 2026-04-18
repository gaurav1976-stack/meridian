"""search — search index records, saved searches, connector references.

Revision ID: 0009_search
Revises: 0008_reporting
Create Date: 2026-04-18

Adds the Enterprise Search & Retrieval domain (Module 12). Non-native enums
keep SQLite (test) and Postgres (prod) on the same DDL path.

Nullable FKs:
- ``connector_references.index_record_id`` — a connector pointer can exist
  in ``Pending`` state before the ingestion pipeline has produced the
  matching search row.

Per-column unique enum names are required for SQLite compatibility — the
``SearchSource`` enum values are identical between ``search_index_records``
and ``connector_references``, but the enum *type name* in the SQLAlchemy
``Enum`` construct must differ per column to avoid collision.

Per-project natural keys are enforced via ``(project_id, <natural_key>)``
uniqueness constraints:
- ``search_index_records`` — ``(project_id, entity_type, entity_ref)``
- ``saved_searches`` — ``(project_id, name)``
- ``connector_references`` — ``(project_id, external_ref)``

Meridian Airport PMO suite
(c) GV Softwares. Developed by Gaurav Vatsa. All rights reserved.
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0009_search"
down_revision: Union[str, None] = "0008_reporting"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _enum(name: str, *values: str) -> sa.Enum:
    return sa.Enum(*values, name=name, native_enum=False)


def upgrade() -> None:
    # ---- search_index_records ----
    op.create_table(
        "search_index_records",
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
            "entity_type",
            _enum(
                "search_entity_type",
                "Project",
                "Schedule",
                "Gate",
                "Risk",
                "Commercial",
                "Design",
                "Document",
                "Action",
                "ORAT",
                "Repository",
                "Report",
            ),
            nullable=False,
        ),
        sa.Column("entity_ref", sa.String(255), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("summary", sa.Text, nullable=False),
        sa.Column(
            "source",
            _enum(
                "search_index_source",
                "Meridian",
                "BIM360",
                "SharePoint",
                "Teams",
            ),
            nullable=False,
        ),
        sa.Column(
            "group_name",
            _enum(
                "search_group",
                "Core",
                "Delivery",
                "Governance",
                "Commercial",
                "Technical",
                "Operations",
                "Outputs",
            ),
            nullable=False,
        ),
        sa.Column("package_code", sa.String(50), nullable=True),
        sa.Column("status_text", sa.String(100), nullable=True),
        sa.Column("tags_csv", sa.Text, nullable=True),
        sa.Column(
            "permission_scope",
            sa.String(255),
            nullable=False,
            server_default="tenant:all",
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
            "project_id",
            "entity_type",
            "entity_ref",
            name="uq_search_index_records_entity",
        ),
    )

    # ---- saved_searches ----
    op.create_table(
        "saved_searches",
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
        sa.Column("user_email", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("query_text", sa.Text, nullable=False),
        sa.Column(
            "scope",
            _enum(
                "saved_search_scope",
                "All",
                "Module Specific",
                "Repository Only",
            ),
            nullable=False,
            server_default="All",
        ),
        sa.Column("type_filter", sa.String(255), nullable=True),
        sa.Column("source_filter", sa.String(255), nullable=True),
        sa.Column("package_filter", sa.String(255), nullable=True),
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
            "project_id", "name", name="uq_saved_searches_project_name"
        ),
    )

    # ---- connector_references ----
    op.create_table(
        "connector_references",
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
            "source",
            _enum(
                "connector_reference_source",
                "Meridian",
                "BIM360",
                "SharePoint",
                "Teams",
            ),
            nullable=False,
        ),
        sa.Column("external_ref", sa.String(255), nullable=False),
        sa.Column("path", sa.Text, nullable=False),
        sa.Column(
            "sync_status",
            _enum(
                "connector_sync_status",
                "Indexed",
                "Pending",
                "Stale",
                "Failed",
            ),
            nullable=False,
            server_default="Pending",
        ),
        sa.Column(
            "index_record_id",
            sa.String(36),
            sa.ForeignKey("search_index_records.id"),
            nullable=True,
            index=True,
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
            "project_id",
            "external_ref",
            name="uq_connector_references_external_ref",
        ),
    )


def downgrade() -> None:
    # Drop in dependency-safe order:
    # connector_references references search_index_records; saved_searches stands alone.
    for table in ["connector_references", "saved_searches", "search_index_records"]:
        op.drop_table(table)
