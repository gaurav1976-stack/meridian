"""Meetings, Actions & Compliance models.

Distilled from `meridian_track_a_9_meetings_actions_compliance_persistence.py`.
Covers the three pillars of Module 09 accountability:

- `MeetingRecord` — governance, review and coordination meeting register
- `ActionItem` — cross-module action tracker (sourced from gates, risks, documents,
  commercial events, ORAT) with closure evidence maturity
- `ComplianceItem` — compliance register per domain, again with evidence maturity

All three are project- and tenant-scoped with a `(project_id, ref)` uniqueness
constraint so that references remain human-addressable within a project.

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
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TenantScopedMixin, TimestampMixin
from app.models.enums import (
    ActionPriority,
    ActionSourceType,
    ActionStatus,
    ComplianceDomain,
    ComplianceStatus,
    LinkedModule,
    MeetingType,
)


class MeetingRecord(Base, TimestampMixin, TenantScopedMixin):
    """Record of a formal meeting held in the programme.

    Meetings are the governance substrate of the accountability module — every
    decision and action is expected to trace back to one. `linked_module` gives
    the primary upstream workstream so the meeting index can be cross-filtered
    from the gate, risk, document, commercial and ORAT dashboards.
    """

    __tablename__ = "meeting_records"
    __table_args__ = (
        UniqueConstraint(
            "project_id", "ref", name="uq_meeting_records_project_ref"
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id"), index=True, nullable=False
    )
    ref: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    meeting_type: Mapped[MeetingType] = mapped_column(
        SAEnum(MeetingType), nullable=False
    )
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    chair: Mapped[str] = mapped_column(String(255), nullable=False)
    attendee_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    linked_module: Mapped[LinkedModule] = mapped_column(
        SAEnum(LinkedModule), nullable=False
    )


class ActionItem(Base, TimestampMixin, TenantScopedMixin):
    """Cross-module action item with closure-evidence maturity.

    `source_type` + `source_ref` identify the upstream artefact the action was
    raised against (e.g. `ActionSourceType.gate` with `source_ref="G2"`).
    `closure_evidence_pct` is the dashboard signal for real progress — a Closed
    status with low evidence % is treated as a data-quality flag rather than a
    genuine closure.
    """

    __tablename__ = "action_items"
    __table_args__ = (
        UniqueConstraint(
            "project_id", "ref", name="uq_action_items_project_ref"
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id"), index=True, nullable=False
    )
    package_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("work_packages.id"), nullable=True, index=True
    )
    ref: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    owner: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[ActionSourceType] = mapped_column(
        SAEnum(ActionSourceType), nullable=False
    )
    source_ref: Mapped[str] = mapped_column(String(255), nullable=False)
    priority: Mapped[ActionPriority] = mapped_column(
        SAEnum(ActionPriority), nullable=False
    )
    due_month: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[ActionStatus] = mapped_column(
        SAEnum(ActionStatus), nullable=False, default=ActionStatus.open
    )
    closure_evidence_pct: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )


class ComplianceItem(Base, TimestampMixin, TenantScopedMixin):
    """Compliance register entry, one per obligation in a programme.

    Compliance items differ from action items in that they represent recurring
    or standing obligations (e.g. "gate decision log maintained", "metadata
    completeness ≥ 90%") rather than point actions. `evidence_pct` tracks how
    much of the supporting evidence is in place.
    """

    __tablename__ = "compliance_items"
    __table_args__ = (
        UniqueConstraint(
            "project_id", "ref", name="uq_compliance_items_project_ref"
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id"), index=True, nullable=False
    )
    package_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("work_packages.id"), nullable=True, index=True
    )
    ref: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[ComplianceDomain] = mapped_column(
        SAEnum(ComplianceDomain), nullable=False
    )
    owner: Mapped[str] = mapped_column(String(255), nullable=False)
    due_month: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[ComplianceStatus] = mapped_column(
        SAEnum(ComplianceStatus), nullable=False, default=ComplianceStatus.open
    )
    evidence_pct: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
