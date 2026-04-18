"""Core multi-tenant tables: Tenant, User, Project, AuditLog, WorkPackage, ProjectMembership.

Consolidated from `meridian_track_a_backend_foundation.py`,
`meridian_track_a_2_project_setup_persistence.py`, and
`meridian_integration_pack_part_4_jwt_auth_role_enforcement.py` (the 12 Track A
files each redeclared subsets of these — this is the single canonical version).
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional
from uuid import uuid4

from sqlalchemy import Boolean, Enum as SAEnum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TenantScopedMixin, TimestampMixin
from app.models.enums import ProjectStatus, UserRole

if TYPE_CHECKING:
    from app.models.project_setup import Contract


class Tenant(Base, TimestampMixin):
    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    region: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    users: Mapped[list["User"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")
    projects: Mapped[list["Project"]] = relationship(back_populates="tenant", cascade="all, delete-orphan")


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), nullable=False, default=UserRole.viewer)
    external_subject: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    tenant: Mapped["Tenant"] = relationship(back_populates="users")
    memberships: Mapped[list["ProjectMembership"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Project(Base, TimestampMixin, TenantScopedMixin):
    __tablename__ = "projects"
    __table_args__ = (UniqueConstraint("tenant_id", "code", name="uq_projects_tenant_code"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[ProjectStatus] = mapped_column(
        SAEnum(ProjectStatus), nullable=False, default=ProjectStatus.planned
    )
    stage: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    tenant: Mapped["Tenant"] = relationship(back_populates="projects")
    work_packages: Mapped[list["WorkPackage"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    contracts: Mapped[list["Contract"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    memberships: Mapped[list["ProjectMembership"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )


class ProjectMembership(Base, TimestampMixin, TenantScopedMixin):
    __tablename__ = "project_memberships"
    __table_args__ = (
        UniqueConstraint("project_id", "user_id", name="uq_project_memberships_project_user"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id"), index=True, nullable=False
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), index=True, nullable=False
    )
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), nullable=False, default=UserRole.viewer)

    project: Mapped["Project"] = relationship(back_populates="memberships")
    user: Mapped["User"] = relationship(back_populates="memberships")


class WorkPackage(Base, TimestampMixin, TenantScopedMixin):
    __tablename__ = "work_packages"
    __table_args__ = (
        UniqueConstraint("project_id", "code", name="uq_work_packages_project_code"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id"), index=True, nullable=False
    )
    code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    package_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    project: Mapped["Project"] = relationship(back_populates="work_packages")


class AuditLog(Base, TimestampMixin, TenantScopedMixin):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    actor_user_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=True
    )
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
