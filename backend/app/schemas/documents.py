"""Document Control — Pydantic schemas.

Meridian Airport PMO suite
(c) GV Softwares. Developed by Gaurav Vatsa. All rights reserved.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from app.models.enums import (
    CdeStage,
    DocumentType,
    DocumentWorkflowStatus,
    RepositorySource,
    ReviewStatus,
    SyncStatus,
    TransmittalStatus,
)
from app.schemas.common import TimestampedOrm


# ---------------------------------------------------------------------------
# Controlled Document
# ---------------------------------------------------------------------------


class ControlledDocumentCreate(BaseModel):
    package_id: Optional[str] = None
    number: str = Field(min_length=1, max_length=255)
    title: str = Field(min_length=1, max_length=255)
    discipline: str = Field(min_length=1, max_length=100)
    document_type: DocumentType
    revision: str = Field(min_length=1, max_length=50)
    suitability: str = Field(min_length=1, max_length=50)
    workflow_status: DocumentWorkflowStatus = DocumentWorkflowStatus.wip
    cde_stage: CdeStage = CdeStage.wip
    owner: str = Field(min_length=1, max_length=255)
    due_month: int = Field(ge=1, le=240)
    metadata_pct: int = Field(ge=0, le=100, default=0)
    source: RepositorySource = RepositorySource.meridian


class ControlledDocumentUpdate(BaseModel):
    package_id: Optional[str] = None
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    discipline: Optional[str] = Field(default=None, min_length=1, max_length=100)
    document_type: Optional[DocumentType] = None
    revision: Optional[str] = Field(default=None, min_length=1, max_length=50)
    suitability: Optional[str] = Field(default=None, min_length=1, max_length=50)
    workflow_status: Optional[DocumentWorkflowStatus] = None
    cde_stage: Optional[CdeStage] = None
    owner: Optional[str] = Field(default=None, min_length=1, max_length=255)
    due_month: Optional[int] = Field(default=None, ge=1, le=240)
    metadata_pct: Optional[int] = Field(default=None, ge=0, le=100)
    source: Optional[RepositorySource] = None


class ControlledDocumentRead(TimestampedOrm):
    id: str
    project_id: str
    tenant_id: str
    package_id: Optional[str]
    number: str
    title: str
    discipline: str
    document_type: DocumentType
    revision: str
    suitability: str
    workflow_status: DocumentWorkflowStatus
    cde_stage: CdeStage
    owner: str
    due_month: int
    metadata_pct: int
    source: RepositorySource


# ---------------------------------------------------------------------------
# Document Review
# ---------------------------------------------------------------------------


class DocumentReviewCreate(BaseModel):
    document_id: str
    reviewer: str = Field(min_length=1, max_length=255)
    role: str = Field(min_length=1, max_length=255)
    status: ReviewStatus = ReviewStatus.pending
    due_month: int = Field(ge=1, le=240)


class DocumentReviewUpdate(BaseModel):
    reviewer: Optional[str] = Field(default=None, min_length=1, max_length=255)
    role: Optional[str] = Field(default=None, min_length=1, max_length=255)
    status: Optional[ReviewStatus] = None
    due_month: Optional[int] = Field(default=None, ge=1, le=240)


class DocumentReviewRead(TimestampedOrm):
    id: str
    project_id: str
    tenant_id: str
    document_id: str
    reviewer: str
    role: str
    status: ReviewStatus
    due_month: int


# ---------------------------------------------------------------------------
# Transmittal
# ---------------------------------------------------------------------------


class TransmittalCreate(BaseModel):
    ref: str = Field(min_length=1, max_length=100)
    package_id: Optional[str] = None
    recipient: str = Field(min_length=1, max_length=255)
    document_count: int = Field(ge=1, default=1)
    issue_month: int = Field(ge=1, le=240)
    status: TransmittalStatus = TransmittalStatus.draft


class TransmittalUpdate(BaseModel):
    package_id: Optional[str] = None
    recipient: Optional[str] = Field(default=None, min_length=1, max_length=255)
    document_count: Optional[int] = Field(default=None, ge=1)
    issue_month: Optional[int] = Field(default=None, ge=1, le=240)
    status: Optional[TransmittalStatus] = None


class TransmittalRead(TimestampedOrm):
    id: str
    project_id: str
    tenant_id: str
    ref: str
    package_id: Optional[str]
    recipient: str
    document_count: int
    issue_month: int
    status: TransmittalStatus


# ---------------------------------------------------------------------------
# Repository Link
# ---------------------------------------------------------------------------


class RepositoryLinkCreate(BaseModel):
    document_id: str
    repository: RepositorySource
    path: str = Field(min_length=1)
    sync_status: SyncStatus = SyncStatus.pending_sync


class RepositoryLinkUpdate(BaseModel):
    repository: Optional[RepositorySource] = None
    path: Optional[str] = Field(default=None, min_length=1)
    sync_status: Optional[SyncStatus] = None


class RepositoryLinkRead(TimestampedOrm):
    id: str
    project_id: str
    tenant_id: str
    document_id: str
    repository: RepositorySource
    path: str
    sync_status: SyncStatus


# ---------------------------------------------------------------------------
# Rollup
# ---------------------------------------------------------------------------


class DocumentControlSummary(BaseModel):
    """Project-wide document-control telemetry rollup."""

    project_id: str
    document_count: int
    review_count: int
    transmittal_count: int
    repository_link_count: int
    average_metadata_pct: int
    overdue_document_count: int
    published_document_count: int
    pending_review_count: int
    sync_issue_count: int
    issued_transmittal_count: int
