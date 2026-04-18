"""Document Control router.

Port of `meridian_track_a_8_document_control_persistence.py` FastAPI handlers
into a single project-scoped APIRouter at `/projects/{project_id}/documents`.
Exposes the controlled document register (ISO 19650 numbered + revisioned),
the per-document review register, the transmittal register, and external
repository links (BIM360 / SharePoint / Meridian-native), plus the
project-level document-control telemetry summary.

Tenant isolation via `get_project_for_view/edit`; audit-log on every mutation;
single commit per request.

Meridian Airport PMO suite
(c) GV Softwares. Developed by Gaurav Vatsa. All rights reserved.
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import (
    CurrentPrincipal,
    get_current_principal,
    get_project_for_edit,
    get_project_for_view,
)
from app.db.session import get_db
from app.models.core import Project, WorkPackage
from app.models.documents import (
    ControlledDocument,
    DocumentReview,
    RepositoryLink,
    TransmittalRecord,
)
from app.models.enums import (
    DocumentWorkflowStatus,
    RepositorySource,
    ReviewStatus,
    SyncStatus,
    TransmittalStatus,
)
from app.schemas.documents import (
    ControlledDocumentCreate,
    ControlledDocumentRead,
    ControlledDocumentUpdate,
    DocumentControlSummary,
    DocumentReviewCreate,
    DocumentReviewRead,
    DocumentReviewUpdate,
    RepositoryLinkCreate,
    RepositoryLinkRead,
    RepositoryLinkUpdate,
    TransmittalCreate,
    TransmittalRead,
    TransmittalUpdate,
)
from app.services.audit import write_audit_log

router = APIRouter(prefix="/projects/{project_id}/documents")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _validate_work_package(
    db: Session, tenant_id: str, project_id: str, package_id: str
) -> WorkPackage:
    pkg = (
        db.query(WorkPackage)
        .filter(
            WorkPackage.id == package_id,
            WorkPackage.project_id == project_id,
            WorkPackage.tenant_id == tenant_id,
        )
        .first()
    )
    if pkg is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Work package {package_id} not found for project.",
        )
    return pkg


def _validate_document(
    db: Session, tenant_id: str, project_id: str, document_id: str
) -> ControlledDocument:
    doc = (
        db.query(ControlledDocument)
        .filter(
            ControlledDocument.id == document_id,
            ControlledDocument.project_id == project_id,
            ControlledDocument.tenant_id == tenant_id,
        )
        .first()
    )
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found for project.",
        )
    return doc


# ---------------------------------------------------------------------------
# Controlled documents
# ---------------------------------------------------------------------------


@router.get("", response_model=List[ControlledDocumentRead])
def list_documents(
    workflow_status: Optional[DocumentWorkflowStatus] = Query(default=None),
    source: Optional[RepositorySource] = Query(default=None),
    project: Project = Depends(get_project_for_view),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> List[ControlledDocumentRead]:
    q = db.query(ControlledDocument).filter(
        ControlledDocument.project_id == project.id,
        ControlledDocument.tenant_id == principal.tenant_id,
    )
    if workflow_status is not None:
        q = q.filter(ControlledDocument.workflow_status == workflow_status)
    if source is not None:
        q = q.filter(ControlledDocument.source == source)
    rows = q.order_by(ControlledDocument.number.asc()).all()
    return [ControlledDocumentRead.model_validate(r) for r in rows]


@router.post(
    "",
    response_model=ControlledDocumentRead,
    status_code=status.HTTP_201_CREATED,
)
def create_document(
    payload: ControlledDocumentCreate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> ControlledDocumentRead:
    if payload.package_id is not None:
        _validate_work_package(db, principal.tenant_id, project.id, payload.package_id)

    duplicate = (
        db.query(ControlledDocument)
        .filter(
            ControlledDocument.project_id == project.id,
            ControlledDocument.tenant_id == principal.tenant_id,
            ControlledDocument.number == payload.number,
        )
        .first()
    )
    if duplicate is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Document number {payload.number!r} already exists in project.",
        )

    item = ControlledDocument(
        tenant_id=principal.tenant_id,
        project_id=project.id,
        package_id=payload.package_id,
        number=payload.number,
        title=payload.title,
        discipline=payload.discipline,
        document_type=payload.document_type,
        revision=payload.revision,
        suitability=payload.suitability,
        workflow_status=payload.workflow_status,
        cde_stage=payload.cde_stage,
        owner=payload.owner,
        due_month=payload.due_month,
        metadata_pct=payload.metadata_pct,
        source=payload.source,
    )
    db.add(item)
    db.flush()
    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="ControlledDocument",
        entity_id=item.id,
        action="created",
        details={
            "number": item.number,
            "type": item.document_type.value,
            "revision": item.revision,
        },
    )
    db.commit()
    db.refresh(item)
    return ControlledDocumentRead.model_validate(item)


@router.patch("/{document_id}", response_model=ControlledDocumentRead)
def update_document(
    document_id: str,
    payload: ControlledDocumentUpdate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> ControlledDocumentRead:
    item = _validate_document(db, principal.tenant_id, project.id, document_id)
    data = payload.model_dump(exclude_unset=True)
    if "package_id" in data and data["package_id"]:
        _validate_work_package(
            db, principal.tenant_id, project.id, data["package_id"]
        )
    for field, value in data.items():
        setattr(item, field, value)
    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="ControlledDocument",
        entity_id=item.id,
        action="updated",
        details=data,
    )
    db.commit()
    db.refresh(item)
    return ControlledDocumentRead.model_validate(item)


# ---------------------------------------------------------------------------
# Reviews
# ---------------------------------------------------------------------------


@router.get("/reviews", response_model=List[DocumentReviewRead])
def list_reviews(
    status_filter: Optional[ReviewStatus] = Query(default=None, alias="status"),
    project: Project = Depends(get_project_for_view),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> List[DocumentReviewRead]:
    q = db.query(DocumentReview).filter(
        DocumentReview.project_id == project.id,
        DocumentReview.tenant_id == principal.tenant_id,
    )
    if status_filter is not None:
        q = q.filter(DocumentReview.status == status_filter)
    rows = q.order_by(DocumentReview.due_month.asc()).all()
    return [DocumentReviewRead.model_validate(r) for r in rows]


@router.post(
    "/reviews",
    response_model=DocumentReviewRead,
    status_code=status.HTTP_201_CREATED,
)
def create_review(
    payload: DocumentReviewCreate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> DocumentReviewRead:
    document = _validate_document(
        db, principal.tenant_id, project.id, payload.document_id
    )
    item = DocumentReview(
        tenant_id=principal.tenant_id,
        project_id=project.id,
        document_id=payload.document_id,
        reviewer=payload.reviewer,
        role=payload.role,
        status=payload.status,
        due_month=payload.due_month,
    )
    db.add(item)
    db.flush()
    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="DocumentReview",
        entity_id=item.id,
        action="created",
        details={
            "document_number": document.number,
            "reviewer": item.reviewer,
            "role": item.role,
        },
    )
    db.commit()
    db.refresh(item)
    return DocumentReviewRead.model_validate(item)


@router.patch("/reviews/{review_id}", response_model=DocumentReviewRead)
def update_review(
    review_id: str,
    payload: DocumentReviewUpdate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> DocumentReviewRead:
    item = (
        db.query(DocumentReview)
        .filter(
            DocumentReview.id == review_id,
            DocumentReview.project_id == project.id,
            DocumentReview.tenant_id == principal.tenant_id,
        )
        .first()
    )
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Review not found."
        )
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(item, field, value)
    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="DocumentReview",
        entity_id=item.id,
        action="updated",
        details=data,
    )
    db.commit()
    db.refresh(item)
    return DocumentReviewRead.model_validate(item)


# ---------------------------------------------------------------------------
# Transmittals
# ---------------------------------------------------------------------------


@router.get("/transmittals", response_model=List[TransmittalRead])
def list_transmittals(
    status_filter: Optional[TransmittalStatus] = Query(default=None, alias="status"),
    project: Project = Depends(get_project_for_view),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> List[TransmittalRead]:
    q = db.query(TransmittalRecord).filter(
        TransmittalRecord.project_id == project.id,
        TransmittalRecord.tenant_id == principal.tenant_id,
    )
    if status_filter is not None:
        q = q.filter(TransmittalRecord.status == status_filter)
    rows = q.order_by(TransmittalRecord.issue_month.desc()).all()
    return [TransmittalRead.model_validate(r) for r in rows]


@router.post(
    "/transmittals",
    response_model=TransmittalRead,
    status_code=status.HTTP_201_CREATED,
)
def create_transmittal(
    payload: TransmittalCreate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> TransmittalRead:
    if payload.package_id is not None:
        _validate_work_package(db, principal.tenant_id, project.id, payload.package_id)

    duplicate = (
        db.query(TransmittalRecord)
        .filter(
            TransmittalRecord.project_id == project.id,
            TransmittalRecord.tenant_id == principal.tenant_id,
            TransmittalRecord.ref == payload.ref,
        )
        .first()
    )
    if duplicate is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Transmittal ref {payload.ref!r} already exists in project.",
        )

    item = TransmittalRecord(
        tenant_id=principal.tenant_id,
        project_id=project.id,
        ref=payload.ref,
        package_id=payload.package_id,
        recipient=payload.recipient,
        document_count=payload.document_count,
        issue_month=payload.issue_month,
        status=payload.status,
    )
    db.add(item)
    db.flush()
    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="TransmittalRecord",
        entity_id=item.id,
        action="created",
        details={
            "ref": item.ref,
            "recipient": item.recipient,
            "document_count": item.document_count,
        },
    )
    db.commit()
    db.refresh(item)
    return TransmittalRead.model_validate(item)


@router.patch("/transmittals/{transmittal_id}", response_model=TransmittalRead)
def update_transmittal(
    transmittal_id: str,
    payload: TransmittalUpdate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> TransmittalRead:
    item = (
        db.query(TransmittalRecord)
        .filter(
            TransmittalRecord.id == transmittal_id,
            TransmittalRecord.project_id == project.id,
            TransmittalRecord.tenant_id == principal.tenant_id,
        )
        .first()
    )
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Transmittal not found."
        )
    data = payload.model_dump(exclude_unset=True)
    if "package_id" in data and data["package_id"]:
        _validate_work_package(
            db, principal.tenant_id, project.id, data["package_id"]
        )
    for field, value in data.items():
        setattr(item, field, value)
    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="TransmittalRecord",
        entity_id=item.id,
        action="updated",
        details=data,
    )
    db.commit()
    db.refresh(item)
    return TransmittalRead.model_validate(item)


# ---------------------------------------------------------------------------
# Repository links
# ---------------------------------------------------------------------------


@router.get("/repository-links", response_model=List[RepositoryLinkRead])
def list_repository_links(
    repository: Optional[RepositorySource] = Query(default=None),
    sync_status: Optional[SyncStatus] = Query(default=None),
    project: Project = Depends(get_project_for_view),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> List[RepositoryLinkRead]:
    q = db.query(RepositoryLink).filter(
        RepositoryLink.project_id == project.id,
        RepositoryLink.tenant_id == principal.tenant_id,
    )
    if repository is not None:
        q = q.filter(RepositoryLink.repository == repository)
    if sync_status is not None:
        q = q.filter(RepositoryLink.sync_status == sync_status)
    rows = q.order_by(RepositoryLink.created_at.desc()).all()
    return [RepositoryLinkRead.model_validate(r) for r in rows]


@router.post(
    "/repository-links",
    response_model=RepositoryLinkRead,
    status_code=status.HTTP_201_CREATED,
)
def create_repository_link(
    payload: RepositoryLinkCreate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> RepositoryLinkRead:
    document = _validate_document(
        db, principal.tenant_id, project.id, payload.document_id
    )
    item = RepositoryLink(
        tenant_id=principal.tenant_id,
        project_id=project.id,
        document_id=payload.document_id,
        repository=payload.repository,
        path=payload.path,
        sync_status=payload.sync_status,
    )
    db.add(item)
    db.flush()
    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="RepositoryLink",
        entity_id=item.id,
        action="created",
        details={
            "document_number": document.number,
            "repository": item.repository.value,
            "path": item.path,
        },
    )
    db.commit()
    db.refresh(item)
    return RepositoryLinkRead.model_validate(item)


@router.patch("/repository-links/{link_id}", response_model=RepositoryLinkRead)
def update_repository_link(
    link_id: str,
    payload: RepositoryLinkUpdate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> RepositoryLinkRead:
    item = (
        db.query(RepositoryLink)
        .filter(
            RepositoryLink.id == link_id,
            RepositoryLink.project_id == project.id,
            RepositoryLink.tenant_id == principal.tenant_id,
        )
        .first()
    )
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Repository link not found."
        )
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(item, field, value)
    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="RepositoryLink",
        entity_id=item.id,
        action="updated",
        details=data,
    )
    db.commit()
    db.refresh(item)
    return RepositoryLinkRead.model_validate(item)


# ---------------------------------------------------------------------------
# Rollup
# ---------------------------------------------------------------------------


@router.get("/summary", response_model=DocumentControlSummary)
def document_control_summary(
    project: Project = Depends(get_project_for_view),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> DocumentControlSummary:
    documents = (
        db.query(ControlledDocument)
        .filter(
            ControlledDocument.project_id == project.id,
            ControlledDocument.tenant_id == principal.tenant_id,
        )
        .all()
    )
    reviews = (
        db.query(DocumentReview)
        .filter(
            DocumentReview.project_id == project.id,
            DocumentReview.tenant_id == principal.tenant_id,
        )
        .all()
    )
    transmittals = (
        db.query(TransmittalRecord)
        .filter(
            TransmittalRecord.project_id == project.id,
            TransmittalRecord.tenant_id == principal.tenant_id,
        )
        .all()
    )
    links = (
        db.query(RepositoryLink)
        .filter(
            RepositoryLink.project_id == project.id,
            RepositoryLink.tenant_id == principal.tenant_id,
        )
        .all()
    )

    avg_metadata = (
        round(sum(d.metadata_pct for d in documents) / len(documents))
        if documents
        else 0
    )

    return DocumentControlSummary(
        project_id=project.id,
        document_count=len(documents),
        review_count=len(reviews),
        transmittal_count=len(transmittals),
        repository_link_count=len(links),
        average_metadata_pct=avg_metadata,
        overdue_document_count=sum(
            1 for d in documents if d.workflow_status == DocumentWorkflowStatus.overdue
        ),
        published_document_count=sum(
            1
            for d in documents
            if d.workflow_status
            in {DocumentWorkflowStatus.published, DocumentWorkflowStatus.accepted}
        ),
        pending_review_count=sum(
            1
            for r in reviews
            if r.status in {ReviewStatus.pending, ReviewStatus.in_review}
        ),
        sync_issue_count=sum(
            1
            for link in links
            if link.sync_status in {SyncStatus.pending_sync, SyncStatus.out_of_sync}
        ),
        issued_transmittal_count=sum(
            1
            for t in transmittals
            if t.status in {TransmittalStatus.issued, TransmittalStatus.acknowledged}
        ),
    )
