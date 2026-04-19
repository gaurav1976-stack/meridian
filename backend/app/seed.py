"""Idempotent seed — rich demo data across all 13 Meridian modules.

Creates 1 tenant, 1 admin, 2 projects (ZNZ-T1 active, DXB-T3 planned),
plus full data for schedule, risks, governance, commercial, design,
documents, meetings, ORAT, reporting, and search.

Re-run safely — uses get-or-create per row.

Meridian Airport PMO suite
(c) GV Softwares. Developed by Gaurav Vatsa. All rights reserved.
Proprietary — unauthorised copying, distribution, modification or use prohibited.
"""
from __future__ import annotations

from datetime import date, timedelta
from uuid import uuid4

from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models import (  # noqa: F401
    ActionItem,
    ArchiveRecord,
    AuditLog,
    BimCoordinationItem,
    CommercialChangeItem,
    CommercialNoticeItem,
    ComplianceItem,
    ConnectorReference,
    Contract,
    ControlledDocument,
    DesignDeliverable,
    DesignInterfaceItem,
    DesignPackage,
    DocumentReview,
    ExportJob,
    GateApproval,
    GateDecision,
    GateDefinition,
    GateEvidenceItem,
    GatePackageLink,
    HandoverItem,
    MeetingRecord,
    OpportunityItem,
    OratTrial,
    OratWorkstream,
    PackageCostControl,
    Project,
    ProjectMembership,
    RepositoryLink,
    ReportTemplate,
    RiskItem,
    SavedSearch,
    ScheduleActivity,
    ScheduleFile,
    SearchIndexRecord,
    Tenant,
    TrainingGroup,
    TransmittalRecord,
    User,
    WorkPackage,
)
from app.models.enums import (
    ActionPriority,
    ActionSourceType,
    ActionStatus,
    ActivityStatus,
    ApprovalStatus,
    ChangeStatus,
    ChangeType,
    CdeStage,
    ComplianceDomain,
    ComplianceStatus,
    ConnectorSyncStatus,
    ContractForm,
    ContractStatus,
    DecisionOutcome,
    DeliverableStatus,
    DeliverableType,
    DesignPackageStatus,
    DocumentType,
    DocumentWorkflowStatus,
    EntitlementStrength,
    EvidenceCategory,
    EvidenceStatus,
    ExportJobStatus,
    GateStatus,
    HandoverStatus,
    InterfaceStatus,
    LinkedModule,
    MeetingType,
    ModelShareStatus,
    NoticeKind,
    NoticeStatus,
    OratWorkstreamStatus,
    PackageStatus,
    PackageType,
    ProjectStatus,
    ReportFormat,
    ReportTemplateType,
    RepositorySource,
    ReviewStatus,
    RibaStage,
    RiskCategory,
    RiskStatus,
    SavedSearchScope,
    ScheduleFileCategory,
    ScheduleFileStatus,
    SearchEntityType,
    SearchGroup,
    SearchSource,
    SyncStatus,
    TrainingStatus,
    TransmittalStatus,
    TrialStatus,
    UserRole,
)


def _get_or_create(db: Session, model, defaults: dict | None = None, **filters):
    obj = db.query(model).filter_by(**filters).first()
    if obj is not None:
        return obj, False
    params = {**filters, **(defaults or {})}
    obj = model(**params)
    db.add(obj)
    db.flush()
    return obj, True


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _d(offset: int) -> date:
    """Return today + offset days."""
    return date.today() + timedelta(days=offset)


