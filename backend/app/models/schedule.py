"""Schedule tables: ScheduleFile, ScheduleActivity, ActivityDependency, ScheduleSnapshot.

Distilled from `meridian_track_a_3_schedule_persistence.py`.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import Date, DateTime, Enum as SAEnum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TenantScopedMixin, TimestampMixin
from app.models.enums import (
    ActivityStatus,
    DependencyType,
    ScheduleFileCategory,
    ScheduleFileStatus,
    ScheduleScenario,
)


class ScheduleFile(Base, TimestampMixin, TenantScopedMixin):
    __tablename__ = "schedule_files"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), index=True, nullable=False)
    package_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("work_packages.id"), nullable=True, index=True
    )
    category: Mapped[ScheduleFileCategory] = mapped_column(SAEnum(ScheduleFileCategory), nullable=False)
    status: Mapped[ScheduleFileStatus] = mapped_column(
        SAEnum(ScheduleFileStatus), nullable=False, default=ScheduleFileStatus.draft
    )
    revision: Mapped[str] = mapped_column(String(20), nullable=False, default="R0")
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    issued_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    storage_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)


class ScheduleActivity(Base, TimestampMixin, TenantScopedMixin):
    __tablename__ = "schedule_activities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), index=True, nullable=False)
    schedule_file_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("schedule_files.id"), nullable=True, index=True
    )
    package_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("work_packages.id"), nullable=True, index=True
    )
    activity_id_external: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[ActivityStatus] = mapped_column(
        SAEnum(ActivityStatus), nullable=False, default=ActivityStatus.not_started
    )
    scenario: Mapped[ScheduleScenario] = mapped_column(
        SAEnum(ScheduleScenario), nullable=False, default=ScheduleScenario.baseline
    )
    planned_start: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    planned_finish: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    actual_start: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    actual_finish: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    duration_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_float_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    percent_complete: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_critical: Mapped[Optional[bool]] = mapped_column(nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class ActivityDependency(Base, TimestampMixin, TenantScopedMixin):
    __tablename__ = "activity_dependencies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), index=True, nullable=False)
    predecessor_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("schedule_activities.id"), nullable=False, index=True
    )
    successor_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("schedule_activities.id"), nullable=False, index=True
    )
    dependency_type: Mapped[DependencyType] = mapped_column(
        SAEnum(DependencyType), nullable=False, default=DependencyType.fs
    )
    lag_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class ScheduleSnapshot(Base, TimestampMixin, TenantScopedMixin):
    __tablename__ = "schedule_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), index=True, nullable=False)
    schedule_file_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("schedule_files.id"), nullable=True, index=True
    )
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    snapshot_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    metrics_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
