"""ORAT Readiness & Handover — Pydantic schemas.

Meridian Airport PMO suite
(c) GV Softwares. Developed by Gaurav Vatsa. All rights reserved.
Proprietary — unauthorised copying, distribution, modification or use prohibited.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from app.models.enums import (
    HandoverStatus,
    OratWorkstreamStatus,
    TrainingStatus,
    TrialStatus,
)
from app.schemas.common import TimestampedOrm


# ---------------------------------------------------------------------------
# ORAT Workstream
# ---------------------------------------------------------------------------


class OratWorkstreamCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    owner: str = Field(min_length=1, max_length=255)
    progress_pct: int = Field(ge=0, le=100, default=0)
    status: OratWorkstreamStatus = OratWorkstreamStatus.not_started
    due_month: int = Field(ge=1, le=240)


class OratWorkstreamUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    owner: Optional[str] = Field(default=None, min_length=1, max_length=255)
    progress_pct: Optional[int] = Field(default=None, ge=0, le=100)
    status: Optional[OratWorkstreamStatus] = None
    due_month: Optional[int] = Field(default=None, ge=1, le=240)


class OratWorkstreamRead(TimestampedOrm):
    id: str
    project_id: str
    tenant_id: str
    name: str
    owner: str
    progress_pct: int
    status: OratWorkstreamStatus
    due_month: int


# ---------------------------------------------------------------------------
# ORAT Trial
# ---------------------------------------------------------------------------


class OratTrialCreate(BaseModel):
    workstream_id: Optional[str] = None
    ref: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=255)
    month: int = Field(ge=1, le=240)
    participants: int = Field(ge=0, default=0)
    status: TrialStatus = TrialStatus.planned
    observations: str = Field(min_length=1)


class OratTrialUpdate(BaseModel):
    workstream_id: Optional[str] = None
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    month: Optional[int] = Field(default=None, ge=1, le=240)
    participants: Optional[int] = Field(default=None, ge=0)
    status: Optional[TrialStatus] = None
    observations: Optional[str] = Field(default=None, min_length=1)


class OratTrialRead(TimestampedOrm):
    id: str
    project_id: str
    tenant_id: str
    workstream_id: Optional[str]
    ref: str
    title: str
    month: int
    participants: int
    status: TrialStatus
    observations: str


# ---------------------------------------------------------------------------
# Training Group
# ---------------------------------------------------------------------------


class TrainingGroupCreate(BaseModel):
    function_name: str = Field(min_length=1, max_length=255)
    target_headcount: int = Field(ge=0, default=0)
    trained_headcount: int = Field(ge=0, default=0)
    status: TrainingStatus = TrainingStatus.not_started
    owner: str = Field(min_length=1, max_length=255)


class TrainingGroupUpdate(BaseModel):
    function_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    target_headcount: Optional[int] = Field(default=None, ge=0)
    trained_headcount: Optional[int] = Field(default=None, ge=0)
    status: Optional[TrainingStatus] = None
    owner: Optional[str] = Field(default=None, min_length=1, max_length=255)


class TrainingGroupRead(TimestampedOrm):
    id: str
    project_id: str
    tenant_id: str
    function_name: str
    target_headcount: int
    trained_headcount: int
    status: TrainingStatus
    owner: str


# ---------------------------------------------------------------------------
# Handover Item
# ---------------------------------------------------------------------------


class HandoverItemCreate(BaseModel):
    package_id: Optional[str] = None
    ref: str = Field(min_length=1, max_length=100)
    asset_group: str = Field(min_length=1, max_length=255)
    status: HandoverStatus = HandoverStatus.pending
    evidence_pct: int = Field(ge=0, le=100, default=0)
    owner: str = Field(min_length=1, max_length=255)


class HandoverItemUpdate(BaseModel):
    package_id: Optional[str] = None
    asset_group: Optional[str] = Field(default=None, min_length=1, max_length=255)
    status: Optional[HandoverStatus] = None
    evidence_pct: Optional[int] = Field(default=None, ge=0, le=100)
    owner: Optional[str] = Field(default=None, min_length=1, max_length=255)


class HandoverItemRead(TimestampedOrm):
    id: str
    project_id: str
    tenant_id: str
    package_id: Optional[str]
    ref: str
    asset_group: str
    status: HandoverStatus
    evidence_pct: int
    owner: str


# ---------------------------------------------------------------------------
# Rollups
# ---------------------------------------------------------------------------


class OratReadinessSummary(BaseModel):
    """Project-wide ORAT readiness telemetry rollup.

    Mirrors the legacy Track A.10 `/orat-readiness-summary` payload but typed
    end-to-end. `training_completion_pct` is computed as
    ``sum(trained) / sum(target) * 100`` across every group, matching the
    aggregate formula used on the prototype dashboard.
    """

    project_id: str
    workstream_count: int
    trial_count: int
    training_group_count: int
    handover_item_count: int
    average_workstream_progress_pct: int
    at_risk_workstream_count: int
    passed_trial_count: int
    training_completion_pct: int
    accepted_handover_count: int
    blocked_handover_count: int


class PackageHandoverPressure(BaseModel):
    """Per-package handover load used on the package handover heat-map.

    `blocked_count` counts items in `Blocked` state — these are the ones that
    will defer go-live. `pending_count` includes both `Pending` and
    `In Verification` because both still need work before acceptance.
    """

    package_id: str
    package_code: str
    package_name: str
    handover_count: int
    accepted_count: int
    blocked_count: int
    pending_count: int
    average_evidence_pct: int
