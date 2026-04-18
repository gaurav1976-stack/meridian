"""Project + work-package schemas."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from app.models.enums import PackageStatus, PackageType, ProjectStatus
from app.schemas.common import OrmBase, TimestampedOrm


class ProjectCreate(BaseModel):
    code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=255)
    location: Optional[str] = None
    status: ProjectStatus = ProjectStatus.planned
    stage: Optional[str] = None
    description: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    status: Optional[ProjectStatus] = None
    stage: Optional[str] = None
    description: Optional[str] = None


class ProjectRead(TimestampedOrm):
    id: str
    tenant_id: str
    code: str
    name: str
    location: Optional[str]
    status: ProjectStatus
    stage: Optional[str]
    description: Optional[str]


class WorkPackageCreate(BaseModel):
    code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=255)
    package_type: Optional[PackageType] = None
    status: PackageStatus = PackageStatus.planned
    description: Optional[str] = None


class WorkPackageUpdate(BaseModel):
    name: Optional[str] = None
    package_type: Optional[PackageType] = None
    status: Optional[PackageStatus] = None
    description: Optional[str] = None


class WorkPackageRead(TimestampedOrm):
    id: str
    project_id: str
    tenant_id: str
    code: str
    name: str
    package_type: Optional[str]
    status: Optional[str]
    description: Optional[str]


class DashboardCounts(OrmBase):
    work_packages: int
    contracts: int
    open_risks: int
    schedule_activities: int
    activities_critical: int


class ProjectDashboard(OrmBase):
    project: ProjectRead
    counts: DashboardCounts
