"""Project setup tables: Contract, NumberingRule, MetadataFieldDefinition, WorkflowDefinition.

Distilled from `meridian_track_a_2_project_setup_persistence.py`. WorkPackage lives
in `core.py` because every other domain references it.
"""
from __future__ import annotations

from typing import Optional
from uuid import uuid4

from sqlalchemy import Boolean, Enum as SAEnum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TenantScopedMixin, TimestampMixin
from app.models.enums import ContractForm, ContractStatus


class Contract(Base, TimestampMixin, TenantScopedMixin):
    __tablename__ = "contracts"
    __table_args__ = (
        UniqueConstraint("project_id", "reference", name="uq_contracts_project_reference"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id"), index=True, nullable=False
    )
    reference: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    contractor: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    form: Mapped[ContractForm] = mapped_column(
        SAEnum(ContractForm), nullable=False, default=ContractForm.nec4_ecc
    )
    status: Mapped[ContractStatus] = mapped_column(
        SAEnum(ContractStatus), nullable=False, default=ContractStatus.draft
    )
    value_amount: Mapped[Optional[float]] = mapped_column(nullable=True)
    value_currency: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    project = relationship("Project", back_populates="contracts")


class NumberingRule(Base, TimestampMixin, TenantScopedMixin):
    __tablename__ = "numbering_rules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id"), index=True, nullable=False
    )
    entity: Mapped[str] = mapped_column(String(50), nullable=False)
    pattern: Mapped[str] = mapped_column(String(255), nullable=False)
    next_sequence: Mapped[int] = mapped_column(default=1, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class MetadataFieldDefinition(Base, TimestampMixin, TenantScopedMixin):
    __tablename__ = "metadata_field_definitions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id"), index=True, nullable=False
    )
    entity: Mapped[str] = mapped_column(String(50), nullable=False)
    field_key: Mapped[str] = mapped_column(String(80), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    field_type: Mapped[str] = mapped_column(String(50), nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    options_csv: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class WorkflowDefinition(Base, TimestampMixin, TenantScopedMixin):
    __tablename__ = "workflow_definitions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id"), index=True, nullable=False
    )
    entity: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    approval_mode: Mapped[str] = mapped_column(String(50), nullable=False, default="Sequential")
    states_csv: Mapped[str] = mapped_column(Text, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