def _uid() -> str:
    return str(uuid4())


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        # ------------------------------------------------------------------ tenant / users
        tenant, _ = _get_or_create(
            db, Tenant,
            defaults={"id": _uid(), "region": "EMEA"},
            name="Meridian Demo Tenant",
        )

        admin, _ = _get_or_create(
            db, User,
            defaults={"id": _uid(), "tenant_id": tenant.id, "name": "Demo Admin",
                      "role": UserRole.tenant_admin},
            email="admin@meridian.local",
        )

        # ------------------------------------------------------------------ project 1: ZNZ-T1 (active)
        project, project_created = _get_or_create(
            db, Project,
            defaults={
                "id": _uid(),
                "name": "Zanzibar International Airport — Terminal Expansion",
                "location": "Zanzibar, Tanzania",
                "status": ProjectStatus.active,
                "stage": "G3 Detailed Design",
                "description": (
                    "New 45,000 m² international terminal to handle 4 million passengers per annum. "
                    "Includes airside concourse, landside forecourt, BHS, and full MEP fit-out."
                ),
            },
            tenant_id=tenant.id, code="ZNZ-T1",
        )

        _get_or_create(
            db, ProjectMembership,
            defaults={"id": _uid(), "tenant_id": tenant.id, "role": UserRole.tenant_admin},
            project_id=project.id, user_id=admin.id,
        )

        # ------------------------------------------------------------------ project 2: DXB-T3 (planned)
        project2, _ = _get_or_create(
            db, Project,
            defaults={
                "id": _uid(),
                "name": "Dubai International — Concourse D Upgrade",
                "location": "Dubai, UAE",
                "status": ProjectStatus.planned,
                "stage": "G1 Feasibility",
                "description": "Upgrade of Concourse D to increase capacity by 8 million passengers per annum.",
            },
            tenant_id=tenant.id, code="DXB-T3",
        )

        # ------------------------------------------------------------------ work packages
        wp_str, _ = _get_or_create(
            db, WorkPackage,
            defaults={"id": _uid(), "tenant_id": tenant.id, "name": "Terminal Substructure",
                      "package_type": PackageType.structural.value, "status": PackageStatus.active.value},
            project_id=project.id, code="WP-STR-01",
        )
        wp_mep, _ = _get_or_create(
            db, WorkPackage,
            defaults={"id": _uid(), "tenant_id": tenant.id, "name": "MEP Services",
                      "package_type": PackageType.mep.value, "status": PackageStatus.active.value},
            project_id=project.id, code="WP-MEP-02",
        )
        wp_facade, _ = _get_or_create(
            db, WorkPackage,
            defaults={"id": _uid(), "tenant_id": tenant.id, "name": "Facade & Roof",
                      "package_type": PackageType.facade.value, "status": PackageStatus.planned.value},
            project_id=project.id, code="WP-FAC-03",
        )
        wp_bhs, _ = _get_or_create(
            db, WorkPackage,
            defaults={"id": _uid(), "tenant_id": tenant.id, "name": "Baggage Handling System",
                      "package_type": PackageType.bhs.value, "status": PackageStatus.planned.value},
            project_id=project.id, code="WP-BHS-04",
        )

        # ------------------------------------------------------------------ contracts
        _get_or_create(
            db, Contract,
            defaults={"id": _uid(), "tenant_id": tenant.id, "title": "Main Works Contract",
                      "contractor": "Mwanza Construction Ltd.", "form": ContractForm.nec4_ecc,
                      "status": ContractStatus.active, "value_amount": 245_000_000, "value_currency": "USD"},
            project_id=project.id, reference="C-001",
        )
        _get_or_create(
            db, Contract,
            defaults={"id": _uid(), "tenant_id": tenant.id, "title": "Lead Designer (PSC)",
                      "contractor": "Skyline Architects LLP", "form": ContractForm.nec4_psc,
                      "status": ContractStatus.active, "value_amount": 18_500_000, "value_currency": "USD"},
            project_id=project.id, reference="C-002",
        )
        _get_or_create(
            db, Contract,
            defaults={"id": _uid(), "tenant_id": tenant.id, "title": "MEP Specialist Works",
                      "contractor": "Gulf Electro-Mechanical Co.", "form": ContractForm.nec4_ecc,
                      "status": ContractStatus.active, "value_amount": 42_000_000, "value_currency": "USD"},
            project_id=project.id, reference="C-003",
        )

        # ------------------------------------------------------------------ schedule
        sf, _ = _get_or_create(
            db, ScheduleFile,
            defaults={"id": _uid(), "tenant_id": tenant.id,
                      "category": ScheduleFileCategory.programme_master,
                      "status": ScheduleFileStatus.issued, "revision": "R4",
                      "issued_date": _d(-14)},
            project_id=project.id, title="Programme Master Schedule R4",
        )

        schedule_rows = [
            # (ext_id, name, days_start, days_dur, is_critical, float, pct)
            ("A1000", "Site Establishment & Mobilisation",    -60, 30, False, 25, 100),
            ("A1010", "Enabling Works & Demolition",          -30, 28, False, 18,  80),
            ("A1020", "Piling — Zone A (Apron Side)",         -10, 45, True,   0,  40),
            ("A1030", "Piling — Zone B (Landside)",            10, 45, True,   0,   0),
            ("A1040", "Pile Cap Construction — Zone A",        40, 35, True,   0,   0),
            ("A1050", "Pile Cap Construction — Zone B",        60, 35, True,   0,   0),
            ("A1060", "Ground Beams & Slab — Zone A",          80, 40, True,   0,   0),
            ("A1070", "Structural Steel Frame — Level 1",     120, 50, True,   0,   0),
            ("A1080", "Structural Steel Frame — Level 2",     175, 50, True,   0,   0),
            ("A1090", "Roof Structure",                       230, 60, True,   0,   0),
            ("A2000", "MEP Rough-In — Level 1",               160, 55, False,  8,   0),
            ("A2010", "MEP Rough-In — Level 2",               220, 55, False,  8,   0),
            ("A2020", "BHS Installation — Zone A",            200, 70, False, 12,   0),
            ("A2030", "Facade Installation",                  240, 80, False,  5,   0),
            ("A3000", "Interior Fit-Out — Departures",        300, 90, False, 10,   0),
            ("A3010", "Interior Fit-Out — Arrivals",          320, 90, False, 10,   0),
            ("A4000", "Systems Integration & Testing",        390, 45, True,   0,   0),
            ("A4010", "ORAT Trials Phase 1",                  440, 30, True,   0,   0),
            ("A4020", "ORAT Trials Phase 2",                  475, 30, True,   0,   0),
            ("A5000", "Commissioning & Handover",             510, 30, True,   0,   0),
        ]

        for ext_id, name, ds, dur, crit, flt, pct in schedule_rows:
            status = (ActivityStatus.completed if pct == 100
                      else ActivityStatus.in_progress if pct > 0
                      else ActivityStatus.not_started)
            _get_or_create(
                db, ScheduleActivity,
                defaults={
                    "id": _uid(), "tenant_id": tenant.id,
                    "schedule_file_id": sf.id,
                    "package_id": wp_str.id if "Piling" in name or "Pile" in name or "Slab" in name or "Steel" in name or "Roof" in name or "Establish" in name or "Enabling" in name else wp_mep.id if "MEP" in name or "BHS" in name or "Systems" in name else wp_facade.id if "Facade" in name else wp_bhs.id if "ORAT" in name or "Commission" in name else wp_str.id,
                    "name": name,
                    "status": status,
                    "planned_start": _d(ds),
                    "planned_finish": _d(ds + dur),
                    "duration_days": dur,
                    "total_float_days": flt,
                    "is_critical": crit,
                    "percent_complete": pct,
                },
                project_id=project.id, activity_id_external=ext_id,
            )

        # ------------------------------------------------------------------ risks
        risk_rows = [
            ("R-001", "Piling refusal due to unforeseen rock strata",       RiskCategory.technical,    3, 4, RiskStatus.mitigating),
            ("R-002", "Late issue of MEP detail design drawings",            RiskCategory.programme,    4, 4, RiskStatus.assessed),
            ("R-003", "CAA aerodrome certification delay",                   RiskCategory.regulatory,   2, 5, RiskStatus.assessed),
            ("R-004", "Steel supply chain disruption — global shortage",     RiskCategory.commercial,   3, 5, RiskStatus.mitigating),
            ("R-005", "Groundwater ingress during substructure works",       RiskCategory.technical,    2, 4, RiskStatus.monitoring),
            ("R-006", "Contractor insolvency — Main Works",                  RiskCategory.commercial,   1, 5, RiskStatus.identified),
            ("R-007", "BHS vendor delivery programme slip",                  RiskCategory.programme,    3, 3, RiskStatus.assessed),
            ("R-008", "Airside access restrictions during peak season",      RiskCategory.operational,  4, 3, RiskStatus.mitigating),
            ("R-009", "Design freeze slippage — MEP coordination",          RiskCategory.programme,    4, 4, RiskStatus.assessed),
            ("R-010", "Force majeure — tropical storm season",               RiskCategory.force_majeure,2, 4, RiskStatus.monitoring),
        ]

        for code, title, cat, l, i, st in risk_rows:
            _get_or_create(
                db, RiskItem,
                defaults={"id": _uid(), "tenant_id": tenant.id, "title": title,
                          "category": cat, "status": st, "likelihood": l, "impact": i,
                          "owner": "Risk Manager", "target_closure_date": _d(120)},
                project_id=project.id, code=code,
            )

        for code, title, l, b in [
            ("O-001", "Modular pile cap design — value engineering saving",  3, 4),
            ("O-002", "Early procurement of steel — lock in current rates",  4, 3),
            ("O-003", "Accelerated piling programme — 3-week programme gain",2, 5),
        ]:
            _get_or_create(
                db, OpportunityItem,
                defaults={"id": _uid(), "tenant_id": tenant.id, "title": title,
                          "likelihood": l, "benefit": b, "owner": "Design Manager"},
                project_id=project.id, code=code,
            )

        # ------------------------------------------------------------------ stage gates
        gate_rows = [
            ("G1", "Feasibility Approval",    "Confirm project viability and secure initial funding.",          6,  GateStatus.complete),
            ("G2", "Concept Design Approval", "Approve concept design and confirm project scope.",              12, GateStatus.complete),
            ("G3", "Detailed Design Approval","Approve detailed design and release for construction.",          18, GateStatus.active),
            ("G4", "Construction Readiness",  "Confirm site readiness and contractor mobilisation.",            24, GateStatus.upcoming),
            ("G5", "Structural Completion",   "Confirm structural works complete and watertight.",              36, GateStatus.upcoming),
            ("G6", "Systems Completion",      "Confirm all MEP and BHS systems installed and tested.",          48, GateStatus.upcoming),
            ("G7", "ORAT Readiness",          "Confirm operational readiness for trial operations.",            54, GateStatus.upcoming),
            ("G8", "Go-Live Approval",        "Final approval for terminal opening to commercial operations.",  60, GateStatus.upcoming),
        ]

        gates = {}
        for code, name, purpose, month, status in gate_rows:
            g, _ = _get_or_create(
                db, GateDefinition,
                defaults={"id": _uid(), "tenant_id": tenant.id, "name": name,
                          "purpose": purpose, "target_month": month, "status": status},
                project_id=project.id, code=code,
            )
            gates[code] = g

        # Evidence for G3 (active gate)
        g3 = gates["G3"]
        evidence_rows = [
            ("Detailed Design Report — Structural",    EvidenceCategory.design,    EvidenceStatus.accepted,  True),
            ("Detailed Design Report — MEP",           EvidenceCategory.design,    EvidenceStatus.submitted, True),
            ("Cost Plan — RIBA Stage 3",               EvidenceCategory.commercial,EvidenceStatus.accepted,  True),
            ("Risk Register — G3 Snapshot",            EvidenceCategory.controls,  EvidenceStatus.accepted,  True),
            ("Programme — Baseline P6 Export",         EvidenceCategory.controls,  EvidenceStatus.submitted, True),
            ("Authority Approval — Planning Consent",  EvidenceCategory.authority, EvidenceStatus.accepted,  True),
            ("BIM Coordination Report",                EvidenceCategory.design,    EvidenceStatus.draft,     True),
            ("Commercial Strategy Sign-Off",           EvidenceCategory.commercial,EvidenceStatus.missing,   True),
        ]
        for title, cat, ev_status, required in evidence_rows:
            _get_or_create(
                db, GateEvidenceItem,
                defaults={"id": _uid(), "tenant_id": tenant.id, "gate_definition_id": g3.id,
                          "package_id": wp_str.id, "category": cat, "required": required,
                          "status": ev_status, "owner": "PMO Director"},
                project_id=project.id, title=title,
            )

        # Approvals for G3
        for approver, role, ap_status in [
            ("Sarah Al-Rashid",  "Programme Director",  ApprovalStatus.approved),
            ("James Okonkwo",    "Commercial Director", ApprovalStatus.approved),
            ("Dr. Amina Yusuf",  "Design Director",     ApprovalStatus.pending),
            ("Tom Whitfield",    "PMO Director",        ApprovalStatus.pending),
        ]:
            _get_or_create(
                db, GateApproval,
                defaults={"id": _uid(), "tenant_id": tenant.id, "gate_definition_id": g3.id,
                          "role": role, "status": ap_status, "response_date": str(_d(-5)) if ap_status == ApprovalStatus.approved else None},
                project_id=project.id, approver=approver,
            )

        # Decision for G2 (complete)
        g2 = gates["G2"]
        _get_or_create(
            db, GateDecision,
            defaults={"id": _uid(), "tenant_id": tenant.id, "gate_definition_id": g2.id,
                      "meeting_ref": "GB-M-012", "decision_date": str(_d(-90)),
                      "outcome": DecisionOutcome.proceed,
                      "summary": "Board approved concept design. Proceed to detailed design stage."},
            project_id=project.id, meeting_ref="GB-M-012",
        )

        # ------------------------------------------------------------------ commercial
        _get_or_create(
            db, PackageCostControl,
            defaults={"id": _uid(), "tenant_id": tenant.id,
                      "budget_minor":    24_500_000_00,
                      "committed_minor": 22_800_000_00,
                      "forecast_minor":  25_100_000_00,
                      "actual_minor":    11_200_000_00,
                      "percent_complete": 44},
            project_id=project.id, package_id=wp_str.id,
        )
        _get_or_create(
            db, PackageCostControl,
            defaults={"id": _uid(), "tenant_id": tenant.id,
                      "budget_minor":    4_200_000_00,
                      "committed_minor": 3_900_000_00,
                      "forecast_minor":  4_350_000_00,
                      "actual_minor":    1_800_000_00,
                      "percent_complete": 38},
            project_id=project.id, package_id=wp_mep.id,
        )
        _get_or_create(
            db, PackageCostControl,
            defaults={"id": _uid(), "tenant_id": tenant.id,
                      "budget_minor":    3_100_000_00,
                      "committed_minor": 0,
                      "forecast_minor":  3_100_000_00,
                      "actual_minor":    0,
                      "percent_complete": 0},
            project_id=project.id, package_id=wp_facade.id,
        )

        change_rows = [
            ("CE-001", "Unforeseen rock — additional piling works",       ChangeType.compensation_event, ChangeStatus.approved,    EntitlementStrength.strong,   1_250_000_00, 3, "Contractor", "Unforeseen ground conditions per GI report"),
            ("CE-002", "MEP design change — revised duct routing",        ChangeType.compensation_event, ChangeStatus.quoted,      EntitlementStrength.moderate,   380_000_00, 2, "Design Manager", "Client-instructed design change"),
            ("VAR-001","Additional security screening lanes",             ChangeType.client_change,      ChangeStatus.approved,    EntitlementStrength.strong,     920_000_00, 0, "Commercial Manager", "Client requirement post-contract"),
            ("VAR-002","Upgraded passenger boarding bridges",             ChangeType.client_change,      ChangeStatus.notified,    EntitlementStrength.strong,   2_100_000_00, 4, "Commercial Manager", "Airline operator requirement"),
            ("CE-003", "Delayed authority approval — 6-week impact",      ChangeType.compensation_event, ChangeStatus.identified,  EntitlementStrength.moderate,   650_000_00, 6, "PMO Director", "CAA approval delayed beyond programme"),
            ("CLM-001","Prolongation claim — steel delivery delay",       ChangeType.claim,              ChangeStatus.identified,  EntitlementStrength.weak,       480_000_00, 4, "Commercial Manager", "Contractor claim for extended preliminaries"),
        ]
        for ref, title, ctype, cstatus, entitlement, cost, time, owner, cause in change_rows:
            _get_or_create(
                db, CommercialChangeItem,
                defaults={"id": _uid(), "tenant_id": tenant.id, "package_id": wp_str.id,
                          "title": title, "change_type": ctype, "status": cstatus,
                          "cost_impact_minor": cost, "time_impact_weeks": time,
                          "entitlement": entitlement, "owner": owner, "cause": cause},
                project_id=project.id, ref=ref,
            )

        notice_rows = [
            ("EWN-001", "C-001", NoticeKind.ewn,             14, NoticeStatus.issued,  "Commercial Manager"),
            ("EWN-002", "C-001", NoticeKind.ewn,              7, NoticeStatus.overdue, "Commercial Manager"),
            ("EWN-003", "C-003", NoticeKind.ewn,             21, NoticeStatus.open,    "Commercial Manager"),
            ("CEN-001", "C-001", NoticeKind.ce_notification,  8, NoticeStatus.issued,  "Commercial Manager"),
            ("NOT-001", "C-002", NoticeKind.notice,          28, NoticeStatus.closed,  "PMO Director"),
        ]
        for ref, cref, kind, due, nstatus, owner in notice_rows:
            _get_or_create(
                db, CommercialNoticeItem,
                defaults={"id": _uid(), "tenant_id": tenant.id, "package_id": wp_str.id,
                          "contract_ref": cref, "kind": kind, "due_days": due,
                          "status": nstatus, "owner": owner},
                project_id=project.id, ref=ref,
            )

        # ------------------------------------------------------------------ design
        dp_rows = [
            ("DP-STR-01", "Substructure Design Package",    "Structural",  RibaStage.stage_3, 85, DesignPackageStatus.in_review,       14, 16),
            ("DP-STR-02", "Superstructure Design Package",  "Structural",  RibaStage.stage_3, 70, DesignPackageStatus.coordinating,    16, 18),
            ("DP-MEP-01", "MEP Services — Level 1",         "MEP",         RibaStage.stage_3, 55, DesignPackageStatus.in_review,       18, 20),
            ("DP-MEP-02", "MEP Services — Level 2",         "MEP",         RibaStage.stage_2, 30, DesignPackageStatus.draft,           20, 22),
            ("DP-FAC-01", "Facade & Glazing System",        "Facade",      RibaStage.stage_2, 45, DesignPackageStatus.draft,           20, 24),
            ("DP-BHS-01", "Baggage Handling System",        "BHS",         RibaStage.stage_2, 25, DesignPackageStatus.draft,           22, 22),
            ("DP-INT-01", "Interior Fit-Out — Departures",  "Interiors",   RibaStage.stage_2, 20, DesignPackageStatus.draft,           24, 26),
        ]
        design_packages = {}
        for code, name, disc, stage, mat, dpstatus, fp, fc in dp_rows:
            dp, _ = _get_or_create(
                db, DesignPackage,
                defaults={"id": _uid(), "tenant_id": tenant.id, "package_id": wp_str.id,
                          "name": name, "lead_discipline": disc, "stage": stage,
                          "maturity_pct": mat, "status": dpstatus,
                          "freeze_planned_month": fp, "freeze_current_month": fc},
                project_id=project.id, code=code,
            )
            design_packages[code] = dp

        deliverable_rows = [
            ("STR-DWG-001", "Pile Layout Plan — Zone A",          "Structural", DeliverableType.drawing,       RibaStage.stage_3, 10, DeliverableStatus.published, "Lead Structural Engineer"),
            ("STR-DWG-002", "Pile Cap Details — Zone A",          "Structural", DeliverableType.drawing,       RibaStage.stage_3, 11, DeliverableStatus.published, "Lead Structural Engineer"),
            ("STR-DWG-003", "Ground Beam Layout",                 "Structural", DeliverableType.drawing,       RibaStage.stage_3, 12, DeliverableStatus.shared,    "Lead Structural Engineer"),
            ("STR-CALC-001","Pile Capacity Calculations",         "Structural", DeliverableType.calculation,   RibaStage.stage_3, 10, DeliverableStatus.accepted,  "Geotechnical Engineer"),
            ("STR-SPEC-001","Concrete Specification",             "Structural", DeliverableType.specification, RibaStage.stage_3, 12, DeliverableStatus.published, "Lead Structural Engineer"),
            ("MEP-DWG-001", "HVAC Ductwork Layout — Level 1",     "MEP",        DeliverableType.drawing,       RibaStage.stage_3, 14, DeliverableStatus.wip,       "MEP Lead"),
            ("MEP-DWG-002", "Electrical Distribution Layout",     "MEP",        DeliverableType.drawing,       RibaStage.stage_3, 14, DeliverableStatus.wip,       "Electrical Engineer"),
            ("MEP-RPT-001", "MEP Coordination Report",            "MEP",        DeliverableType.report,        RibaStage.stage_3, 13, DeliverableStatus.overdue,   "MEP Lead"),
            ("FAC-DWG-001", "Facade System Elevation",            "Facade",     DeliverableType.drawing,       RibaStage.stage_2, 18, DeliverableStatus.wip,       "Facade Engineer"),
            ("BHS-RPT-001", "BHS Concept Design Report",          "BHS",        DeliverableType.report,        RibaStage.stage_2, 16, DeliverableStatus.wip,       "BHS Specialist"),
        ]
        for ref, title, disc, dtype, stage, month, dstatus, owner in deliverable_rows:
            _get_or_create(
                db, DesignDeliverable,
                defaults={"id": _uid(), "tenant_id": tenant.id,
                          "design_package_id": design_packages.get("DP-STR-01", list(design_packages.values())[0]).id,
                          "package_id": wp_str.id, "title": title, "discipline": disc,
                          "deliverable_type": dtype, "stage": stage, "due_month": month,
                          "status": dstatus, "owner": owner},
                project_id=project.id, ref=ref,
            )

        for ref, title, owner, sev, istatus, month in [
            ("INT-001", "Structural/MEP interface — Level 1 slab penetrations",  "Design Manager", 4, InterfaceStatus.resolving, 14),
            ("INT-002", "Facade/Structural interface — curtain wall fixings",     "Design Manager", 3, InterfaceStatus.assigned,  16),
            ("INT-003", "BHS/Structural interface — conveyor support steelwork",  "Design Manager", 5, InterfaceStatus.escalated, 15),
            ("INT-004", "MEP/Facade interface — louvre positions",                "MEP Lead",       2, InterfaceStatus.open,      18),
        ]:
            _get_or_create(
                db, DesignInterfaceItem,
                defaults={"id": _uid(), "tenant_id": tenant.id, "title": title,
                          "package_a_id": wp_str.id, "package_b_id": wp_mep.id,
                          "owner": owner, "severity": sev, "status": istatus, "due_month": month},
                project_id=project.id, ref=ref,
            )

        for ws, clash_open, clash_crit, fed_ready, share_status in [
            ("Structural",  12, 3, True,  ModelShareStatus.published),
            ("MEP",         28, 7, False, ModelShareStatus.shared),
            ("Facade",       5, 1, False, ModelShareStatus.wip),
            ("BHS",          0, 0, False, ModelShareStatus.wip),
        ]:
            _get_or_create(
                db, BimCoordinationItem,
                defaults={"id": _uid(), "tenant_id": tenant.id, "clash_open": clash_open,
                          "clash_critical": clash_crit, "federation_ready": fed_ready,
                          "model_share_status": share_status},
                project_id=project.id, workstream=ws,
            )

        # ------------------------------------------------------------------ documents
        doc_rows = [
            ("ZNZ-STR-DWG-0001", "Pile Layout Plan Zone A",          "Structural", DocumentType.drawing,       "P01", "S2", DocumentWorkflowStatus.published, CdeStage.published, 12, 95, RepositorySource.bim360),
            ("ZNZ-STR-DWG-0002", "Pile Cap Details Zone A",          "Structural", DocumentType.drawing,       "P02", "S2", DocumentWorkflowStatus.published, CdeStage.published, 12, 92, RepositorySource.bim360),
            ("ZNZ-STR-CALC-0001","Pile Capacity Calculations",       "Structural", DocumentType.calculation,   "C01", "S2", DocumentWorkflowStatus.accepted,  CdeStage.published, 11, 98, RepositorySource.meridian),
            ("ZNZ-MEP-DWG-0001", "HVAC Ductwork Layout Level 1",     "MEP",        DocumentType.drawing,       "P01", "S1", DocumentWorkflowStatus.shared,    CdeStage.shared,    14, 70, RepositorySource.bim360),
            ("ZNZ-MEP-RPT-0001", "MEP Coordination Report",          "MEP",        DocumentType.report,        "D01", "S1", DocumentWorkflowStatus.overdue,   CdeStage.wip,       13, 45, RepositorySource.sharepoint),
            ("ZNZ-FAC-DWG-0001", "Facade System Elevation",          "Facade",     DocumentType.drawing,       "P01", "S1", DocumentWorkflowStatus.wip,       CdeStage.wip,       18, 30, RepositorySource.bim360),
            ("ZNZ-PMO-RPT-0001", "Monthly Progress Report — M12",    "PMO",        DocumentType.report,        "R01", "A1", DocumentWorkflowStatus.published, CdeStage.published, 12, 100,RepositorySource.sharepoint),
            ("ZNZ-PMO-RPT-0002", "Monthly Progress Report — M13",    "PMO",        DocumentType.report,        "R01", "A1", DocumentWorkflowStatus.wip,       CdeStage.wip,       13, 60, RepositorySource.sharepoint),
            ("ZNZ-STR-SPEC-0001","Concrete Specification",           "Structural", DocumentType.specification, "S01", "S2", DocumentWorkflowStatus.published, CdeStage.published, 11, 100,RepositorySource.meridian),
            ("ZNZ-BHS-RPT-0001", "BHS Concept Design Report",        "BHS",        DocumentType.report,        "D01", "S1", DocumentWorkflowStatus.wip,       CdeStage.wip,       16, 40, RepositorySource.meridian),
        ]
        docs = {}
        for number, title, disc, dtype, rev, suit, wf_status, cde, month, meta, source in doc_rows:
            doc, _ = _get_or_create(
                db, ControlledDocument,
                defaults={"id": _uid(), "tenant_id": tenant.id, "package_id": wp_str.id,
                          "title": title, "discipline": disc, "document_type": dtype,
                          "revision": rev, "suitability": suit, "workflow_status": wf_status,
                          "cde_stage": cde, "owner": disc + " Lead", "due_month": month,
                          "metadata_pct": meta, "source": source},
                project_id=project.id, number=number,
            )
            docs[number] = doc

        for reviewer, role, rstatus, month in [
            ("James Okonkwo",   "Commercial Director", ReviewStatus.approved,  11),
            ("Dr. Amina Yusuf", "Design Director",     ReviewStatus.approved,  11),
            ("Tom Whitfield",   "PMO Director",        ReviewStatus.in_review, 13),
            ("Sarah Al-Rashid", "Programme Director",  ReviewStatus.pending,   14),
        ]:
            _get_or_create(
                db, DocumentReview,
                defaults={"id": _uid(), "tenant_id": tenant.id,
                          "document_id": list(docs.values())[0].id, "role": role,
                          "status": rstatus, "due_month": month},
                project_id=project.id, reviewer=reviewer,
            )

        for ref, recipient, doc_count, month, tstatus in [
            ("TRS-001", "Mwanza Construction Ltd.",  5, 10, TransmittalStatus.acknowledged),
            ("TRS-002", "Gulf Electro-Mechanical",   3, 11, TransmittalStatus.issued),
            ("TRS-003", "CAA Tanzania",              2, 12, TransmittalStatus.issued),
            ("TRS-004", "Skyline Architects LLP",    4, 13, TransmittalStatus.draft),
        ]:
            _get_or_create(
                db, TransmittalRecord,
                defaults={"id": _uid(), "tenant_id": tenant.id, "package_id": wp_str.id,
                          "recipient": recipient, "document_count": doc_count,
                          "issue_month": month, "status": tstatus},
                project_id=project.id, ref=ref,
            )

        first_doc = list(docs.values())[0]
        doc_list = list(docs.values())
        repo_link_rows = [
            (doc_list[0].id, RepositorySource.bim360,    "/ZNZ-T1/Structural/Drawings/",  SyncStatus.linked),
            (doc_list[1].id, RepositorySource.bim360,    "/ZNZ-T1/Structural/Drawings/",  SyncStatus.linked),
            (doc_list[3].id, RepositorySource.bim360,    "/ZNZ-T1/MEP/Drawings/",         SyncStatus.out_of_sync),
            (doc_list[6].id, RepositorySource.sharepoint,"/Sites/ZNZ-T1/PMO/Reports/",    SyncStatus.linked),
        ]
        for doc_id, repo, path, sync in repo_link_rows:
            existing = db.query(RepositoryLink).filter_by(
                project_id=project.id, document_id=doc_id, repository=repo
            ).first()
            if not existing:
                db.add(RepositoryLink(
                    id=_uid(), tenant_id=tenant.id, project_id=project.id,
                    document_id=doc_id, repository=repo, path=path, sync_status=sync,
                ))
                db.flush()

        # ------------------------------------------------------------------ meetings & actions
        meeting_rows = [
            ("MTG-001", "Governance Board — Month 10",    MeetingType.governance_board,  10, "Sarah Al-Rashid", 12, LinkedModule.gate),
            ("MTG-002", "Package Review — Structural M11",MeetingType.package_review,    11, "Tom Whitfield",    8, LinkedModule.programme),
            ("MTG-003", "Design Review — MEP Coordination",MeetingType.design_review,   11, "Dr. Amina Yusuf",  6, LinkedModule.document),
            ("MTG-004", "Commercial Review — M12",        MeetingType.commercial_review, 12, "James Okonkwo",    5, LinkedModule.commercial),
            ("MTG-005", "Governance Board — Month 12",    MeetingType.governance_board,  12, "Sarah Al-Rashid", 14, LinkedModule.gate),
            ("MTG-006", "ORAT Kick-Off",                  MeetingType.orat_review,       13, "ORAT Manager",     8, LinkedModule.orat),
        ]
        for ref, title, mtype, month, chair, attendees, linked in meeting_rows:
            _get_or_create(
                db, MeetingRecord,
                defaults={"id": _uid(), "tenant_id": tenant.id, "title": title,
                          "meeting_type": mtype, "month": month, "chair": chair,
                          "attendee_count": attendees, "linked_module": linked},
                project_id=project.id, ref=ref,
            )

        action_rows = [
            ("ACT-001", "Issue revised pile layout to contractor",          "Lead Structural Engineer", ActionSourceType.meeting,  "MTG-002", ActionPriority.critical, 12, ActionStatus.closed,         90, wp_str.id),
            ("ACT-002", "Submit MEP coordination report for review",        "MEP Lead",                 ActionSourceType.meeting,  "MTG-003", ActionPriority.high,     13, ActionStatus.overdue,        30, wp_mep.id),
            ("ACT-003", "Resolve BHS/Structural interface INT-003",         "Design Manager",           ActionSourceType.gate,     "G3",      ActionPriority.critical, 13, ActionStatus.in_progress,   60, wp_str.id),
            ("ACT-004", "Submit CE-002 quotation to client",                "Commercial Manager",       ActionSourceType.commercial,"CE-002",  ActionPriority.high,     13, ActionStatus.open,          20, wp_mep.id),
            ("ACT-005", "Update risk register with new steel supply risk",  "Risk Manager",             ActionSourceType.risk,     "R-004",   ActionPriority.medium,   14, ActionStatus.in_progress,   75, wp_str.id),
            ("ACT-006", "Prepare G3 evidence pack for board submission",    "PMO Director",             ActionSourceType.gate,     "G3",      ActionPriority.critical, 14, ActionStatus.in_progress,   50, wp_str.id),
            ("ACT-007", "Issue EWN-003 to MEP contractor",                  "Commercial Manager",       ActionSourceType.commercial,"EWN-003", ActionPriority.high,     13, ActionStatus.open,           0, wp_mep.id),
            ("ACT-008", "Confirm CAA approval timeline",                    "PMO Director",             ActionSourceType.risk,     "R-003",   ActionPriority.medium,   15, ActionStatus.open,          10, wp_str.id),
        ]
        for ref, title, owner, stype, sref, priority, month, astatus, evidence_pct, pkg_id in action_rows:
            _get_or_create(
                db, ActionItem,
                defaults={"id": _uid(), "tenant_id": tenant.id, "package_id": pkg_id,
                          "title": title, "owner": owner, "source_type": stype,
                          "source_ref": sref, "priority": priority, "due_month": month,
                          "status": astatus, "closure_evidence_pct": evidence_pct},
                project_id=project.id, ref=ref,
            )

        compliance_rows = [
            ("COMP-001", "Gate decision log maintained and current",         ComplianceDomain.governance,       "PMO Director",    12, ComplianceStatus.compliant,     100),
            ("COMP-002", "Document metadata completeness ≥ 90%",            ComplianceDomain.document_control, "Doc Controller",  13, ComplianceStatus.in_progress,    72),
            ("COMP-003", "Commercial notices issued within contractual time",ComplianceDomain.commercial,       "Comm. Manager",   13, ComplianceStatus.non_compliant,  40),
            ("COMP-004", "Design freeze dates maintained per programme",     ComplianceDomain.design,           "Design Manager",  14, ComplianceStatus.in_progress,    60),
            ("COMP-005", "Risk register reviewed monthly",                   ComplianceDomain.governance,       "Risk Manager",    13, ComplianceStatus.compliant,     100),
            ("COMP-006", "ORAT workstream progress reported fortnightly",    ComplianceDomain.orat,             "ORAT Manager",    14, ComplianceStatus.open,           20),
        ]
        for ref, title, domain, owner, month, cstatus, evidence_pct in compliance_rows:
            _get_or_create(
                db, ComplianceItem,
                defaults={"id": _uid(), "tenant_id": tenant.id, "package_id": wp_str.id,
                          "title": title, "domain": domain, "owner": owner,
                          "due_month": month, "status": cstatus, "evidence_pct": evidence_pct},
                project_id=project.id, ref=ref,
            )

        # ------------------------------------------------------------------ ORAT
        orat_ws_rows = [
            ("Airside Operations",        "ORAT Manager",    65, OratWorkstreamStatus.in_progress, 54),
            ("Landside & Ground Transport","ORAT Manager",   45, OratWorkstreamStatus.in_progress, 54),
            ("Baggage Handling",          "BHS Specialist",  30, OratWorkstreamStatus.at_risk,     52),
            ("Passenger Processing",      "Terminal Ops Mgr",55, OratWorkstreamStatus.in_progress, 54),
            ("Security & Access Control", "Security Manager",40, OratWorkstreamStatus.in_progress, 54),
            ("IT & Communications",       "ICT Manager",     20, OratWorkstreamStatus.not_started, 56),
            ("Emergency Response",        "Safety Manager",  70, OratWorkstreamStatus.in_progress, 54),
            ("Retail & Concessions",      "Commercial Ops",  15, OratWorkstreamStatus.not_started, 58),
        ]
        orat_ws = {}
        for name, owner, pct, ws_status, month in orat_ws_rows:
            ws, _ = _get_or_create(
                db, OratWorkstream,
                defaults={"id": _uid(), "tenant_id": tenant.id, "owner": owner,
                          "progress_pct": pct, "status": ws_status, "due_month": month},
                project_id=project.id, name=name,
            )
            orat_ws[name] = ws

        trial_rows = [
            ("TRL-001", "Airside Vehicle Movement Trial",       40, 45, TrialStatus.planned,  "Planned trial — airside vehicle routing validation.", orat_ws["Airside Operations"].id),
            ("TRL-002", "Baggage Reconciliation System Test",   35, 20, TrialStatus.planned,  "Full BRS end-to-end test with live baggage.", orat_ws["Baggage Handling"].id),
            ("TRL-003", "Passenger Processing — Departures",    42, 200,TrialStatus.planned,  "Full departures flow with volunteer passengers.", orat_ws["Passenger Processing"].id),
            ("TRL-004", "Emergency Evacuation Drill",           44, 150,TrialStatus.planned,  "Full terminal evacuation to assembly points.", orat_ws["Emergency Response"].id),
            ("TRL-005", "Security Screening Trial",             43, 80, TrialStatus.planned,  "Security lane throughput and detection rate test.", orat_ws["Security & Access Control"].id),
            ("TRL-006", "IT Systems Integration Test",          45, 15, TrialStatus.planned,  "End-to-end DCS, FIDS, and CUTE system test.", orat_ws["IT & Communications"].id),
        ]
        for ref, title, month, participants, tstatus, obs, ws_id in trial_rows:
            _get_or_create(
                db, OratTrial,
                defaults={"id": _uid(), "tenant_id": tenant.id, "workstream_id": ws_id,
                          "title": title, "month": month, "participants": participants,
                          "status": tstatus, "observations": obs},
                project_id=project.id, ref=ref,
            )

        training_rows = [
            ("Airside Driving",          120, 45, TrainingStatus.in_delivery, "ORAT Manager"),
            ("Passenger Services",       280, 80, TrainingStatus.scheduled,   "Terminal Ops Mgr"),
            ("Security Screening",       150, 30, TrainingStatus.scheduled,   "Security Manager"),
            ("Baggage Handling",          90, 20, TrainingStatus.not_started, "BHS Specialist"),
            ("Emergency Response",       200, 60, TrainingStatus.in_delivery, "Safety Manager"),
            ("IT Systems",                40, 10, TrainingStatus.not_started, "ICT Manager"),
            ("Retail Operations",         60,  0, TrainingStatus.not_started, "Commercial Ops"),
        ]
        for fn, target, trained, tstatus, owner in training_rows:
            _get_or_create(
                db, TrainingGroup,
                defaults={"id": _uid(), "tenant_id": tenant.id,
                          "target_headcount": target, "trained_headcount": trained,
                          "status": tstatus, "owner": owner},
                project_id=project.id, function_name=fn,
            )

        handover_rows = [
            ("HOV-001", "Airside Pavement & Markings",    HandoverStatus.in_verification, 75, "ORAT Manager",    wp_str.id),
            ("HOV-002", "Terminal Building Structure",    HandoverStatus.pending,          20, "PMO Director",    wp_str.id),
            ("HOV-003", "MEP Services — Level 1",         HandoverStatus.pending,          10, "MEP Lead",        wp_mep.id),
            ("HOV-004", "Baggage Handling System",        HandoverStatus.blocked,           5, "BHS Specialist",  wp_bhs.id),
            ("HOV-005", "Security Systems",               HandoverStatus.pending,          15, "Security Manager",wp_str.id),
            ("HOV-006", "IT Infrastructure",              HandoverStatus.blocked,           0, "ICT Manager",     wp_str.id),
            ("HOV-007", "Retail Fit-Out",                 HandoverStatus.pending,           0, "Commercial Ops",  wp_facade.id),
        ]
        for ref, asset_group, hstatus, evidence_pct, owner, pkg_id in handover_rows:
            _get_or_create(
                db, HandoverItem,
                defaults={"id": _uid(), "tenant_id": tenant.id, "package_id": pkg_id,
                          "asset_group": asset_group, "status": hstatus,
                          "evidence_pct": evidence_pct, "owner": owner},
                project_id=project.id, ref=ref,
            )

        # ------------------------------------------------------------------ reporting
        template_rows = [
            ("Board Pack — Monthly",          ReportTemplateType.board_pack,       "Programme Board",    8, ReportFormat.pdf_excel, True),
            ("Monthly PMO Report",            ReportTemplateType.monthly_pmo,      "PMO Team",           12,ReportFormat.pdf,       True),
            ("G3 Gate Evidence Pack",         ReportTemplateType.gate_pack,        "Gate Board",         6, ReportFormat.pdf,       True),
            ("Risk Report — Monthly",         ReportTemplateType.risk_report,      "Risk Committee",     5, ReportFormat.pdf,       True),
            ("Commercial Summary",            ReportTemplateType.commercial_summary,"Commercial Board",  7, ReportFormat.pdf_excel, True),
            ("Document Control Report",       ReportTemplateType.document_control, "Document Controller",4,ReportFormat.excel,     True),
            ("ORAT Readiness Pack",           ReportTemplateType.orat_pack,        "ORAT Board",         9, ReportFormat.pdf,       False),
        ]
        templates = {}
        for name, ttype, audience, sections, fmt, enabled in template_rows:
            t, _ = _get_or_create(
                db, ReportTemplate,
                defaults={"id": _uid(), "tenant_id": tenant.id, "template_type": ttype,
                          "audience": audience, "section_count": sections,
                          "default_format": fmt, "enabled": enabled},
                project_id=project.id, name=name,
            )
            templates[name] = t

        job_rows = [
            ("EXP-001", "Board Pack — Month 12",          ReportFormat.pdf_excel, "PMO Director",  12, ExportJobStatus.ready,      100, None,                          None),
            ("EXP-002", "Monthly PMO Report — Month 12",  ReportFormat.pdf,       "PMO Director",  12, ExportJobStatus.ready,      100, None,                          None),
            ("EXP-003", "G3 Gate Evidence Pack",          ReportFormat.pdf,       "PMO Director",  13, ExportJobStatus.generating,  65, None,                          None),
            ("EXP-004", "Risk Report — Month 13",         ReportFormat.pdf,       "Risk Manager",  13, ExportJobStatus.queued,       0, None,                          None),
            ("EXP-005", "Commercial Summary — Month 11",  ReportFormat.pdf_excel, "Comm. Manager", 11, ExportJobStatus.ready,      100, None,                          None),
            ("EXP-006", "Board Pack — Month 11",          ReportFormat.pdf_excel, "PMO Director",  11, ExportJobStatus.ready,      100, None,                          None),
            ("EXP-007", "ORAT Readiness Pack — Draft",    ReportFormat.pdf,       "ORAT Manager",  13, ExportJobStatus.failed,       0, None, "Template not yet enabled"),
        ]
        for ref, title, fmt, created_by, month, jstatus, progress, artifact_url, error_msg in job_rows:
            tmpl = list(templates.values())[0]
            _get_or_create(
                db, ExportJob,
                defaults={"id": _uid(), "tenant_id": tenant.id, "template_id": tmpl.id,
                          "title": title, "format": fmt, "created_by": created_by,
                          "created_month": month, "status": jstatus,
                          "progress_pct": progress, "artifact_url": artifact_url,
                          "error_message": error_msg},
                project_id=project.id, ref=ref,
            )

        archive_rows = [
            ("ARC-001", "Board Pack — Month 10",         ReportFormat.pdf_excel, 10, 4.2,  ["board", "monthly", "M10"]),
            ("ARC-002", "Board Pack — Month 11",         ReportFormat.pdf_excel, 11, 4.5,  ["board", "monthly", "M11"]),
            ("ARC-003", "Monthly PMO Report — Month 10", ReportFormat.pdf,       10, 2.1,  ["pmo", "monthly", "M10"]),
            ("ARC-004", "Monthly PMO Report — Month 11", ReportFormat.pdf,       11, 2.3,  ["pmo", "monthly", "M11"]),
            ("ARC-005", "Commercial Summary — Month 10", ReportFormat.pdf_excel, 10, 1.8,  ["commercial", "M10"]),
            ("ARC-006", "G2 Gate Evidence Pack",         ReportFormat.pdf,        9, 8.7,  ["gate", "G2", "governance"]),
        ]
        for ref, title, fmt, month, size_mb, tags in archive_rows:
            _get_or_create(
                db, ArchiveRecord,
                defaults={"id": _uid(), "tenant_id": tenant.id, "export_job_id": None,
                          "title": title, "format": fmt, "generated_month": month,
                          "size_mb": int(size_mb), "tags_csv": ",".join(tags), "artifact_url": None},
                project_id=project.id, ref=ref,
            )

        # ------------------------------------------------------------------ search index
        index_rows = [
            ("PRJ-001",  "Zanzibar International Airport — Terminal Expansion", SearchEntityType.project,    SearchSource.meridian,    SearchGroup.core,        None,       "Active",          ["airport", "terminal", "ZNZ"]),
            ("SCH-001",  "Programme Master Schedule R4",                        SearchEntityType.schedule,   SearchSource.meridian,    SearchGroup.delivery,    "WP-STR-01","Issued",          ["schedule", "programme", "R4"]),
            ("GATE-G3",  "G3 Detailed Design Approval",                         SearchEntityType.gate,       SearchSource.meridian,    SearchGroup.governance,  None,       "Active",          ["gate", "G3", "design"]),
            ("RISK-001", "Piling refusal due to unforeseen rock strata",         SearchEntityType.risk,       SearchSource.meridian,    SearchGroup.delivery,    "WP-STR-01","Mitigating",      ["risk", "piling", "geotechnical"]),
            ("RISK-002", "Late issue of MEP detail design drawings",             SearchEntityType.risk,       SearchSource.meridian,    SearchGroup.delivery,    "WP-MEP-02","Assessed",        ["risk", "MEP", "design"]),
            ("COM-CE001","CE-001 Unforeseen rock — additional piling works",     SearchEntityType.commercial, SearchSource.meridian,    SearchGroup.commercial,  "WP-STR-01","Approved",        ["CE", "commercial", "piling"]),
            ("DES-DP01", "Substructure Design Package",                          SearchEntityType.design,     SearchSource.bim360,      SearchGroup.technical,   "WP-STR-01","In Review",       ["design", "structural", "RIBA3"]),
            ("DOC-0001", "Pile Layout Plan Zone A",                              SearchEntityType.document,   SearchSource.bim360,      SearchGroup.technical,   "WP-STR-01","Published",       ["drawing", "piling", "structural"]),
            ("DOC-0002", "MEP Coordination Report",                              SearchEntityType.document,   SearchSource.sharepoint,  SearchGroup.technical,   "WP-MEP-02","Overdue",         ["report", "MEP", "coordination"]),
            ("ACT-003",  "Resolve BHS/Structural interface INT-003",             SearchEntityType.action,     SearchSource.meridian,    SearchGroup.delivery,    "WP-STR-01","In Progress",     ["action", "BHS", "interface"]),
            ("ORAT-WS1", "Airside Operations Workstream",                        SearchEntityType.orat,       SearchSource.meridian,    SearchGroup.operations,  None,       "In Progress",     ["ORAT", "airside", "operations"]),
            ("REP-001",  "Board Pack — Month 12",                                SearchEntityType.report,     SearchSource.meridian,    SearchGroup.outputs,     None,       "Ready",           ["report", "board", "monthly"]),
        ]
        for entity_ref, title, etype, source, group, pkg_code, status_text, tags in index_rows:
            _get_or_create(
                db, SearchIndexRecord,
                defaults={"id": _uid(), "tenant_id": tenant.id,
                          "title": title, "summary": f"{title} — {status_text}",
                          "source": source, "group_name": group,
                          "package_code": pkg_code, "status_text": status_text,
                          "tags_csv": ",".join(tags), "permission_scope": "project"},
                project_id=project.id, entity_type=etype, entity_ref=entity_ref,
            )

        for name, query, scope, type_filter in [
            ("Open Risks",          "status:Assessed OR status:Mitigating", SavedSearchScope.module_specific, "Risk"),
            ("Overdue Documents",   "status:Overdue",                       SavedSearchScope.module_specific, "Document"),
            ("Critical Actions",    "priority:Critical",                    SavedSearchScope.module_specific, "Action"),
            ("BIM360 Documents",    "source:BIM360",                        SavedSearchScope.repository_only, None),
        ]:
            _get_or_create(
                db, SavedSearch,
                defaults={"id": _uid(), "tenant_id": tenant.id,
                          "user_email": "admin@meridian.local",
                          "query_text": query, "scope": scope,
                          "type_filter": type_filter, "source_filter": None,
                          "package_filter": None},
                project_id=project.id, name=name,
            )

        for source, ext_ref, path, sync in [
            (SearchSource.bim360,    "urn:adsk.wipprod:dm.lineage:abc123", "/ZNZ-T1/Structural/",  ConnectorSyncStatus.indexed),
            (SearchSource.bim360,    "urn:adsk.wipprod:dm.lineage:def456", "/ZNZ-T1/MEP/",         ConnectorSyncStatus.stale),
            (SearchSource.sharepoint,"sp://sites/ZNZ-T1/PMO",             "/Sites/ZNZ-T1/PMO/",   ConnectorSyncStatus.indexed),
            (SearchSource.sharepoint,"sp://sites/ZNZ-T1/Commercial",      "/Sites/ZNZ-T1/Comm/",  ConnectorSyncStatus.pending),
        ]:
            _get_or_create(
                db, ConnectorReference,
                defaults={"id": _uid(), "tenant_id": tenant.id, "source": source,
                          "path": path, "sync_status": sync, "index_record_id": None},
                project_id=project.id, external_ref=ext_ref,
            )

        # ------------------------------------------------------------------ commit
        db.commit()
        if project_created:
            print(f"Seeded tenant={tenant.id!r} project={project.code!r} with full demo data.")
        else:
            print("Seed already present — refreshed any missing rows.")


if __name__ == "__main__":  # pragma: no cover
    seed()
