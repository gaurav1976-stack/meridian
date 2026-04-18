"""Document Control models.

Distilled from `meridian_track_a_8_document_control_persistence.py`. Covers the
controlled document register (ISO 19650 numbering + suitability), per-document
review register, transmittal register (issue control), and repository-link
register (external CDE integration — BIM360 / SharePoint / Meridian-native).

Key standards applied:
- ISO 19650 document workflow states — WIP / Shared / Published / Archived
- CDE hierarchy for information approval
- Suitability codes (S0–S6) carried as free-text to accommodate client variants

Meridian Airport PMO suite
(c) GV Softwares. Developed by Gaurav Vatsa. All rights reserved.
Proprietary — unauthorised copying, distribution, modification or use prohibited.
"""
from __future__ import annotations

from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    Enum as SAEnum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TenantScopedMixin, TimestampMixin
from app.models.enums import (
    CdeStage,
    DocumentType,
    DocumentWorkflowStatus,
    RepositorySource,
    ReviewStatus,
    SyncStatus,
    TransmittalStatus,
)


class ControlledDocument(Base, TimestampMixin, TenantScopedMixin):
    """A single controlled document — ISO 19650 numbered, revision-tracked.

    `number` follows the ProjectCode-Discipline-Type-Zone-Sequential pattern
    from the Meridian conversion playbook. `suitability` is the ISO 19650
    status code (S0–S6, A, B etc). `metadata_pct` drives the metadata
    completeness telemetry on the programme dashboard.
    """

    __tablename__ = "controlled_documents"
    __table_args__ = (
        UniqueConstraint(
            "project_id", "number", name="uq_controlled_documents_project_number"
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id"), index=True, nullable=False
    )
    package_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("work_packages.id"), nullable=True, index=True
    )
    number: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    discipline: Mapped[str] = mapped_column(String(100), nullable=False)
    document_type: Mapped[DocumentType] = mapped_column(
        SAEnum(DocumentType), nullable=False
    )
    revision: Mapped[str] = mapped_column(String(50), nullable=False)
    suitability: Mapped[str] = mapped_column(String(50), nullable=False)
    workflow_status: Mapped[DocumentWorkflowStatus] = mapped_column(
        SAEnum(DocumentWorkflowStatus),
        nullable=False,
        default=DocumentWorkflowStatus.wip,
    )
    cde_stage: Mapped[CdeStage] = mapped_column(
        SAEnum(CdeStage), nullable=False, default=CdeStage.wip
    )
    owner: Mapped[str] = mapped_column(String(255), nullable=False)
    due_month: Mapped[int] = mapped_column(Integer, nullable=False)
    metadata_pct: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    source: Mapped[RepositorySource] = mapped_column(
        SAEnum(RepositorySource), nullable=False, default=RepositorySource.meridian
    )


class DocumentReview(Base, TimestampMixin, TenantScopedMixin):
    """Review record attached to a controlled document."""

    __tablename__ = "document_reviews"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id"), index=True, nullable=False
    )
    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("controlled_documents.id"), nullable=False, index=True
    )
    reviewer: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[ReviewStatus] = mapped_column(
        SAEnum(ReviewStatus), nullable=False, default=ReviewStatus.pending
    )
    due_month: Mapped[int] = mapped_column(Integer, nullable=False)


class TransmittalRecord(Base, TimestampMixin, TenantScopedMixin):
    """Transmittal register entry — an issue bundle to an external recipient."""

    __tablename__ = "transmittal_records"
    __table_args__ = (
        UniqueConstraint(
            "project_id", "ref", name="uq_transmittal_records_project_ref"
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id"), index=True, nullable=False
    )
    ref: Mapped[str] = mapped_column(String(100), nullable=False)
    package_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("work_packages.id"), nullable=True, index=True
    )
    recipient: Mapped[str] = mapped_column(String(255), nullable=False)
    document_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    issue_month: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[TransmittalStatus] = mapped_column(
        SAEnum(TransmittalStatus), nullable=False, default=TransmittalStatus.draft
    )


class RepositoryLink(Base, TimestampMixin, TenantScopedMixin):
    """Pointer from a Meridian document to its external CDE location."""

    __tablename__ = "repository_links"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id"), index=True, nullable=False
    )
    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("controlled_documents.id"), nullable=False, index=True
    )
    repository: Mapped[RepositorySource] = mapped_column(
        SAEnum(RepositorySource), nullable=False
    )
    path: Mapped[str] = mapped_column(Text, nullable=False)
    sync_status: Mapped[SyncStatus] = mapped_column(
        SAEnum(SyncStatus), nullable=False, default=SyncStatus.pending_sync
    )
