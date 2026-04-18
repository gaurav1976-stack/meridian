"""All Meridian enumerations in one place.

Consolidated from the 12 Track A files where each redeclared its own. Importing
here means every router, schema, and service refers to the same enum class
identity (so `isinstance(x, RiskStatus)` actually works across modules).
"""
from __future__ import annotations

from enum import Enum


# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------


class ProjectStatus(str, Enum):
    active = "Active"
    planned = "Planned"
    on_hold = "On Hold"
    closed = "Closed"


class UserRole(str, Enum):
    super_admin = "Super Admin"
    tenant_admin = "Tenant Admin"
    programme_director = "Programme Director"
    pmo_director = "PMO Director"
    project_director = "Project Director"
    controls_manager = "Controls Manager"
    document_controller = "Document Controller"
    design_manager = "Design Manager"
    commercial_manager = "Commercial Manager"
    risk_manager = "Risk Manager"
    orat_manager = "ORAT Manager"
    package_manager = "Package Manager"
    reviewer_approver = "Reviewer / Approver"
    external_consultant = "External Consultant"
    contractor_user = "Contractor User"
    viewer = "Viewer"


# ---------------------------------------------------------------------------
# Project setup (Module 02)
# ---------------------------------------------------------------------------


class PackageType(str, Enum):
    civil = "Civil"
    structural = "Structural"
    mep = "MEP"
    facade = "Facade"
    interiors = "Interiors"
    landside = "Landside"
    airside = "Airside"
    bhs = "BHS"
    ict = "ICT / Systems"
    security = "Security"
    other = "Other"


class PackageStatus(str, Enum):
    planned = "Planned"
    active = "Active"
    on_hold = "On Hold"
    completed = "Completed"


class ContractForm(str, Enum):
    nec4_ecc = "NEC4 ECC"
    nec4_psc = "NEC4 PSC"
    nec4_tsc = "NEC4 TSC"
    fidic_red = "FIDIC Red Book"
    fidic_yellow = "FIDIC Yellow Book"
    fidic_silver = "FIDIC Silver Book"
    jct = "JCT"
    bespoke = "Bespoke"


class ContractStatus(str, Enum):
    draft = "Draft"
    awarded = "Awarded"
    active = "Active"
    completed = "Completed"
    closed = "Closed"


# ---------------------------------------------------------------------------
# Schedule (Module 03)
# ---------------------------------------------------------------------------


class ActivityStatus(str, Enum):
    not_started = "Not Started"
    in_progress = "In Progress"
    completed = "Completed"
    on_hold = "On Hold"


class DependencyType(str, Enum):
    fs = "FS"  # finish-to-start
    ss = "SS"
    ff = "FF"
    sf = "SF"


class ScheduleScenario(str, Enum):
    baseline = "Baseline"
    forecast = "Forecast"
    actual = "Actual"
    mitigation = "Mitigation"


class ScheduleFileCategory(str, Enum):
    programme_master = "Programme Master"
    project_master = "Project Master"
    contractor_baseline = "Contractor Baseline"
    contractor_update = "Contractor Update"
    package = "Package"
    authority = "Authority / Approval"
    look_ahead = "Look-Ahead"
    mitigation = "Mitigation / Recovery"


class ScheduleFileStatus(str, Enum):
    draft = "Draft"
    issued = "Issued"
    archived = "Archived"


# ---------------------------------------------------------------------------
# Risk (Module 05)
# ---------------------------------------------------------------------------


class RiskCategory(str, Enum):
    technical = "Technical"
    commercial = "Commercial"
    programme = "Programme"
    regulatory = "Regulatory / Political"
    operational = "Operational"
    force_majeure = "Force Majeure"


class RiskStatus(str, Enum):
    identified = "Identified"
    assessed = "Assessed"
    mitigating = "Mitigating"
    monitoring = "Monitoring"
    closed = "Closed"


class OpportunityStatus(str, Enum):
    identified = "Identified"
    pursuing = "Pursuing"
    realised = "Realised"
    declined = "Declined"


# ---------------------------------------------------------------------------
# Stage Gate Governance (Module 04)
# ---------------------------------------------------------------------------


class GateStatus(str, Enum):
    complete = "Complete"
    active = "Active"
    upcoming = "Upcoming"
    blocked = "Blocked"


class EvidenceCategory(str, Enum):
    strategy = "Strategy"
    commercial = "Commercial"
    design = "Design"
    controls = "Controls"
    readiness = "Readiness"
    authority = "Authority"


class EvidenceStatus(str, Enum):
    missing = "Missing"
    draft = "Draft"
    submitted = "Submitted"
    accepted = "Accepted"


