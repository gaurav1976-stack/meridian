"""Schedule domain schemas."""
from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field

from app.models.enums import (
    ActivityStatus,
    DependencyType,
    ScheduleFileCategory,
    ScheduleFileStatus,
    ScheduleScenario,
)
from app.schemas.common import TimestampedOrm


# ----- ScheduleFile -----


class ScheduleFileCreate(BaseModel):
    package_id: Optional[str] = None
    category: ScheduleFileCategory
    status: ScheduleFileStatus = ScheduleFileStatus.draft
    revision: str = "R0"
    title: str = Field(min_length=1, max_length=255)
    issued_date: Optional[date] = None
    notes: Optional[str] = None
    storage_key: Optional[str] = None


class ScheduleFileRead(TimestampedOrm):
    id: str
    project_id: str
    tenant_id: str
    package_id: Optional[str]
    category: ScheduleFileCategory
    status: ScheduleFileStatus
    revision: str
    title: str
    issued_date: Optional[date]
    notes: Optional[str]
    storage_key: Optional[str]


# ----- Activity -----


class ScheduleActivityCreate(BaseModel):
    schedule_file_id: Optional[str] = None
    package_id: Optional[str] = None
    activity_id_external: str
    name: str
    status: ActivityStatus = ActivityStatus.not_started
    scenario: ScheduleScenario = ScheduleScenario.baseline
    planned_start: Optional[date] = None
    planned_finish: Optional[date] = None
    actual_start: Optional[date] = None
    actual_finish: Optional[date] = None
    duration_days: Optional[int] = None
    total_float_days: Optional[int] = None
    percent_complete: int = 0
    is_critical: Optional[bool] = None
    notes: Optional[str] = None


class ScheduleActivityUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[ActivityStatus] = None
    scenario: Optional[ScheduleScenario] = None
    planned_start: Optional[date] = None
    planned_finish: Optional[date] = None
    actual_start: Optional[date] = None
    actual_finish: Optional[date] = None
    duration_days: Optional[int] = None
    total_float_days: Optional[int] = None
    percent_complete: Optional[int] = None
    is_critical: Optional[bool] = None
    notes: Optional[str] = None


class ScheduleActivityRead(TimestampedOrm):
    id: str
    project_id: str
    tenant_id: str
    schedule_file_id: Optional[str]
    package_id: Optional[str]
    activity_id_external: str
    name: str
    status: ActivityStatus
    scenario: ScheduleScenario
    planned_start: Optional[date]
    planned_finish: Optional[date]
    actual_start: Optional[date]
    actual_finish: Optional[date]
    duration_days: Optional[int]
    total_float_days: Optional[int]
    percent_complete: int
    is_critical: Optional[bool]
    notes: Optional[str]


# ----- Dependency -----


class ActivityDependencyCreate(BaseModel):
    predecessor_id: str
    successor_id: str
    dependency_type: DependencyType = DependencyType.fs
    lag_days: int = 0


class ActivityDependencyRead(TimestampedOrm):
    id: str
    project_id: str
    tenant_id: str
    predecessor_id: str
    successor_id: str
    dependency_type: DependencyType
    lag_days: int


# ----- Health -----


class ScheduleHealth(BaseModel):
    total_activities: int
    completed: int
    in_progress: int
    not_started: int
    on_hold: int
    critical_activities: int
    low_float_activities: int  # total_float_days < 20
    percent_complete_avg: float
