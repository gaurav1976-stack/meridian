"""Project-setup CRUD: contracts, numbering rules, metadata fields, workflows.

These are tenant-admin / programme-director surfaces — view is allowed for any
project member, edit is gated through `get_project_for_edit`.
"""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import CurrentPrincipal, get_current_principal, get_project_for_edit, get_project_for_view
from app.db.session import get_db
from app.models.core import Project
from app.models.project_setup import Contract, MetadataFieldDefinition, NumberingRule, WorkflowDefinition
from app.schemas.project_setup import (
    ContractCreate,
    ContractRead,
    ContractUpdate,
    MetadataFieldCreate,
    MetadataFieldRead,
    NumberingRuleCreate,
    NumberingRuleRead,
    WorkflowCreate,
    WorkflowRead,
)
from app.services.audit import write_audit_log

router = APIRouter(prefix="/projects/{project_id}/setup")


# ---------------------------------------------------------------------------
# Contracts
# ---------------------------------------------------------------------------


@router.get("/contracts", response_model=List[ContractRead])
def list_contracts(
    project: Project = Depends(get_project_for_view),
    db: Session = Depends(get_db),
) -> List[ContractRead]:
    rows = (
        db.query(Contract)
        .filter(Contract.project_id == project.id)
        .order_by(Contract.reference)
        .all()
    )
    return [ContractRead.model_validate(r) for r in rows]


@router.post("/contracts", response_model=ContractRead, status_code=status.HTTP_201_CREATED)
def create_contract(
    payload: ContractCreate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> ContractRead:
    duplicate = (
        db.query(Contract)
        .filter(Contract.project_id == project.id, Contract.reference == payload.reference)
        .first()
    )
    if duplicate is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Contract reference '{payload.reference}' already exists in this project.",
        )
    contract = Contract(
        tenant_id=principal.tenant_id, project_id=project.id, **payload.model_dump()
    )
    db.add(contract)
    db.flush()
    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="Contract",
        entity_id=contract.id,
        action="created",
        details=payload.model_dump(),
    )
    db.commit()
    db.refresh(contract)
    return ContractRead.model_validate(contract)


@router.patch("/contracts/{contract_id}", response_model=ContractRead)
def update_contract(
    contract_id: str,
    payload: ContractUpdate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> ContractRead:
    contract = (
        db.query(Contract)
        .filter(Contract.id == contract_id, Contract.project_id == project.id)
        .first()
    )
    if contract is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found.")
    changes = payload.model_dump(exclude_unset=True)
    for key, value in changes.items():
        setattr(contract, key, value)
    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="Contract",
        entity_id=contract.id,
        action="updated",
        details=changes,
    )
    db.commit()
    db.refresh(contract)
    return ContractRead.model_validate(contract)


# ---------------------------------------------------------------------------
# Numbering rules
# ---------------------------------------------------------------------------


@router.get("/numbering", response_model=List[NumberingRuleRead])
def list_numbering(
    project: Project = Depends(get_project_for_view),
    db: Session = Depends(get_db),
) -> List[NumberingRuleRead]:
    rows = (
        db.query(NumberingRule)
        .filter(NumberingRule.project_id == project.id)
        .order_by(NumberingRule.entity)
        .all()
    )
    return [NumberingRuleRead.model_validate(r) for r in rows]


@router.post("/numbering", response_model=NumberingRuleRead, status_code=status.HTTP_201_CREATED)
def create_numbering_rule(
    payload: NumberingRuleCreate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> NumberingRuleRead:
    rule = NumberingRule(
        tenant_id=principal.tenant_id, project_id=project.id, **payload.model_dump()
    )
    db.add(rule)
    db.flush()
    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="NumberingRule",
        entity_id=rule.id,
        action="created",
        details=payload.model_dump(),
    )
    db.commit()
    db.refresh(rule)
    return NumberingRuleRead.model_validate(rule)


# ---------------------------------------------------------------------------
# Metadata fields
# ---------------------------------------------------------------------------


@router.get("/metadata-fields", response_model=List[MetadataFieldRead])
def list_metadata_fields(
    project: Project = Depends(get_project_for_view),
    db: Session = Depends(get_db),
) -> List[MetadataFieldRead]:
    rows = (
        db.query(MetadataFieldDefinition)
        .filter(MetadataFieldDefinition.project_id == project.id)
        .order_by(MetadataFieldDefinition.entity, MetadataFieldDefinition.field_key)
        .all()
    )
    return [MetadataFieldRead.model_validate(r) for r in rows]


@router.post("/metadata-fields", response_model=MetadataFieldRead, status_code=status.HTTP_201_CREATED)
def create_metadata_field(
    payload: MetadataFieldCreate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> MetadataFieldRead:
    field = MetadataFieldDefinition(
        tenant_id=principal.tenant_id, project_id=project.id, **payload.model_dump()
    )
    db.add(field)
    db.flush()
    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="MetadataFieldDefinition",
        entity_id=field.id,
        action="created",
        details=payload.model_dump(),
    )
    db.commit()
    db.refresh(field)
    return MetadataFieldRead.model_validate(field)


# ---------------------------------------------------------------------------
# Workflows
# ---------------------------------------------------------------------------


@router.get("/workflows", response_model=List[WorkflowRead])
def list_workflows(
    project: Project = Depends(get_project_for_view),
    db: Session = Depends(get_db),
) -> List[WorkflowRead]:
    rows = (
        db.query(WorkflowDefinition)
        .filter(WorkflowDefinition.project_id == project.id)
        .order_by(WorkflowDefinition.entity, WorkflowDefinition.name)
        .all()
    )
    return [WorkflowRead.model_validate(r) for r in rows]


@router.post("/workflows", response_model=WorkflowRead, status_code=status.HTTP_201_CREATED)
def create_workflow(
    payload: WorkflowCreate,
    project: Project = Depends(get_project_for_edit),
    db: Session = Depends(get_db),
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> WorkflowRead:
    workflow = WorkflowDefinition(
        tenant_id=principal.tenant_id, project_id=project.id, **payload.model_dump()
    )
    db.add(workflow)
    db.flush()
    write_audit_log(
        db,
        tenant_id=principal.tenant_id,
        actor_user_id=principal.user_id,
        entity_type="WorkflowDefinition",
        entity_id=workflow.id,
        action="created",
        details=payload.model_dump(),
    )
    db.commit()
    db.refresh(workflow)
    return WorkflowRead.model_validate(workflow)