class ApprovalStatus(str, Enum):
    pending = "Pending"
    approved = "Approved"
    rejected = "Rejected"


class DecisionOutcome(str, Enum):
    proceed = "Proceed"
    proceed_with_conditions = "Proceed with Conditions"
    hold = "Hold"
    rejected = "Rejected"


# ---------------------------------------------------------------------------
# Commercial / Change Control (Module 06)
# ---------------------------------------------------------------------------


class ChangeType(str, Enum):
    compensation_event = "Compensation Event"
    variation = "Variation"
    client_change = "Client Change"
    authority_change = "Authority Change"
    claim = "Claim"


class ChangeStatus(str, Enum):
    identified = "Identified"
    notified = "Notified"
    quoted = "Quoted"
    approved = "Approved"
    rejected = "Rejected"
    implemented = "Implemented"


class EntitlementStrength(str, Enum):
    strong = "Strong"
    moderate = "Moderate"
    weak = "Weak"


class NoticeKind(str, Enum):
    ewn = "EWN"
    notice = "Notice"
    ce_notification = "CE Notification"
    claim_notice = "Claim Notice"


class NoticeStatus(str, Enum):
    open = "Open"
    issued = "Issued"
    overdue = "Overdue"
    closed = "Closed"


# ---------------------------------------------------------------------------
# Design Management (Module 07)
# ---------------------------------------------------------------------------


class RibaStage(str, Enum):
    stage_0 = "0"
    stage_1 = "1"
    stage_2 = "2"
    stage_3 = "3"
    stage_4 = "4"
    stage_5 = "5"
    stage_6 = "6"


class DesignPackageStatus(str, Enum):
    draft = "Draft"
    in_review = "In Review"
    coordinating = "Coordinating"
    ready_for_issue = "Ready for Issue"
    frozen = "Frozen"


class DeliverableType(str, Enum):
    drawing = "Drawing"
    report = "Report"
    calculation = "Calculation"
    specification = "Specification"
    schedule = "Schedule"


class DeliverableStatus(str, Enum):
    wip = "WIP"
    shared = "Shared"
    published = "Published"
    accepted = "Accepted"
    overdue = "Overdue"


class InterfaceStatus(str, Enum):
    open = "Open"
    assigned = "Assigned"
    resolving = "Resolving"
    closed = "Closed"
    escalated = "Escalated"


class ModelShareStatus(str, Enum):
    wip = "WIP"
    shared = "Shared"
    published = "Published"


# ---------------------------------------------------------------------------
# Document Control (Module 08)
# ---------------------------------------------------------------------------


class DocumentType(str, Enum):
    drawing = "Drawing"
    report = "Report"
    calculation = "Calculation"
    specification = "Specification"
    letter = "Letter"
    transmittal = "Transmittal"
    procedure = "Procedure"


class DocumentWorkflowStatus(str, Enum):
    """ISO 19650 workflow status over the document lifecycle."""

    wip = "WIP"
    shared = "Shared"
    published = "Published"
    accepted = "Accepted"
    archived = "Archived"
    overdue = "Overdue"


class CdeStage(str, Enum):
    """Common Data Environment hierarchy per ISO 19650."""

    wip = "WIP"
    shared = "Shared"
    published = "Published"
    archived = "Archived"


class ReviewStatus(str, Enum):
    pending = "Pending"
    in_review = "In Review"
    approved = "Approved"
    rejected = "Rejected"


class RepositorySource(str, Enum):
    meridian = "Meridian"
    bim360 = "BIM360"
    sharepoint = "SharePoint"


class TransmittalStatus(str, Enum):
    draft = "Draft"
    issued = "Issued"
    acknowledged = "Acknowledged"
    returned = "Returned"


class SyncStatus(str, Enum):
    linked = "Linked"
    pending_sync = "Pending Sync"
    out_of_sync = "Out of Sync"


# ---------------------------------------------------------------------------
# Meetings, Actions & Compliance (Module 09)
# ---------------------------------------------------------------------------


class MeetingType(str, Enum):
    governance_board = "Governance Board"
    package_review = "Package Review"
    design_review = "Design Review"
    commercial_review = "Commercial Review"
    orat_review = "ORAT Review"
    coordination = "Coordination"


class LinkedModule(str, Enum):
    """Primary upstream module a meeting ties back to."""

    gate = "Gate"
    risk = "Risk"
    document = "Document"
    commercial = "Commercial"
    programme = "Programme"
    orat = "ORAT"


