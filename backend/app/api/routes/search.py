"""Enterprise Search & Retrieval router.

Port of `meridian_track_a_12_enterprise_search_retrieval_persistence.py`
FastAPI handlers into a single project-scoped APIRouter at
`/projects/{project_id}/search`. Sub-resources live under the same project
prefix so tenant isolation rides along on every request:

- ``"/index"``                  — indexed search records register
- ``"/query"``                  — retrieval endpoint (ILIKE over title /
                                  summary / tags / status / entity_ref)
- ``"/saved-searches"``         — user-saved search recipes
- ``"/connector-references"``   — external-system pointers (BIM360,
                                  SharePoint, Teams)
- ``"/summary"``                — project-wide search posture rollup
- ``"/connector-pressure"``     — per-source connector health heat-map

Tenant isolation via `get_project_for_view/edit`; audit log on every
mutation; single commit per request. Patch routes are kept project-scoped
(unlike the loose Track A prototype's `/saved-searches/{id}` handlers) so
tenant_id can never be bypassed via a bare id. `SearchIndexRecord.tags` is
exposed on the wire as `list[str]` but persisted as a comma-separated
string — `_index_to_read` is the ORM-to-schema adapter.

Meridian Airport PMO suite
(c) GV Softwares. Developed by Gaurav Vatsa. All rights reserved.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.deps import (
    CurrentPrincipal,
    get_current_principal,
    get_project_for_edit,
    get_project_for_view,
)
from app.db.session import get_db
from app.models.core import Project
from app.models.enums import (
    ConnectorSyncStatus,
    SavedSearchScope,
    SearchEntityType,
    SearchGroup,
    SearchSource,
)
from app.models.search import (
    ConnectorReference,
    SavedSearch,
    SearchIndexRecord,
)
from app.schemas.search import (
    ConnectorReferenceCreate,
    ConnectorReferenceRead,
    ConnectorReferenceUpdate,
    ConnectorSourcePressure,
    SavedSearchCreate,
    SavedSearchRead,
    SavedSearchUpdate,
    SearchIndexRecordCreate,
    SearchIndexRecordRead,
    SearchIndexRecordUpdate,
    SearchQueryResult,
    SearchSummary,
)
from app.services.audit import write_audit_log

router = APIRouter(prefix="/projects/{project_id}/search")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _tags_to_csv(tags: Optional[List[str]]) -> Optional[str]:
    if tags is None:
        return None
    cleaned = [t.strip() for t in tags if t and t.strip()]
    return ", ".join(cleaned) if cleaned else None


def _csv_to_tags(value: Optional[str]) -> List[str]:
    if not value:
        return []
    return [t.strip() for t in value.split(",") if t.strip()]


def _index_to_read(item: SearchIndexRecord) -> SearchIndexRecordRead:
    """Adapt an ORM row to the public schema — tag CSV → list."""
    return SearchIndexRecordRead(
        id=item.id,
        project_id=item.project_id,
        tenant_id=item.tenant_id,
        entity_type=item.entity_type,
        entity_ref=item.entity_ref,
        title=item.title,
        summary=item.summary,
        source=item.source,
        group_name=item.group_name,
        package_code=item.package_code,
        status_text=item.status_text,
        tags=_csv_to_tags(item.tags_csv),
        permission_scope=item.permission_scope,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def _validate_index_record(
    db: Session, tenant_id: str, project_id: str, record_id: str
) -> SearchIndexRecord:
    row = (
        db.query(SearchIndexRecord)
        .filter(
            SearchIndexRecord.id == record_id,
            SearchIndexRecord.project_id == project_id,
            SearchIndexRecord.tenant_id == tenant_id,
        )
        .first()
    )
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Search index record {record_id} not found for project.",
        )
    return row


# ---------------------------------------------------------------------------
# Search Index Records
# ---------------------------------------------------------------------------


@router.get("/index", response_model=List[SearchIndexRecordRead])
def list_search_index(
    entity_type: Optional[SearchEntityType] = Query(default=None),
    source: Optional[SearchSource] = Query(default=None),
    group_name: Optional[SearchGroup] = Query(default=None),
    package_code: Optional[str] = Query(default=None),
    project: Project = Depends(get_project_for_view),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> List[SearchIndexRecordRead]:
    q = db.query(SearchIndexRecord).filter(
        SearchIndexRecord.project_id == project.id,
        SearchIndexRecord.tenant_id == principal.tenant_id,
    )
    if entity_type is not None:
        q = q.filter(SearchIndexRecord.entity_type == entity_type)
    if source is not None:
        q = q.filter(SearchIndexRecord.source == source)
    if group_name is not None:
        q = q.filter(SearchIndexRecord.group_name == group_name)
    if package_code is not None:
        q = q.filter(SearchIndexRecord.package_code == package_code)
    rows = q.order_by(
        SearchIndexRecord.entity_type.asc(), SearchIndexRecord.entity_ref.asc()
    ).all()
    return [_index_to_read(r) for r in rows]


@router.post(
    "/index",
    response_model=SearchIndexRecordRead,
    status_code=status.HTTP_201_CREATED,
)
def create_search_index_record(
    payload: SearchIndexRecordCreate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> SearchIndexRecordRead:
    duplicate = (
        db.query(SearchIndexRecord)
        .filter(
            SearchIndexRecord.project_id == project.id,
            SearchIndexRecord.tenant_id == principal.tenant_id,
            SearchIndexRecord.entity_type == payload.entity_type,
            SearchIndexRecord.entity_ref == payload.entity_ref,
        )
        .first()
    )
    if duplicate is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Search index record {payload.entity_type.value}/"
                f"{payload.entity_ref!r} already exists in project."
            ),
        )

    item = SearchIndexRecord(
        tenant_id=principal.tenant_id,
        project_id=project.id,
        entity_type=payload.entity_type,
        entity_ref=payload.entity_ref,
        title=payload.title,
        summary=payload.summary,
        source=payload.source,
        group_name=payload.group_name,
        package_code=payload.package_code,
        status_text=payload.status_text,
        tags_csv=_tags_to_csv(payload.tags),
        permission_scope=payload.permission_scope,
    )
    db.add(item)
    db.flush()
    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="SearchIndexRecord",
        entity_id=item.id,
        action="created",
        details={
            "entity_type": item.entity_type.value,
            "entity_ref": item.entity_ref,
            "source": item.source.value,
        },
    )
    db.commit()
    db.refresh(item)
    return _index_to_read(item)


@router.patch(
    "/index/{record_id}", response_model=SearchIndexRecordRead
)
def update_search_index_record(
    record_id: str,
    payload: SearchIndexRecordUpdate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> SearchIndexRecordRead:
    item = _validate_index_record(
        db, principal.tenant_id, project.id, record_id
    )
    data = payload.model_dump(exclude_unset=True)
    if "tags" in data:
        tags_value = data.pop("tags")
        item.tags_csv = _tags_to_csv(tags_value)
    for field, value in data.items():
        setattr(item, field, value)
    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="SearchIndexRecord",
        entity_id=item.id,
        action="updated",
        details=data,
    )
    db.commit()
    db.refresh(item)
    return _index_to_read(item)


# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------


@router.get("/query", response_model=SearchQueryResult)
def query_search_index(
    q: str = Query(
        ...,
        min_length=1,
        description="Retrieval query over title, summary, tags, status, and entity ref.",
    ),
    entity_type: Optional[SearchEntityType] = Query(default=None),
    source: Optional[SearchSource] = Query(default=None),
    package_code: Optional[str] = Query(default=None),
    project: Project = Depends(get_project_for_view),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> SearchQueryResult:
    pattern = f"%{q.strip()}%"
    query = db.query(SearchIndexRecord).filter(
        SearchIndexRecord.project_id == project.id,
        SearchIndexRecord.tenant_id == principal.tenant_id,
        or_(
            SearchIndexRecord.title.ilike(pattern),
            SearchIndexRecord.summary.ilike(pattern),
            SearchIndexRecord.tags_csv.ilike(pattern),
            SearchIndexRecord.status_text.ilike(pattern),
            SearchIndexRecord.entity_ref.ilike(pattern),
        ),
    )
    if entity_type is not None:
        query = query.filter(SearchIndexRecord.entity_type == entity_type)
    if source is not None:
        query = query.filter(SearchIndexRecord.source == source)
    if package_code is not None:
        query = query.filter(SearchIndexRecord.package_code == package_code)

    items = query.order_by(SearchIndexRecord.updated_at.desc()).all()
    grouped_counts: Dict[str, int] = {}
    for item in items:
        key = item.entity_type.value
        grouped_counts[key] = grouped_counts.get(key, 0) + 1

    return SearchQueryResult(
        total=len(items),
        grouped_counts=grouped_counts,
        results=[_index_to_read(item) for item in items],
    )


# ---------------------------------------------------------------------------
# Saved Searches
# ---------------------------------------------------------------------------


@router.get("/saved-searches", response_model=List[SavedSearchRead])
def list_saved_searches(
    scope: Optional[SavedSearchScope] = Query(default=None),
    project: Project = Depends(get_project_for_view),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> List[SavedSearchRead]:
    q = db.query(SavedSearch).filter(
        SavedSearch.project_id == project.id,
        SavedSearch.tenant_id == principal.tenant_id,
    )
    if scope is not None:
        q = q.filter(SavedSearch.scope == scope)
    rows = q.order_by(SavedSearch.name.asc()).all()
    return [SavedSearchRead.model_validate(r) for r in rows]


@router.post(
    "/saved-searches",
    response_model=SavedSearchRead,
    status_code=status.HTTP_201_CREATED,
)
def create_saved_search(
    payload: SavedSearchCreate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> SavedSearchRead:
    duplicate = (
        db.query(SavedSearch)
        .filter(
            SavedSearch.project_id == project.id,
            SavedSearch.tenant_id == principal.tenant_id,
            SavedSearch.name == payload.name,
        )
        .first()
    )
    if duplicate is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Saved search {payload.name!r} already exists in project.",
        )

    item = SavedSearch(
        tenant_id=principal.tenant_id,
        project_id=project.id,
        user_email=principal.email,
        name=payload.name,
        query_text=payload.query_text,
        scope=payload.scope,
        type_filter=payload.type_filter,
        source_filter=payload.source_filter,
        package_filter=payload.package_filter,
    )
    db.add(item)
    db.flush()
    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="SavedSearch",
        entity_id=item.id,
        action="created",
        details={
            "name": item.name,
            "scope": item.scope.value,
        },
    )
    db.commit()
    db.refresh(item)
    return SavedSearchRead.model_validate(item)


@router.patch(
    "/saved-searches/{saved_search_id}", response_model=SavedSearchRead
)
def update_saved_search(
    saved_search_id: str,
    payload: SavedSearchUpdate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> SavedSearchRead:
    item = (
        db.query(SavedSearch)
        .filter(
            SavedSearch.id == saved_search_id,
            SavedSearch.project_id == project.id,
            SavedSearch.tenant_id == principal.tenant_id,
        )
        .first()
    )
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved search not found.",
        )
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(item, field, value)
    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="SavedSearch",
        entity_id=item.id,
        action="updated",
        details=data,
    )
    db.commit()
    db.refresh(item)
    return SavedSearchRead.model_validate(item)


# ---------------------------------------------------------------------------
# Connector References
# ---------------------------------------------------------------------------


@router.get(
    "/connector-references", response_model=List[ConnectorReferenceRead]
)
def list_connector_references(
    source: Optional[SearchSource] = Query(default=None),
    sync_status: Optional[ConnectorSyncStatus] = Query(default=None),
    project: Project = Depends(get_project_for_view),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> List[ConnectorReferenceRead]:
    q = db.query(ConnectorReference).filter(
        ConnectorReference.project_id == project.id,
        ConnectorReference.tenant_id == principal.tenant_id,
    )
    if source is not None:
        q = q.filter(ConnectorReference.source == source)
    if sync_status is not None:
        q = q.filter(ConnectorReference.sync_status == sync_status)
    rows = q.order_by(
        ConnectorReference.source.asc(), ConnectorReference.external_ref.asc()
    ).all()
    return [ConnectorReferenceRead.model_validate(r) for r in rows]


@router.post(
    "/connector-references",
    response_model=ConnectorReferenceRead,
    status_code=status.HTTP_201_CREATED,
)
def create_connector_reference(
    payload: ConnectorReferenceCreate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> ConnectorReferenceRead:
    if payload.index_record_id is not None:
        _validate_index_record(
            db, principal.tenant_id, project.id, payload.index_record_id
        )

    duplicate = (
        db.query(ConnectorReference)
        .filter(
            ConnectorReference.project_id == project.id,
            ConnectorReference.tenant_id == principal.tenant_id,
            ConnectorReference.external_ref == payload.external_ref,
        )
        .first()
    )
    if duplicate is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Connector reference {payload.external_ref!r} already "
                "exists in project."
            ),
        )

    item = ConnectorReference(
        tenant_id=principal.tenant_id,
        project_id=project.id,
        source=payload.source,
        external_ref=payload.external_ref,
        path=payload.path,
        sync_status=payload.sync_status,
        index_record_id=payload.index_record_id,
    )
    db.add(item)
    db.flush()
    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="ConnectorReference",
        entity_id=item.id,
        action="created",
        details={
            "source": item.source.value,
            "external_ref": item.external_ref,
            "sync_status": item.sync_status.value,
        },
    )
    db.commit()
    db.refresh(item)
    return ConnectorReferenceRead.model_validate(item)


@router.patch(
    "/connector-references/{connector_reference_id}",
    response_model=ConnectorReferenceRead,
)
def update_connector_reference(
    connector_reference_id: str,
    payload: ConnectorReferenceUpdate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> ConnectorReferenceRead:
    item = (
        db.query(ConnectorReference)
        .filter(
            ConnectorReference.id == connector_reference_id,
            ConnectorReference.project_id == project.id,
            ConnectorReference.tenant_id == principal.tenant_id,
        )
        .first()
    )
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connector reference not found.",
        )
    data = payload.model_dump(exclude_unset=True)
    if "index_record_id" in data and data["index_record_id"]:
        _validate_index_record(
            db, principal.tenant_id, project.id, data["index_record_id"]
        )
    for field, value in data.items():
        setattr(item, field, value)
    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="ConnectorReference",
        entity_id=item.id,
        action="updated",
        details=data,
    )
    db.commit()
    db.refresh(item)
    return ConnectorReferenceRead.model_validate(item)


# ---------------------------------------------------------------------------
# Rollups
# ---------------------------------------------------------------------------


@router.get("/summary", response_model=SearchSummary)
def search_summary(
    project: Project = Depends(get_project_for_view),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> SearchSummary:
    records = (
        db.query(SearchIndexRecord)
        .filter(
            SearchIndexRecord.project_id == project.id,
            SearchIndexRecord.tenant_id == principal.tenant_id,
        )
        .all()
    )
    saved = (
        db.query(SavedSearch)
        .filter(
            SavedSearch.project_id == project.id,
            SavedSearch.tenant_id == principal.tenant_id,
        )
        .all()
    )
    connectors = (
        db.query(ConnectorReference)
        .filter(
            ConnectorReference.project_id == project.id,
            ConnectorReference.tenant_id == principal.tenant_id,
        )
        .all()
    )

    by_type: Dict[str, int] = {}
    by_source: Dict[str, int] = {}
    for item in records:
        by_type[item.entity_type.value] = (
            by_type.get(item.entity_type.value, 0) + 1
        )
        by_source[item.source.value] = (
            by_source.get(item.source.value, 0) + 1
        )

    indexed_connectors = sum(
        1 for c in connectors if c.sync_status == ConnectorSyncStatus.indexed
    )
    stale_connectors = sum(
        1
        for c in connectors
        if c.sync_status in {ConnectorSyncStatus.stale, ConnectorSyncStatus.failed}
    )

    return SearchSummary(
        project_id=project.id,
        indexed_record_count=len(records),
        saved_search_count=len(saved),
        connector_reference_count=len(connectors),
        indexed_connector_count=indexed_connectors,
        stale_connector_count=stale_connectors,
        records_by_type=by_type,
        records_by_source=by_source,
    )


@router.get(
    "/connector-pressure", response_model=List[ConnectorSourcePressure]
)
def connector_pressure(
    project: Project = Depends(get_project_for_view),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> List[ConnectorSourcePressure]:
    connectors = (
        db.query(ConnectorReference)
        .filter(
            ConnectorReference.project_id == project.id,
            ConnectorReference.tenant_id == principal.tenant_id,
        )
        .all()
    )
    grouped: Dict[SearchSource, List[ConnectorReference]] = {}
    for c in connectors:
        grouped.setdefault(c.source, []).append(c)

    results: List[ConnectorSourcePressure] = []
    for src in SearchSource:
        bucket = grouped.get(src, [])
        if not bucket:
            continue
        results.append(
            ConnectorSourcePressure(
                source=src,
                total_count=len(bucket),
                indexed_count=sum(
                    1
                    for c in bucket
                    if c.sync_status == ConnectorSyncStatus.indexed
                ),
                pending_count=sum(
                    1
                    for c in bucket
                    if c.sync_status == ConnectorSyncStatus.pending
                ),
                stale_count=sum(
                    1
                    for c in bucket
                    if c.sync_status == ConnectorSyncStatus.stale
                ),
                failed_count=sum(
                    1
                    for c in bucket
                    if c.sync_status == ConnectorSyncStatus.failed
                ),
            )
        )
    return results
