"""Risk + opportunity schemas."""
from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field

from app.models.enums import OpportunityStatus, RiskCategory, RiskStatus
from app.schemas.common import TimestampedOrm


# ----- Risk -----


class RiskCreate(BaseModel):
    package_id: Optional[str] = None
    code: str = Field(min_length=1, max_length=40)
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    category: RiskCategory
    status: RiskStatus = RiskStatus.identified
    likelihood: int = Field(default=3, ge=1, le=5)
    impact: int = Field(default=3, ge=1, le=5)
    mitigated_likelihood: Optional[int] = Field(default=None, ge=1, le=5)
    mitigated_impact: Optional[int] = Field(default=None, ge=1, le=5)
    owner: Optional[str] = None
    mitigation: Optional[str] = None
    target_closure_date: Optional[date] = None


class RiskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[RiskCategory] = None
    status: Optional[RiskStatus] = None
    likelihood: Optional[int] = Field(default=None, ge=1, le=5)
    impact: Optional[int] = Field(default=None, ge=1, le=5)
    mitigated_likelihood: Optional[int] = Field(default=None, ge=1, le=5)
    mitigated_impact: Optional[int] = Field(default=None, ge=1, le=5)
    owner: Optional[str] = None
    mitigation: Optional[str] = None
    target_closure_date: Optional[date] = None


class RiskRead(TimestampedOrm):
    id: str
    project_id: str
    tenant_id: str
    package_id: Optional[str]
    code: str
    title: str
    description: Optional[str]
    category: RiskCategory
    status: RiskStatus
    likelihood: int
    impact: int
    mitigated_likelihood: Optional[int]
    mitigated_impact: Optional[int]
    owner: Optional[str]
    mitigation: Optional[str]
    target_closure_date: Optional[date]
    gross_score: int
    residual_score: int


class RiskHeatmapCell(BaseModel):
    likelihood: int
    impact: int
    count: int


class RiskHeatmap(BaseModel):
    cells: list[RiskHeatmapCell]
    top_residual: list[RiskRead]


# ----- Opportunity -----


class OpportunityCreate(BaseModel):
    code: str = Field(min_length=1, max_length=40)
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    status: OpportunityStatus = OpportunityStatus.identified
    likelihood: int = Field(default=3, ge=1, le=5)
    benefit: int = Field(default=3, ge=1, le=5)
    owner: Optional[str] = None
    target_realisation_date: Optional[date] = None
    notes: Optional[str] = None


class OpportunityRead(TimestampedOrm):
    id: str
    project_id: str
    tenant_id: str
    code: str
    title: str
    description: Optional[str]
    status: OpportunityStatus
    likelihood: int
    benefit: int
    owner: Optional[str]
    target_realisation_date: Optional[date]
    notes: Optional[str]