class ActionSourceType(str, Enum):
    """Upstream artefact that spawned the action item."""

    meeting = "Meeting"
    gate = "Gate"
    risk = "Risk"
    document = "Document"
    commercial = "Commercial"
    orat = "ORAT"


class ActionPriority(str, Enum):
    critical = "Critical"
    high = "High"
    medium = "Medium"
    low = "Low"


class ActionStatus(str, Enum):
    open = "Open"
    in_progress = "In Progress"
    awaiting_review = "Awaiting Review"
    closed = "Closed"
    overdue = "Overdue"


class ComplianceDomain(str, Enum):
    governance = "Governance"
    document_control = "Document Control"
    commercial = "Commercial"
    design = "Design"
    orat = "ORAT"
    programme = "Programme"


class ComplianceStatus(str, Enum):
    open = "Open"
    in_progress = "In Progress"
    compliant = "Compliant"
    non_compliant = "Non-Compliant"
    overdue = "Overdue"


# ---------------------------------------------------------------------------
# ORAT Readiness (Module 10)
# ---------------------------------------------------------------------------


class OratWorkstreamStatus(str, Enum):
    not_started = "Not Started"
    in_progress = "In Progress"
    at_risk = "At Risk"
    ready = "Ready"


class TrialStatus(str, Enum):
    planned = "Planned"
    prepared = "Prepared"
    executed = "Executed"
    passed = "Passed"
    failed = "Failed"


class TrainingStatus(str, Enum):
    not_started = "Not Started"
    scheduled = "Scheduled"
    in_delivery = "In Delivery"
    complete = "Complete"


class HandoverStatus(str, Enum):
    pending = "Pending"
    in_verification = "In Verification"
    accepted = "Accepted"
    blocked = "Blocked"


# ---------------------------------------------------------------------------
# Reporting & Export (Module 11)
# ---------------------------------------------------------------------------


class ReportFormat(str, Enum):
    pdf = "PDF"
    excel = "Excel"
    pdf_excel = "PDF + Excel"


class ReportTemplateType(str, Enum):
    """Template archetypes for the reporting suite. Each maps to a distinct
    consumer audience (Board, PMO, Governance, etc.) and dictates the section
    catalogue that the export job assembles.
    """

    board_pack = "Board Pack"
    monthly_pmo = "Monthly PMO Report"
    gate_pack = "Gate Evidence Pack"
    risk_report = "Risk Report"
    commercial_summary = "Commercial Summary"
    document_control = "Document Control Report"
    orat_pack = "ORAT Readiness Pack"


class ExportJobStatus(str, Enum):
    """Lifecycle of an export job from authoring to artefact availability."""

    draft = "Draft"
    queued = "Queued"
    generating = "Generating"
    ready = "Ready"
    failed = "Failed"


# ---------------------------------------------------------------------------
# Enterprise Search & Retrieval (Module 12)
# ---------------------------------------------------------------------------


class SearchEntityType(str, Enum):
    """Top-level entity classes the unified search index covers.

    Mirrors the Meridian module taxonomy — every domain that can surface a
    discoverable artefact registers under one of these. Adding a new module
    will normally extend this enumeration first.
    """

    project = "Project"
    schedule = "Schedule"
    gate = "Gate"
    risk = "Risk"
    commercial = "Commercial"
    design = "Design"
    document = "Document"
    action = "Action"
    orat = "ORAT"
    repository = "Repository"
    report = "Report"


class SearchSource(str, Enum):
    """Origin system that holds the authoritative copy of the indexed record."""

    meridian = "Meridian"
    bim360 = "BIM360"
    sharepoint = "SharePoint"
    teams = "Teams"


class SearchGroup(str, Enum):
    """Coarse grouping used by the search UI to bucket results into facets.

    Maps several entity types into a single user-facing column so the result
    panel does not fragment into 11 thin lanes.
    """

    core = "Core"
    delivery = "Delivery"
    governance = "Governance"
    commercial = "Commercial"
    technical = "Technical"
    operations = "Operations"
    outputs = "Outputs"


class SavedSearchScope(str, Enum):
    """Whether a saved search runs across everything, a module, or only the
    repository / connector surface."""

    all = "All"
    module_specific = "Module Specific"
    repository_only = "Repository Only"


class ConnectorSyncStatus(str, Enum):
    """Health state of a connector-backed reference.

    `indexed` rows are searchable and current; `pending` are queued for the
    next ingestion pass; `stale` flag drift between source and index; `failed`
    rows surfaced an error during the most recent attempt.
    """

    indexed = "Indexed"
    pending = "Pending"
    stale = "Stale"
    failed = "Failed"
