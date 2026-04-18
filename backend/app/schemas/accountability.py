"""Meetings, Actions & Compliance — Pydantic schemas.

Meridian Airport PMO suite
(c) GV Softwares. Developed by Gaurav Vatsa. All rights reserved.
Proprietary — unauthorised copying, distribution, modification or use prohibited.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from app.models.enums import (
    ActionPriority,
    ActionSourceType,
    ActionStatus,
    ComplianceDomain,
    ComplianceStatus,
    LinkedModule,
    MeetingType,
)
from app.schemas.common import TimestampedOrm


# ---------------------------------------------------------------------------
# Meeting Record
# ---------------------------------------------------------------------------


class MeetingRecordCreate(BaseModel):
    ref: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=255)
    meeting_type: MeetingType
    month: int = Field(ge=1, le=240)
    chair: str = Field(min_length=1, max_length=255)
    attendee_count: int = Field(ge=0, default=0)
    linked_module: LinkedModule


class MeetingRecordUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    meeting_type: Optional[MeetingType] = None
    month: Optional[int] = Field(default=None, ge=1, le=240)
    chair: Optional[str] = Field(default=None, min_length=1, max_length=255)
    attendee_count: Optional[int] = Field(default=None, ge=0)
    linked_module: Optional[LinkedModule] = None


class MeetingRecordRead(TimestampedOrm):
    id: str
    project_id: str
    tenant_id: str
    ref: str
    title: str
    meeting_type: MeetingType
    month: int
    chair: str
    attendee_count: int
    linked_module: LinkedModule


# ---------------------------------------------------------------------------
# Action Item
# ---------------------------------------------------------------------------


class ActionItemCreate(BaseModel):
    package_id: Optional[str] = None
    ref: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=255)
    owner: str = Field(min_length=1, max_length=255)
    source_type: ActionSourceType
    source_ref: str = Field(min_length=1, max_length=255)
    priority: ActionPriority
    due_month: int = Field(ge=1, le=240)
    status: ActionStatus = ActionStatus.open
    closure_evidence_pct: int = Field(ge=0, le=100, default=0)


class ActionItemUpdate(BaseModel):
    package_id: Optional[str] = None
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    owner: Optional[str] = Field(default=None, min_length=1, max_length=255)
    source_type: Optional[ActionSourceType] = None
    source_ref: Optional[str] = Field(default=None, min_length=1, max_length=255)
    priority: Optional[ActionPriority] = None
    due_month: Optional[int] = Field(default=None, ge=1, le=240)
    status: Optional[ActionStatus] = None
    closure_evidence_pct: Optional[int] = Field(default=None, ge=0, le=100)


class ActionItemRead(TimestampedOrm):
    id: str
    project_id: str
    tenant_id: str
    package_id: Optional[str]
    ref: str
    title: str
    owner: str
    source_type: ActionSourceType
    source_ref: str
    priority: ActionPriority
    due_month: int
    status: ActionStatus
    closure_evidence_pct: int


# ---------------------------------------------------------------------------
# Compliance Item
# ---------------------------------------------------------------------------


class ComplianceItemCreate(BaseModel):
    package_id: Optional[str] = None
    ref: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=255)
    domain: ComplianceDomain
    owner: str = Field(min_length=1, max_length=255)
    due_month: int = Field(ge=1, le=240)
    status: ComplianceStatus = ComplianceStatus.open
    evidence_pct: int = Field(ge=0, le=100, default=0)


class ComplianceItemUpdate(BaseModel):
    package_id: Optional[str] = None
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    domain: Optional[ComplianceDomain] = None
    owner: Optional[str] = Field(default=None, min_length=1, max_length=255)
    due_month: Optional[int] = Field(default=None, ge=1, le=240)
    status: Optional[ComplianceStatus] = None
    evidence_pct: Optional[int] = Field(default=None, ge=0, le=100)


class ComplianceItemRead(TimestampedOrm):
    id: str
    project_id: str
    tenant_id: str
    package_id: Optional[str]
    ref: str
    title: str
    domain: ComplianceDomain
    owner: str
    due_month: int
    status: ComplianceStatus
    evidence_pct: int


# ---------------------------------------------------------------------------
# Rollups
# ---------------------------------------------------------------------------


class AccountabilitySummary(BaseModel):
    """Project-wide accountability telemetry rollup.

    `open_action_count` counts Open + In Progress + Awaiting Review.
    `non_compliant_count` counts Non-Compliant + Overdue (both are adverse
    compliance states the board needs to see).
    """

    project_id: str
    meeting_count: int
    action_count: int
    compliance_count: int
    open_action_count: int
    overdue_action_count: int
    average_closure_evidence_pct: int
    compliant_count: int
    non_compliant_count: int


class PackageActionPressure(BaseModel):
    """Per-package action load used on the package heat-map."""

    package_id: str
    package_code: str
    package_name: str
    action_count: int
    overdue_count: int
    critical_count: int
    average_closure_evidence_pct: int
