"""Commercial / Cost & Change Control models.

Distilled from `meridian_track_a_6_cost_change_commercial_persistence.py`.
Covers per-package cost control (BAC/committed/forecast/actual + % complete),
commercial change items (Compensation Events, Variations, Client/Authority
changes, Claims) and contract notices (EWN, CE Notification, Claim Notice).

All monetary fields are stored in **minor units** (e.g. pence, cents) as
integers to avoid floating-point drift.

Meridian Airport PMO suite
(c) GV Softwares. Developed by Gaurav Vatsa. All rights reserved.
Proprietary — unauthorised copying, distribution, modification or use prohibited.
"""
from __future__ import annotations

from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    Enum as SAEnum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TenantScopedMixin, TimestampMixin
from app.models.enums import (
    ChangeStatus,
    ChangeType,
    EntitlementStrength,
    NoticeKind,
    NoticeStatus,
)


class PackageCostControl(Base, TimestampMixin, TenantScopedMixin):
    """Cost-control row for a single work package.

    One per (project, package). Budget / committed / forecast / actual all in
    minor currency units. `percent_complete` feeds the EVM rollup.
    """

    __tablename__ = "package_cost_controls"
    __table_args__ = (
        UniqueConstraint(
            "project_id", "package_id", name="uq_package_cost_controls_project_package"
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id"), index=True, nullable=False
    )
    package_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("work_packages.id"), nullable=False, index=True
    )
    budget_minor: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    committed_minor: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    forecast_minor: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    actual_minor: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    percent_complete: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class CommercialChangeItem(Base, TimestampMixin, TenantScopedMixin):
    """Compensation Event, Variation, Claim — one row per change."""

    __tablename__ = "commercial_change_items"
    __table_args__ = (
        UniqueConstraint(
            "project_id", "ref", name="uq_commercial_change_items_project_ref"
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id"), index=True, nullable=False
    )
    package_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("work_packages.id"), nullable=True, index=True
    )
    ref: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    change_type: Mapped[ChangeType] = mapped_column(SAEnum(ChangeType), nullable=False)
    status: Mapped[ChangeStatus] = mapped_column(
        SAEnum(ChangeStatus), nullable=False, default=ChangeStatus.identified
    )
    cost_impact_minor: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    time_impact_weeks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    entitlement: Mapped[EntitlementStrength] = mapped_column(
        SAEnum(EntitlementStrength), nullable=False
    )
    owner: Mapped[str] = mapped_column(String(255), nullable=False)
    cause: Mapped[str] = mapped_column(Text, nullable=False)


class CommercialNoticeItem(Base, TimestampMixin, TenantScopedMixin):
    """Contract notice — EWN, Notice, CE Notification, Claim Notice."""

    __tablename__ = "commercial_notice_items"
    __table_args__ = (
        UniqueConstraint(
            "project_id", "ref", name="uq_commercial_notice_items_project_ref"
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id"), index=True, nullable=False
    )
    package_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("work_packages.id"), nullable=True, index=True
    )
    ref: Mapped[str] = mapped_column(String(100), nullable=False)
    contract_ref: Mapped[str] = mapped_column(String(100), nullable=False)
    kind: Mapped[NoticeKind] = mapped_column(SAEnum(NoticeKind), nullable=False)
    due_days: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[NoticeStatus] = mapped_column(
        SAEnum(NoticeStatus), nullable=False, default=NoticeStatus.open
    )
    owner: Mapped[str] = mapped_column(String(255), nullable=False)
