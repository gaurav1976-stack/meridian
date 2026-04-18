"""Commercial / Cost & Change Control — Pydantic schemas.

Meridian Airport PMO suite
(c) GV Softwares. Developed by Gaurav Vatsa. All rights reserved.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from app.models.enums import (
    ChangeStatus,
    ChangeType,
    EntitlementStrength,
    NoticeKind,
    NoticeStatus,
)
from app.schemas.common import TimestampedOrm


# ---------------------------------------------------------------------------
# Package Cost Control
# ---------------------------------------------------------------------------


class PackageCostCreate(BaseModel):
    package_id: str
    budget_minor: int = Field(ge=0)
    committed_minor: int = Field(ge=0, default=0)
    forecast_minor: int = Field(ge=0, default=0)
    actual_minor: int = Field(ge=0, default=0)
    percent_complete: int = Field(ge=0, le=100, default=0)


class PackageCostUpdate(BaseModel):
    budget_minor: Optional[int] = Field(default=None, ge=0)
    committed_minor: Optional[int] = Field(default=None, ge=0)
    forecast_minor: Optional[int] = Field(default=None, ge=0)
    actual_minor: Optional[int] = Field(default=None, ge=0)
    percent_complete: Optional[int] = Field(default=None, ge=0, le=100)


class PackageCostRead(TimestampedOrm):
    id: str
    project_id: str
    tenant_id: str
    package_id: str
    budget_minor: int
    committed_minor: int
    forecast_minor: int
    actual_minor: int
    percent_complete: int


# ---------------------------------------------------------------------------
# Commercial Change
# ---------------------------------------------------------------------------


class ChangeCreate(BaseModel):
    package_id: Optional[str] = None
    ref: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=255)
    change_type: ChangeType
    status: ChangeStatus = ChangeStatus.identified
    cost_impact_minor: int = Field(ge=0, default=0)
    time_impact_weeks: int = Field(ge=0, default=0)
    entitlement: EntitlementStrength
    owner: str = Field(min_length=1, max_length=255)
    cause: str = Field(min_length=1)


class ChangeUpdate(BaseModel):
    package_id: Optional[str] = None
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    change_type: Optional[ChangeType] = None
    status: Optional[ChangeStatus] = None
    cost_impact_minor: Optional[int] = Field(default=None, ge=0)
    time_impact_weeks: Optional[int] = Field(default=None, ge=0)
    entitlement: Optional[EntitlementStrength] = None
    owner: Optional[str] = Field(default=None, min_length=1, max_length=255)
    cause: Optional[str] = Field(default=None, min_length=1)


class ChangeRead(TimestampedOrm):
    id: str
    project_id: str
    tenant_id: str
    package_id: Optional[str]
    ref: str
    title: str
    change_type: ChangeType
    status: ChangeStatus
    cost_impact_minor: int
    time_impact_weeks: int
    entitlement: EntitlementStrength
    owner: str
    cause: str


# ---------------------------------------------------------------------------
# Commercial Notice
# ---------------------------------------------------------------------------


class NoticeCreate(BaseModel):
    package_id: Optional[str] = None
    ref: str = Field(min_length=1, max_length=100)
    contract_ref: str = Field(min_length=1, max_length=100)
    kind: NoticeKind
    due_days: int = Field(ge=0)
    status: NoticeStatus = NoticeStatus.open
    owner: str = Field(min_length=1, max_length=255)


class NoticeUpdate(BaseModel):
    package_id: Optional[str] = None
    contract_ref: Optional[str] = Field(default=None, min_length=1, max_length=100)
    kind: Optional[NoticeKind] = None
    due_days: Optional[int] = Field(default=None, ge=0)
    status: Optional[NoticeStatus] = None
    owner: Optional[str] = Field(default=None, min_length=1, max_length=255)


class NoticeRead(TimestampedOrm):
    id: str
    project_id: str
    tenant_id: str
    package_id: Optional[str]
    ref: str
    contract_ref: str
    kind: NoticeKind
    due_days: int
    status: NoticeStatus
    owner: str


# ---------------------------------------------------------------------------
# Rollups
# ---------------------------------------------------------------------------


class CommercialSummary(BaseModel):
    project_id: str
    budget_minor: int
    committed_minor: int
    forecast_minor: int
    actual_minor: int
    forecast_variance_minor: int
    change_exposure_minor: int
    notice_count: int
    overdue_notice_count: int
    strong_entitlement_count: int


class EvmSummary(BaseModel):
    """Earned Value Management rollup across all package cost controls.

    BAC (Budget at Completion), EV (Earned Value), AC (Actual Cost),
    PV (Planned Value), CPI (Cost Performance Index), SPI (Schedule
    Performance Index). See ANSI/EIA-748.
    """

    project_id: str
    bac_minor: int
    pv_minor: int
    ev_minor: int
    ac_minor: int
    cpi: float
    spi: float
    cv_minor: int
    sv_minor: int
    average_percent_complete: int


class PackageCommercialExposure(BaseModel):
    package_id: str
    package_code: str
    package_name: str
    budget_minor: int
    forecast_minor: int
    actual_minor: int
    change_exposure_minor: int
    notice_count: int
    overdue_notice_count: int
