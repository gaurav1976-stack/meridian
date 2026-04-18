"""Project-setup domain schemas: contracts, numbering, metadata, workflow."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from app.models.enums import ContractForm, ContractStatus
from app.schemas.common import TimestampedOrm


# ----- Contracts -----


class ContractCreate(BaseModel):
    reference: str = Field(min_length=1, max_length=80)
    title: str = Field(min_length=1, max_length=255)
    contractor: Optional[str] = None
    form: ContractForm = ContractForm.nec4_ecc
    status: ContractStatus = ContractStatus.draft
    value_amount: Optional[float] = None
    value_currency: Optional[str] = None
    notes: Optional[str] = None


class ContractUpdate(BaseModel):
    title: Optional[str] = None
    contractor: Optional[str] = None
    form: Optional[ContractForm] = None
    status: Optional[ContractStatus] = None
    value_amount: Optional[float] = None
    value_currency: Optional[str] = None
    notes: Optional[str] = None


class ContractRead(TimestampedOrm):
    id: str
    project_id: str
    tenant_id: str
    reference: str
    title: str
    contractor: Optional[str]
    form: ContractForm
    status: ContractStatus
    value_amount: Optional[float]
    value_currency: Optional[str]
    notes: Optional[str]


# ----- Numbering -----


class NumberingRuleCreate(BaseModel):
    entity: str
    pattern: str
    next_sequence: int = 1
    notes: Optional[str] = None


class NumberingRuleRead(TimestampedOrm):
    id: str
    project_id: str
    tenant_id: str
    entity: str
    pattern: str
    next_sequence: int
    notes: Optional[str]


# ----- Metadata fields -----


class MetadataFieldCreate(BaseModel):
    entity: str
    field_key: str
    label: str
    field_type: str = "text"
    is_required: bool = False
    options_csv: Optional[str] = None


class MetadataFieldRead(TimestampedOrm):
    id: str
    project_id: str
    tenant_id: str
    entity: str
    field_key: str
    label: str
    field_type: str
    is_required: bool
    options_csv: Optional[str]


# ----- Workflow -----


class WorkflowCreate(BaseModel):
    entity: str
    name: str
    approval_mode: str = "Sequential"
    states_csv: str
    notes: Optional[str] = None


class WorkflowRead(TimestampedOrm):
    id: str
    project_id: str
    tenant_id: str
    entity: str
    name: str
    approval_mode: str
    states_csv: str
    notes: Optional[str]
