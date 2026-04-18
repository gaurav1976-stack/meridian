"""Stage Gate Governance — Pydantic schemas.

Meridian Airport PMO suite
(c) GV Softwares. Developed by Gaurav Vatsa. All rights reserved.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from app.models.enums import (
    ApprovalStatus,
    DecisionOutcome,
    EvidenceCategory,
    EvidenceStatus,
    GateStatus,
)
from app.schemas.common import TimestampedOrm


# ---------------------------------------------------------------------------
# Gate Definition
# ---------------------------------------------------------------------------


class GateDefinitionCreate(BaseModel):
    code: str = Field(min_length=1, max_length=20)
    name: str = Field(min_length=1, max_length=255)
    purpose: str = Field(min_length=1)
    target_month: int = Field(ge=1, le=240)
    status: GateStatus = GateStatus.upcoming
    package_ids: list[str] = Field(default_factory=list)


class GateDefinitionUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    purpose: Optional[str] = Field(default=None, min_length=1)
    target_month: Optional[int] = Field(default=None, ge=1, le=240)
    status: Optional[GateStatus] = None


class GateDefinitionRead(TimestampedOrm):
    id: str
    project_id: str
    tenant_id: str
    code: str
    name: str
    purpose: str
    target_month: int
    status: GateStatus


# ---------------------------------------------------------------------------
# Evidence
# ---------------------------------------------------------------------------


class GateEvidenceCreate(BaseModel):
    gate_definition_id: str
    package_id: Optional[str] = None
    title: str = Field(min_length=1, max_length=255)
    category: EvidenceCategory
    required: bool = True
    status: EvidenceStatus = EvidenceStatus.draft
    owner: str = Field(min_length=1, max_length=255)


class GateEvidenceUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    category: Optional[EvidenceCategory] = None
    required: Optional[bool] = None
    status: Optional[EvidenceStatus] = None
    owner: Optional[str] = Field(default=None, min_length=1, max_length=255)


class GateEvidenceRead(TimestampedOrm):
    id: str
    project_id: str
    tenant_id: str
    gate_definition_id: str
    package_id: Optional[str]
    title: str
    category: EvidenceCategory
    required: bool
    status: EvidenceStatus
    owner: str


# ---------------------------------------------------------------------------
# Approval
# ---------------------------------------------------------------------------


class GateApprovalCreate(BaseModel):
    gate_definition_id: str
    approver: str = Field(min_length=1, max_length=255)
    role: str = Field(min_length=1, max_length=255)
    status: ApprovalStatus = ApprovalStatus.pending
    response_date: Optional[str] = None


class GateApprovalUpdate(BaseModel):
    approver: Optional[str] = Field(default=None, min_length=1, max_length=255)
    role: Optional[str] = Field(default=None, min_length=1, max_length=255)
    status: Optional[ApprovalStatus] = None
    response_date: Optional[str] = None


class GateApprovalRead(TimestampedOrm):
    id: str
    project_id: str
    tenant_id: str
    gate_definition_id: str
    approver: str
    role: str
    status: ApprovalStatus
    response_date: Optional[str]


# ---------------------------------------------------------------------------
# Decision
# ---------------------------------------------------------------------------


class GateDecisionCreate(BaseModel):
    gate_definition_id: str
    meeting_ref: str = Field(min_length=1, max_length=100)
    decision_date: str = Field(min_length=1, max_length=25)
    outcome: DecisionOutcome
    summary: str = Field(min_length=1)


class GateDecisionRead(TimestampedOrm):
    id: str
    project_id: str
    tenant_id: str
    gate_definition_id: str
    meeting_ref: str
    decision_date: str
    outcome: DecisionOutcome
    summary: str


# ---------------------------------------------------------------------------
# Readiness / Summary rollups
# ---------------------------------------------------------------------------


class GateReadinessSummary(BaseModel):
    gate_id: str
    gate_code: str
    gate_name: str
    status: GateStatus
    target_month: int
    readiness_score: int  # 0-100
    approval_progress: int  # 0-100
    blocker_count: int
    required_evidence_count: int
    accepted_evidence_count: int
    submitted_evidence_count: int
    approval_count: int
    decision_count: int
    linked_package_count: int
    latest_decision: Optional[str] = None


class GovernanceSummary(BaseModel):
    project_id: str
    gate_count: int
    active_gates: int
    blocked_gates: int
    evidence_count: int
    approval_count: int
    decision_count: int
    average_readiness_score: int
