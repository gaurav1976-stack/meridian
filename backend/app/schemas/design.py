"""Design Management — Pydantic schemas.

Meridian Airport PMO suite
(c) GV Softwares. Developed by Gaurav Vatsa. All rights reserved.
"""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.enums import (
    DeliverableStatus,
    DeliverableType,
    DesignPackageStatus,
    InterfaceStatus,
    ModelShareStatus,
    RibaStage,
)
from app.schemas.common import TimestampedOrm


# ---------------------------------------------------------------------------
# Design Package
# ---------------------------------------------------------------------------


class DesignPackageCreate(BaseModel):
    package_id: Optional[str] = None
    code: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=255)
    lead_discipline: str = Field(min_length=1, max_length=100)
    stage: RibaStage
    maturity_pct: int = Field(ge=0, le=100, default=0)
    status: DesignPackageStatus = DesignPackageStatus.draft
    freeze_planned_month: int = Field(ge=1, le=240)
    freeze_current_month: int = Field(ge=1, le=240)


class DesignPackageUpdate(BaseModel):
    package_id: Optional[str] = None
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    lead_discipline: Optional[str] = Field(default=None, min_length=1, max_length=100)
    stage: Optional[RibaStage] = None
    maturity_pct: Optional[int] = Field(default=None, ge=0, le=100)
    status: Optional[DesignPackageStatus] = None
    freeze_planned_month: Optional[int] = Field(default=None, ge=1, le=240)
    freeze_current_month: Optional[int] = Field(default=None, ge=1, le=240)


class DesignPackageRead(TimestampedOrm):
    id: str
    project_id: str
    tenant_id: str
    package_id: Optional[str]
    code: str
    name: str
    lead_discipline: str
    stage: RibaStage
    maturity_pct: int
    status: DesignPackageStatus
    freeze_planned_month: int
    freeze_current_month: int


# ---------------------------------------------------------------------------
# Deliverable
# ---------------------------------------------------------------------------


class DeliverableCreate(BaseModel):
    design_package_id: Optional[str] = None
    package_id: Optional[str] = None
    ref: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=255)
    discipline: str = Field(min_length=1, max_length=100)
    deliverable_type: DeliverableType
    stage: RibaStage
    due_month: int = Field(ge=1, le=240)
    status: DeliverableStatus = DeliverableStatus.wip
    owner: str = Field(min_length=1, max_length=255)


class DeliverableUpdate(BaseModel):
    design_package_id: Optional[str] = None
    package_id: Optional[str] = None
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    discipline: Optional[str] = Field(default=None, min_length=1, max_length=100)
    deliverable_type: Optional[DeliverableType] = None
    stage: Optional[RibaStage] = None
    due_month: Optional[int] = Field(default=None, ge=1, le=240)
    status: Optional[DeliverableStatus] = None
    owner: Optional[str] = Field(default=None, min_length=1, max_length=255)


class DeliverableRead(TimestampedOrm):
    id: str
    project_id: str
    tenant_id: str
    design_package_id: Optional[str]
    package_id: Optional[str]
    ref: str
    title: str
    discipline: str
    deliverable_type: DeliverableType
    stage: RibaStage
    due_month: int
    status: DeliverableStatus
    owner: str


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------


class InterfaceCreate(BaseModel):
    ref: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=255)
    package_a_id: str
    package_b_id: str
    owner: str = Field(min_length=1, max_length=255)
    severity: int = Field(ge=1, le=5)
    status: InterfaceStatus = InterfaceStatus.open
    due_month: int = Field(ge=1, le=240)


class InterfaceUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    package_a_id: Optional[str] = None
    package_b_id: Optional[str] = None
    owner: Optional[str] = Field(default=None, min_length=1, max_length=255)
    severity: Optional[int] = Field(default=None, ge=1, le=5)
    status: Optional[InterfaceStatus] = None
    due_month: Optional[int] = Field(default=None, ge=1, le=240)


class InterfaceRead(TimestampedOrm):
    id: str
    project_id: str
    tenant_id: str
    ref: str
    title: str
    package_a_id: str
    package_b_id: str
    owner: str
    severity: int
    status: InterfaceStatus
    due_month: int


# ---------------------------------------------------------------------------
# BIM Coordination
# ---------------------------------------------------------------------------


class BimItemCreate(BaseModel):
    workstream: str = Field(min_length=1, max_length=100)
    clash_open: int = Field(ge=0, default=0)
    clash_critical: int = Field(ge=0, default=0)
    federation_ready: bool = False
    model_share_status: ModelShareStatus = ModelShareStatus.wip


class BimItemUpdate(BaseModel):
    workstream: Optional[str] = Field(default=None, min_length=1, max_length=100)
    clash_open: Optional[int] = Field(default=None, ge=0)
    clash_critical: Optional[int] = Field(default=None, ge=0)
    federation_ready: Optional[bool] = None
    model_share_status: Optional[ModelShareStatus] = None


class BimItemRead(TimestampedOrm):
    id: str
    project_id: str
    tenant_id: str
    workstream: str
    clash_open: int
    clash_critical: int
    federation_ready: bool
    model_share_status: ModelShareStatus


# ---------------------------------------------------------------------------
# Rollups
# ---------------------------------------------------------------------------


class DesignSummary(BaseModel):
    """Project-wide design telemetry rollup."""

    project_id: str
    design_package_count: int
    deliverable_count: int
    interface_count: int
    bim_item_count: int
    average_maturity_pct: int
    overdue_deliverable_count: int
    frozen_package_count: int
    escalated_interface_count: int
    critical_clash_count: int
    average_freeze_variance_months: int


class FreezeControlEntry(BaseModel):
    """One row of the freeze-control surface — positive variance = slip."""

    design_package_id: str
    code: str
    name: str
    status: DesignPackageStatus
    stage: RibaStage
    maturity_pct: int
    freeze_planned_month: int
    freeze_current_month: int
    variance_months: int


class FreezeControlReport(BaseModel):
    project_id: str
    entries: List[FreezeControlEntry]
