"""Stage Gate Governance models.

Distilled from `meridian_track_a_4_stage_gate_governance_persistence.py`.
All models inherit the single shared `Base` + `TenantScopedMixin` + `TimestampMixin`.

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
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TenantScopedMixin, TimestampMixin
from app.models.enums import (
    ApprovalStatus,
    DecisionOutcome,
    EvidenceCategory,
    EvidenceStatus,
    GateStatus,
)


class GateDefinition(Base, TimestampMixin, TenantScopedMixin):
    """A single stage gate on a project (G0 Mandate → G8 Go-Live)."""

    __tablename__ = "gate_definitions"
    __table_args__ = (
        UniqueConstraint("project_id", "code", name="uq_gate_definitions_project_code"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id"), index=True, nullable=False
    )
    code: Mapped[str] = mapped_column(String(20), nullable=False)  # e.g. G1, G2
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    purpose: Mapped[str] = mapped_column(Text, nullable=False)
    target_month: Mapped[int] = mapped_column(Integer, nullable=False)  # month offset from project start
    status: Mapped[GateStatus] = mapped_column(
        SAEnum(GateStatus), nullable=False, default=GateStatus.upcoming
    )


class GatePackageLink(Base, TimestampMixin, TenantScopedMixin):
    """Join row — which work packages must pass a given gate."""

    __tablename__ = "gate_package_links"
    __table_args__ = (
        UniqueConstraint(
            "gate_definition_id", "package_id", name="uq_gate_package_links_gate_package"
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id"), index=True, nullable=False
    )
    gate_definition_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("gate_definitions.id"), index=True, nullable=False
    )
    package_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("work_packages.id"), index=True, nullable=False
    )


class GateEvidenceItem(Base, TimestampMixin, TenantScopedMixin):
    """Evidence artefact required/submitted/accepted against a gate."""

    __tablename__ = "gate_evidence_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id"), index=True, nullable=False
    )
    gate_definition_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("gate_definitions.id"), index=True, nullable=False
    )
    package_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("work_packages.id"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[EvidenceCategory] = mapped_column(SAEnum(EvidenceCategory), nullable=False)
    required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    status: Mapped[EvidenceStatus] = mapped_column(
        SAEnum(EvidenceStatus), nullable=False, default=EvidenceStatus.draft
    )
    owner: Mapped[str] = mapped_column(String(255), nullable=False)


class GateApproval(Base, TimestampMixin, TenantScopedMixin):
    """A named approver's response on a given gate."""

    __tablename__ = "gate_approvals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id"), index=True, nullable=False
    )
    gate_definition_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("gate_definitions.id"), index=True, nullable=False
    )
    approver: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[ApprovalStatus] = mapped_column(
        SAEnum(ApprovalStatus), nullable=False, default=ApprovalStatus.pending
    )
    response_date: Mapped[Optional[str]] = mapped_column(String(25), nullable=True)


class GateDecision(Base, TimestampMixin, TenantScopedMixin):
    """A recorded gate-board decision — Proceed / Proceed with Conditions / Hold / Rejected."""

    __tablename__ = "gate_decisions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id"), index=True, nullable=False
    )
    gate_definition_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("gate_definitions.id"), index=True, nullable=False
    )
    meeting_ref: Mapped[str] = mapped_column(String(100), nullable=False)
    decision_date: Mapped[str] = mapped_column(String(25), nullable=False)
    outcome: Mapped[DecisionOutcome] = mapped_column(SAEnum(DecisionOutcome), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
