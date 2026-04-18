"""documents — controlled documents, reviews, transmittals, repository links.

Revision ID: 0005_documents
Revises: 0004_design
Create Date: 2026-04-18

Adds the Document Control domain. Non-native enums keep SQLite (test) and
Postgres (prod) on the same DDL path. Suitability is stored as free-text to
accommodate variant ISO 19650 status-code taxonomies (S0–S6 plus A/B codes for
transmittal bundles etc).

Meridian Airport PMO suite
(c) GV Softwares. Developed by Gaurav Vatsa. All rights reserved.
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0005_documents"
down_revision: Union[str, None] = "0004_design"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _enum(name: str, *values: str) -> sa.Enum:
    return sa.Enum(*values, name=name, native_enum=False)


def upgrade() -> None:
    # ---- controlled_documents ----
    op.create_table(
        "controlled_documents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id"), nullable=False, index=True),
        sa.Column("package_id", sa.String(36), sa.ForeignKey("work_packages.id"), nullable=True, index=True),
        sa.Column("number", sa.String(255), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("discipline", sa.String(100), nullable=False),
        sa.Column(
            "document_type",
            _enum(
                "document_type",
                "Drawing",
                "Report",
                "Calculation",
                "Specification",
                "Letter",
                "Transmittal",
                "Procedure",
            ),
            nullable=False,
        ),
        sa.Column("revision", sa.String(50), nullable=False),
        sa.Column("suitability", sa.String(50), nullable=False),
        sa.Column(
            "workflow_status",
            _enum(
                "document_workflow_status",
                "WIP",
                "Shared",
                "Published",
                "Accepted",
                "Archived",
                "Overdue",
            ),
            nullable=False,
        ),
        sa.Column(
            "cde_stage",
            _enum("cde_stage", "WIP", "Shared", "Published", "Archived"),
            nullable=False,
        ),
        sa.Column("owner", sa.String(255), nullable=False),
        sa.Column("due_month", sa.Integer, nullable=False),
        sa.Column("metadata_pct", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "source",
            _enum("repository_source", "Meridian", "BIM360", "SharePoint"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint(
            "project_id", "number", name="uq_controlled_documents_project_number"
        ),
    )

    # ---- document_reviews ----
    op.create_table(
        "document_reviews",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id"), nullable=False, index=True),
        sa.Column("document_id", sa.String(36), sa.ForeignKey("controlled_documents.id"), nullable=False, index=True),
        sa.Column("reviewer", sa.String(255), nullable=False),
        sa.Column("role", sa.String(255), nullable=False),
        sa.Column(
            "status",
            _enum(
                "review_status",
                "Pending",
                "In Review",
                "Approved",
                "Rejected",
            ),
            nullable=False,
        ),
        sa.Column("due_month", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ---- transmittal_records ----
    op.create_table(
        "transmittal_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id"), nullable=False, index=True),
        sa.Column("ref", sa.String(100), nullable=False),
        sa.Column("package_id", sa.String(36), sa.ForeignKey("work_packages.id"), nullable=True, index=True),
        sa.Column("recipient", sa.String(255), nullable=False),
        sa.Column("document_count", sa.Integer, nullable=False, server_default="1"),
        sa.Column("issue_month", sa.Integer, nullable=False),
        sa.Column(
            "status",
            _enum(
                "transmittal_status",
                "Draft",
                "Issued",
                "Acknowledged",
                "Returned",
            ),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint(
            "project_id", "ref", name="uq_transmittal_records_project_ref"
        ),
    )

    # ---- repository_links ----
    op.create_table(
        "repository_links",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("project_id", sa.String(36), sa.ForeignKey("projects.id"), nullable=False, index=True),
        sa.Column("document_id", sa.String(36), sa.ForeignKey("controlled_documents.id"), nullable=False, index=True),
        sa.Column(
            "repository",
            _enum("repository_source", "Meridian", "BIM360", "SharePoint"),
            nullable=False,
        ),
        sa.Column("path", sa.Text, nullable=False),
        sa.Column(
            "sync_status",
            _enum(
                "sync_status",
                "Linked",
                "Pending Sync",
                "Out of Sync",
            ),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    for table in [
        "repository_links",
        "transmittal_records",
        "document_reviews",
        "controlled_documents",
    ]:
        op.drop_table(table)
