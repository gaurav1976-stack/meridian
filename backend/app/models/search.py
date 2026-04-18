"""Enterprise Search & Retrieval models.

Distilled from `meridian_track_a_12_enterprise_search_retrieval_persistence.py`.
Covers the three pillars of Module 12:

- `SearchIndexRecord` — a normalised pointer to a discoverable artefact
  anywhere across the Meridian domains (Gate, Risk, Commercial, Design,
  Document, Action, ORAT, Repository, Report, Schedule, Project). Holds the
  searchable title, summary, and a comma-separated tag list plus the source
  system and coarse grouping used by the UI to facet results.
- `SavedSearch` — a user-saved retrieval recipe: a query string, optional
  type / source / package filters, and a scope flag that governs whether the
  search runs across everything, only a specific module set, or only the
  connector-backed repository surface.
- `ConnectorReference` — an external-system pointer (BIM360, SharePoint,
  Teams) that either sits alongside an indexed record (linked back via
  `index_record_id`) or stands on its own pending ingestion. Carries a sync
  status so the reporting layer can surface drift between the source system
  and the local index.

All three are project- and tenant-scoped. Uniqueness keys:

- `SearchIndexRecord` → `(project_id, entity_type, entity_ref)` so a project
  cannot index the same logical entity twice.
- `SavedSearch` → `(project_id, name)` so a saved search's friendly name is
  stable within a project.
- `ConnectorReference` → `(project_id, external_ref)` so each external
  pointer is unique per project.

`SearchIndexRecord.tags_csv` is persisted as a comma-joined string to avoid
a join table for the MVP; the schema and router flatten this into a list of
strings on the wire.

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
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TenantScopedMixin, TimestampMixin
from app.models.enums import (
    ConnectorSyncStatus,
    SavedSearchScope,
    SearchEntityType,
    SearchGroup,
    SearchSource,
)


class SearchIndexRecord(Base, TimestampMixin, TenantScopedMixin):
    """One entry in the unified enterprise search index.

    Every row is a pointer to a single discoverable artefact anywhere inside
    the Meridian surface. `entity_ref` is the human-addressable reference (e.g.
    `"G2"`, `"RISK-001"`, `"CE-001"`) that rides along with the record so the
    result card can deep-link back to the originating module. `permission_scope`
    captures the access boundary as a coarse string — `tenant:all`,
    `package:TER`, `role:orat_manager`, etc. — ahead of the production RBAC
    engine that will expand this into structured claims.
    """

    __tablename__ = "search_index_records"
    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "entity_type",
            "entity_ref",
            name="uq_search_index_records_entity",
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id"), index=True, nullable=False
    )
    entity_type: Mapped[SearchEntityType] = mapped_column(
        SAEnum(SearchEntityType), nullable=False
    )
    entity_ref: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[SearchSource] = mapped_column(
        SAEnum(SearchSource), nullable=False
    )
    group_name: Mapped[SearchGroup] = mapped_column(
        SAEnum(SearchGroup), nullable=False
    )
    package_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status_text: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tags_csv: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    permission_scope: Mapped[str] = mapped_column(
        String(255), nullable=False, default="tenant:all"
    )


class SavedSearch(Base, TimestampMixin, TenantScopedMixin):
    """A named, persistent search recipe tied to a user and project.

    `query_text` is the raw retrieval string; the filter fields are optional
    CSV strings so the saved recipe can narrow by type / source / package
    without a join table. `scope` controls whether the search runs across the
    entire index, a module subset, or only the connector-backed repository
    surface.
    """

    __tablename__ = "saved_searches"
    __table_args__ = (
        UniqueConstraint(
            "project_id", "name", name="uq_saved_searches_project_name"
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id"), index=True, nullable=False
    )
    user_email: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    scope: Mapped[SavedSearchScope] = mapped_column(
        SAEnum(SavedSearchScope),
        nullable=False,
        default=SavedSearchScope.all,
    )
    type_filter: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    source_filter: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    package_filter: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)


class ConnectorReference(Base, TimestampMixin, TenantScopedMixin):
    """An external-system pointer ingested into the Meridian index surface.

    `external_ref` is the source-system identifier (e.g. a BIM360 document id,
    a SharePoint item id, a Teams message id). `path` is the human-readable
    location so the result card can render a breadcrumb. `index_record_id`
    links to the `SearchIndexRecord` this connector pointer surfaces — nullable
    because a reference can exist in `Pending` state before the ingestion
    pipeline has produced the matching search row.
    """

    __tablename__ = "connector_references"
    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "external_ref",
            name="uq_connector_references_external_ref",
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id"), index=True, nullable=False
    )
    source: Mapped[SearchSource] = mapped_column(
        SAEnum(SearchSource), nullable=False
    )
    external_ref: Mapped[str] = mapped_column(String(255), nullable=False)
    path: Mapped[str] = mapped_column(Text, nullable=False)
    sync_status: Mapped[ConnectorSyncStatus] = mapped_column(
        SAEnum(ConnectorSyncStatus),
        nullable=False,
        default=ConnectorSyncStatus.pending,
    )
    index_record_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("search_index_records.id"),
        nullable=True,
        index=True,
    )
