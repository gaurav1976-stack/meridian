"""Enterprise Search & Retrieval — Pydantic schemas.

Mirrors the Track A.12 prototype but typed end-to-end against the shared
enum classes in `app.models.enums`. `SearchIndexRecord` persists tags as a
CSV string in the database; the schema surface exposes them as `list[str]`
via `tags` (an `_index_to_read` helper in the router joins / splits at the
ORM boundary).

The retrieval endpoint returns a `SearchQueryResult` — total count, grouped
counts keyed by entity type, and the hit list. The summary endpoint returns
a `SearchSummary` which is the project-wide rollup consumed by the Search
landing page dashboard.

Meridian Airport PMO suite
(c) GV Softwares. Developed by Gaurav Vatsa. All rights reserved.
Proprietary — unauthorised copying, distribution, modification or use prohibited.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from app.models.enums import (
    ConnectorSyncStatus,
    SavedSearchScope,
    SearchEntityType,
    SearchGroup,
    SearchSource,
)
from app.schemas.common import TimestampedOrm


# ---------------------------------------------------------------------------
# Search Index Record
# ---------------------------------------------------------------------------


class SearchIndexRecordCreate(BaseModel):
    entity_type: SearchEntityType
    entity_ref: str = Field(min_length=1, max_length=255)
    title: str = Field(min_length=1, max_length=255)
    summary: str = Field(min_length=1)
    source: SearchSource
    group_name: SearchGroup
    package_code: Optional[str] = Field(default=None, max_length=50)
    status_text: Optional[str] = Field(default=None, max_length=100)
    tags: List[str] = Field(default_factory=list)
    permission_scope: str = Field(
        min_length=1, max_length=255, default="tenant:all"
    )


class SearchIndexRecordUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    summary: Optional[str] = Field(default=None, min_length=1)
    source: Optional[SearchSource] = None
    group_name: Optional[SearchGroup] = None
    package_code: Optional[str] = Field(default=None, max_length=50)
    status_text: Optional[str] = Field(default=None, max_length=100)
    tags: Optional[List[str]] = None
    permission_scope: Optional[str] = Field(
        default=None, min_length=1, max_length=255
    )


class SearchIndexRecordRead(TimestampedOrm):
    id: str
    project_id: str
    tenant_id: str
    entity_type: SearchEntityType
    entity_ref: str
    title: str
    summary: str
    source: SearchSource
    group_name: SearchGroup
    package_code: Optional[str]
    status_text: Optional[str]
    tags: List[str]
    permission_scope: str


# ---------------------------------------------------------------------------
# Saved Search
# ---------------------------------------------------------------------------


class SavedSearchCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    query_text: str = Field(min_length=1)
    scope: SavedSearchScope = SavedSearchScope.all
    type_filter: Optional[str] = Field(default=None, max_length=255)
    source_filter: Optional[str] = Field(default=None, max_length=255)
    package_filter: Optional[str] = Field(default=None, max_length=255)


class SavedSearchUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    query_text: Optional[str] = Field(default=None, min_length=1)
    scope: Optional[SavedSearchScope] = None
    type_filter: Optional[str] = Field(default=None, max_length=255)
    source_filter: Optional[str] = Field(default=None, max_length=255)
    package_filter: Optional[str] = Field(default=None, max_length=255)


class SavedSearchRead(TimestampedOrm):
    id: str
    project_id: str
    tenant_id: str
    user_email: str
    name: str
    query_text: str
    scope: SavedSearchScope
    type_filter: Optional[str]
    source_filter: Optional[str]
    package_filter: Optional[str]


# ---------------------------------------------------------------------------
# Connector Reference
# ---------------------------------------------------------------------------


class ConnectorReferenceCreate(BaseModel):
    source: SearchSource
    external_ref: str = Field(min_length=1, max_length=255)
    path: str = Field(min_length=1)
    sync_status: ConnectorSyncStatus = ConnectorSyncStatus.pending
    index_record_id: Optional[str] = None


class ConnectorReferenceUpdate(BaseModel):
    source: Optional[SearchSource] = None
    path: Optional[str] = Field(default=None, min_length=1)
    sync_status: Optional[ConnectorSyncStatus] = None
    index_record_id: Optional[str] = None


class ConnectorReferenceRead(TimestampedOrm):
    id: str
    project_id: str
    tenant_id: str
    source: SearchSource
    external_ref: str
    path: str
    sync_status: ConnectorSyncStatus
    index_record_id: Optional[str]


# ---------------------------------------------------------------------------
# Retrieval + Rollup
# ---------------------------------------------------------------------------


class SearchQueryResult(BaseModel):
    """Retrieval response. `grouped_counts` is keyed by entity type value."""

    total: int
    grouped_counts: Dict[str, int]
    results: List[SearchIndexRecordRead]


class SearchSummary(BaseModel):
    """Project-wide search posture rollup.

    `indexed_record_count` is the live index size. `indexed_connector_count`
    counts connector references in `Indexed` state (i.e. current and
    searchable). `stale_connector_count` rolls up `Stale` + `Failed` — the
    signal the PMO uses to prioritise re-ingestion. `records_by_type` and
    `records_by_source` are facet histograms the dashboard renders as the
    distribution panels.
    """

    project_id: str
    indexed_record_count: int
    saved_search_count: int
    connector_reference_count: int
    indexed_connector_count: int
    stale_connector_count: int
    records_by_type: Dict[str, int]
    records_by_source: Dict[str, int]


class ConnectorSourcePressure(BaseModel):
    """Per-source connector health heat-map.

    Shows the count of references per source system plus the breakdown by
    sync state. Sources with a high `stale_count` surface as a data quality
    signal — either the connector has broken or the ingestion cadence needs
    to be raised.
    """

    source: SearchSource
    total_count: int
    indexed_count: int
    pending_count: int
    stale_count: int
    failed_count: int
