"""Risk and opportunity registers.

Distilled from `meridian_track_a_5_risk_opportunity_persistence.py`.
"""
from __future__ import annotations

from datetime import date
from typing import Optional
from uuid import uuid4

from sqlalchemy import Date, Enum as SAEnum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TenantScopedMixin, TimestampMixin
from app.models.enums import OpportunityStatus, RiskCategory, RiskStatus


class RiskItem(Base, TimestampMixin, TenantScopedMixin):
    __tablename__ = "risk_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), index=True, nullable=False)
    package_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("work_packages.id"), nullable=True, index=True
    )
    code: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[RiskCategory] = mapped_column(SAEnum(RiskCategory), nullable=False)
    status: Mapped[RiskStatus] = mapped_column(SAEnum(RiskStatus), nullable=False, default=RiskStatus.identified)
    likelihood: Mapped[int] = mapped_column(Integer, nullable=False, default=3)  # 1-5
    impact: Mapped[int] = mapped_column(Integer, nullable=False, default=3)  # 1-5
    mitigated_likelihood: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    mitigated_impact: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    owner: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    mitigation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    target_closure_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    @property
    def gross_score(self) -> int:
        return self.likelihood * self.impact

    @property
    def residual_score(self) -> int:
        if self.mitigated_likelihood and self.mitigated_impact:
            return self.mitigated_likelihood * self.mitigated_impact
        return self.gross_score


class OpportunityItem(Base, TimestampMixin, TenantScopedMixin):
    __tablename__ = "opportunity_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), index=True, nullable=False)
    code: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[OpportunityStatus] = mapped_column(
        SAEnum(OpportunityStatus), nullable=False, default=OpportunityStatus.identified
    )
    likelihood: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    benefit: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    owner: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    target_realisation_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
