"""ORAT Readiness & Handover models.

Distilled from `meridian_track_a_10_orat_readiness_persistence.py`. Covers the
four pillars of Module 10 operational readiness:

- `OratWorkstream` — named ORAT workstreams (airside, terminal ops, retail, IT,
  etc.) with progress and status signals
- `OratTrial` — trial events (tabletop, partial, integrated, full rehearsal)
  optionally tied to a workstream
- `TrainingGroup` — staff training groups by function with trained/target
  headcount ratio
- `HandoverItem` — asset-group handover register, optionally tied to a work
  package, with verification evidence %

Every entity is project- and tenant-scoped with a `(project_id, <natural_key>)`
uniqueness constraint so references and names remain human-addressable within
a project.

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
    HandoverStatus,
    OratWorkstreamStatus,
    TrainingStatus,
    TrialStatus,
)


class OratWorkstream(Base, TimestampMixin, TenantScopedMixin):
    """ORAT workstream — a named readiness track with progress signal.

    Typical examples: Airside Operations, Terminal Operations, Ground Handling,
    Retail/F&B, IT/FIDS/CUTE, Security, Emergency Response. `status` drives the
    RAG signal on the ORAT dashboard; `progress_pct` drives the aggregate
    average progress across workstreams.
    """

    __tablename__ = "orat_workstreams"
    __table_args__ = (
        UniqueConstraint(
            "project_id", "name", name="uq_orat_workstreams_project_name"
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    owner: Mapped[str] = mapped_column(String(255), nullable=False)
    progress_pct: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[OratWorkstreamStatus] = mapped_column(
        SAEnum(OratWorkstreamStatus),
        nullable=False,
        default=OratWorkstreamStatus.not_started,
    )
    due_month: Mapped[int] = mapped_column(Integer, nullable=False)


class OratTrial(Base, TimestampMixin, TenantScopedMixin):
    """ORAT trial record — rehearsal, tabletop, partial or integrated trial.

    `workstream_id` is nullable so cross-workstream trials (e.g. integrated
    dress rehearsal) can exist independently. `observations` is the narrative
    output — failures and lessons learned feed the snag list and back-briefing
    into the master ORAT plan.
    """

    __tablename__ = "orat_trials"
    __table_args__ = (
        UniqueConstraint(
            "project_id", "ref", name="uq_orat_trials_project_ref"
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id"), index=True, nullable=False
    )
    workstream_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("orat_workstreams.id"),
        nullable=True,
        index=True,
    )
    ref: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    participants: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[TrialStatus] = mapped_column(
        SAEnum(TrialStatus), nullable=False, default=TrialStatus.planned
    )
    observations: Mapped[str] = mapped_column(Text, nullable=False)


class TrainingGroup(Base, TimestampMixin, TenantScopedMixin):
    """Training group — staff cohort to be trained by function.

    Completion ratio (`trained_headcount / target_headcount`) is the principal
    readiness signal for the training workstream. Groups are uniquely named
    per project so duplicate rows (e.g. double-counting ground-handling staff)
    are prevented at the DB layer.
    """

    __tablename__ = "training_groups"
    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "function_name",
            name="uq_training_groups_project_function",
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id"), index=True, nullable=False
    )
    function_name: Mapped[str] = mapped_column(String(255), nullable=False)
    target_headcount: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    trained_headcount: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    status: Mapped[TrainingStatus] = mapped_column(
        SAEnum(TrainingStatus),
        nullable=False,
        default=TrainingStatus.not_started,
    )
    owner: Mapped[str] = mapped_column(String(255), nullable=False)


class HandoverItem(Base, TimestampMixin, TenantScopedMixin):
    """Handover register entry — asset group transfer record.

    Tracks a discrete asset group (e.g. BHS, jet bridges, FIDS, terminal
    finishes) moving from construction/commissioning into operations.
    `package_id` is nullable — some handover items (e.g. ATC equipment,
    regulatory artefacts) do not map cleanly to a single work package.
    `evidence_pct` is the aggregated verification maturity.
    """

    __tablename__ = "handover_items"
    __table_args__ = (
        UniqueConstraint(
            "project_id", "ref", name="uq_handover_items_project_ref"
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id"), index=True, nullable=False
    )
    package_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("work_packages.id"),
        nullable=True,
        index=True,
    )
    ref: Mapped[str] = mapped_column(String(100), nullable=False)
    asset_group: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[HandoverStatus] = mapped_column(
        SAEnum(HandoverStatus), nullable=False, default=HandoverStatus.pending
    )
    evidence_pct: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    owner: Mapped[str] = mapped_column(String(255), nullable=False)
