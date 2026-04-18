"""Design Management models.

Distilled from `meridian_track_a_7_design_management_persistence.py`. Covers
design packages (lead discipline + RIBA stage + maturity + freeze control),
deliverables (drawings, reports, calcs, specs, schedules), design interfaces
between packages, and BIM federation / clash rollup.

The `freeze_planned_month` vs `freeze_current_month` pair drives the freeze
variance telemetry on the programme dashboard — positive variance is slip.

Meridian Airport PMO suite
(c) GV Softwares. Developed by Gaurav Vatsa. All rights reserved.
Proprietary — unauthorised copying, distribution, modification or use prohibited.
"""
from __future__ import annotations

from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TenantScopedMixin, TimestampMixin
from app.models.enums import (
    DeliverableStatus,
    DeliverableType,
    DesignPackageStatus,
    InterfaceStatus,
    ModelShareStatus,
    RibaStage,
)


class DesignPackage(Base, TimestampMixin, TenantScopedMixin):
    """A design package — a logical chunk of design work with a lead discipline.

    Each package sits at a RIBA stage, carries a maturity percentage, and has
    a planned vs current freeze month so the freeze-control surface can
    compute slip.
    """

    __tablename__ = "design_packages"
    __table_args__ = (
        UniqueConstraint(
            "project_id", "code", name="uq_design_packages_project_code"
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id"), index=True, nullable=False
    )
    package_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("work_packages.id"), nullable=True, index=True
    )
    code: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    lead_discipline: Mapped[str] = mapped_column(String(100), nullable=False)
    stage: Mapped[RibaStage] = mapped_column(SAEnum(RibaStage), nullable=False)
    maturity_pct: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[DesignPackageStatus] = mapped_column(
        SAEnum(DesignPackageStatus), nullable=False, default=DesignPackageStatus.draft
    )
    freeze_planned_month: Mapped[int] = mapped_column(Integer, nullable=False)
    freeze_current_month: Mapped[int] = mapped_column(Integer, nullable=False)


class DesignDeliverable(Base, TimestampMixin, TenantScopedMixin):
    """A single design deliverable — drawing, report, calc, spec, schedule."""

    __tablename__ = "design_deliverables"
    __table_args__ = (
        UniqueConstraint(
            "project_id", "ref", name="uq_design_deliverables_project_ref"
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id"), index=True, nullable=False
    )
    design_package_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("design_packages.id"), nullable=True, index=True
    )
    package_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("work_packages.id"), nullable=True, index=True
    )
    ref: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    discipline: Mapped[str] = mapped_column(String(100), nullable=False)
    deliverable_type: Mapped[DeliverableType] = mapped_column(
        SAEnum(DeliverableType), nullable=False
    )
    stage: Mapped[RibaStage] = mapped_column(SAEnum(RibaStage), nullable=False)
    due_month: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[DeliverableStatus] = mapped_column(
        SAEnum(DeliverableStatus), nullable=False, default=DeliverableStatus.wip
    )
    owner: Mapped[str] = mapped_column(String(255), nullable=False)


class DesignInterfaceItem(Base, TimestampMixin, TenantScopedMixin):
    """Design interface between two packages — maintained per ISO 19650 workflow."""

    __tablename__ = "design_interface_items"
    __table_args__ = (
        UniqueConstraint(
            "project_id", "ref", name="uq_design_interface_items_project_ref"
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id"), index=True, nullable=False
    )
    ref: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    package_a_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("work_packages.id"), nullable=False, index=True
    )
    package_b_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("work_packages.id"), nullable=False, index=True
    )
    owner: Mapped[str] = mapped_column(String(255), nullable=False)
    severity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[InterfaceStatus] = mapped_column(
        SAEnum(InterfaceStatus), nullable=False, default=InterfaceStatus.open
    )
    due_month: Mapped[int] = mapped_column(Integer, nullable=False)


class BimCoordinationItem(Base, TimestampMixin, TenantScopedMixin):
    """BIM federation rollup per workstream — clash counts + share status."""

    __tablename__ = "bim_coordination_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id"), index=True, nullable=False
    )
    workstream: Mapped[str] = mapped_column(String(100), nullable=False)
    clash_open: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    clash_critical: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    federation_ready: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    model_share_status: Mapped[ModelShareStatus] = mapped_column(
        SAEnum(ModelShareStatus), nullable=False, default=ModelShareStatus.wip
    )
