"""Minimal smoke test — ensures the app starts, auth works in dev-bypass,
projects can be created, and the dashboard rollup returns 200. Extend this as
new domains come online.
"""
from __future__ import annotations

from fastapi.testclient import TestClient


def test_health(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_modules_registry(client: TestClient) -> None:
    r = client.get("/modules")
    assert r.status_code == 200
    keys = {m["key"] for m in r.json()}
    assert {
        "dashboard",
        "projects",
        "schedule",
        "risks",
        "stage-gates",
        "commercial",
        "design",
        "documents",
        "meetings",
        "orat",
        "reporting",
        "search",
    }.issubset(keys)
    # Stage Gates has been ported — confirm the registry flag is flipped.
    stage_gates = next(m for m in r.json() if m["key"] == "stage-gates")
    assert stage_gates["is_enabled"] is True
    # Commercial has been ported — confirm the registry flag is flipped.
    commercial = next(m for m in r.json() if m["key"] == "commercial")
    assert commercial["is_enabled"] is True
    # Design Management has been ported — confirm the registry flag is flipped.
    design = next(m for m in r.json() if m["key"] == "design")
    assert design["is_enabled"] is True
    # Document Control has been ported — confirm the registry flag is flipped.
    documents = next(m for m in r.json() if m["key"] == "documents")
    assert documents["is_enabled"] is True
    # Meetings & Accountability has been ported — confirm the registry flag is flipped.
    meetings = next(m for m in r.json() if m["key"] == "meetings")
    assert meetings["is_enabled"] is True
    # ORAT Readiness has been ported — confirm the registry flag is flipped.
    orat = next(m for m in r.json() if m["key"] == "orat")
    assert orat["is_enabled"] is True
    # Reporting has been ported — confirm the registry flag is flipped.
    reporting = next(m for m in r.json() if m["key"] == "reporting")
    assert reporting["is_enabled"] is True
    # Search & Ingestion has been ported — confirm the registry flag is flipped.
    search = next(m for m in r.json() if m["key"] == "search")
    assert search["is_enabled"] is True


def test_me(client: TestClient) -> None:
    r = client.get("/auth/me")
    assert r.status_code == 200
    assert r.json()["role"] == "Tenant Admin"


def test_project_lifecycle(client: TestClient) -> None:
    payload = {"code": "AAA", "name": "Acme Airport", "status": "Planned"}
    r = client.post("/projects", json=payload)
    assert r.status_code == 201, r.text
    project = r.json()
    pid = project["id"]

    r2 = client.get(f"/projects/{pid}/dashboard")
    assert r2.status_code == 200, r2.text
    data = r2.json()
    assert data["project"]["code"] == "AAA"
    assert data["counts"]["work_packages"] == 0

    # Duplicate code rejected.
    r3 = client.post("/projects", json=payload)
    assert r3.status_code == 409


def test_risk_and_schedule_endpoints(client: TestClient) -> None:
    r = client.post(
        "/projects",
        json={"code": "BBB", "name": "Beta Airport", "status": "Active"},
    )
    pid = r.json()["id"]
    risk_payload = {
        "code": "R-100",
        "title": "Piling refusal",
        "category": "Technical",
        "likelihood": 4,
        "impact": 4,
    }
    r = client.post(f"/projects/{pid}/risks", json=risk_payload)
    assert r.status_code == 201, r.text
    assert r.json()["residual_score"] == 16

    r = client.get(f"/projects/{pid}/risks/heatmap")
    assert r.status_code == 200
    assert len(r.json()["cells"]) == 1

    r = client.get(f"/projects/{pid}/schedule/activities")
    assert r.status_code == 200
    assert r.json() == []


def test_stage_gate_governance(client: TestClient) -> None:
    """End-to-end exercise of the Stage Gate Governance surface."""
    r = client.post(
        "/projects",
        json={"code": "GGG", "name": "Gamma Airport", "status": "Active"},
    )
    assert r.status_code == 201, r.text
    pid = r.json()["id"]

    # Create G1 Feasibility gate.
    gate_payload = {
        "code": "G1",
        "name": "Feasibility",
        "purpose": "Confirm feasibility and mandate for outline design.",
        "target_month": 6,
        "status": "Upcoming",
        "package_ids": [],
    }
    r = client.post(f"/projects/{pid}/stage-gates", json=gate_payload)
    assert r.status_code == 201, r.text
    gate = r.json()
    gid = gate["id"]
    assert gate["code"] == "G1"

    # Duplicate code rejected with 409.
    r = client.post(f"/projects/{pid}/stage-gates", json=gate_payload)
    assert r.status_code == 409, r.text

    # List gates returns the one we just created.
    r = client.get(f"/projects/{pid}/stage-gates")
    assert r.status_code == 200
    assert len(r.json()) == 1

    # Add evidence: one required accepted + one required submitted → 80% readiness.
    ev_accepted = {
        "gate_definition_id": gid,
        "title": "Feasibility Report",
        "category": "Strategy",
        "required": True,
        "status": "Accepted",
        "owner": "PMO Director",
    }
    ev_submitted = {
        "gate_definition_id": gid,
        "title": "Cost Plan (Class 4)",
        "category": "Commercial",
        "required": True,
        "status": "Submitted",
        "owner": "Commercial Manager",
    }
    r = client.post(f"/projects/{pid}/stage-gates/evidence", json=ev_accepted)
    assert r.status_code == 201, r.text
    r = client.post(f"/projects/{pid}/stage-gates/evidence", json=ev_submitted)
    assert r.status_code == 201, r.text

    # Add one approved approval + one pending approval → 50% approval progress.
    app_approved = {
        "gate_definition_id": gid,
        "approver": "Programme Director",
        "role": "Chair",
        "status": "Approved",
    }
    app_pending = {
        "gate_definition_id": gid,
        "approver": "CFO",
        "role": "Finance",
        "status": "Pending",
    }
    r = client.post(f"/projects/{pid}/stage-gates/approvals", json=app_approved)
    assert r.status_code == 201, r.text
    r = client.post(f"/projects/{pid}/stage-gates/approvals", json=app_pending)
    assert r.status_code == 201, r.text

    # Readiness rollup: (1.0 + 0.6) / 2 * 100 = 80; approvals 1/2 = 50.
    r = client.get(f"/projects/{pid}/stage-gates/{gid}/readiness")
    assert r.status_code == 200, r.text
    rd = r.json()
    assert rd["required_evidence_count"] == 2
    assert rd["accepted_evidence_count"] == 1
    assert rd["submitted_evidence_count"] == 1
    assert rd["readiness_score"] == 80
    assert rd["approval_count"] == 2
    assert rd["approval_progress"] == 50

    # Project-level governance summary.
    r = client.get(f"/projects/{pid}/stage-gates/summary")
    assert r.status_code == 200, r.text
    summ = r.json()
    assert summ["gate_count"] == 1
    assert summ["evidence_count"] == 2
    assert summ["approval_count"] == 2
    assert summ["average_readiness_score"] == 80


def test_commercial(client: TestClient) -> None:
    """End-to-end exercise of the Commercial / Cost & Change Control surface."""
    r = client.post(
        "/projects",
        json={"code": "CCC", "name": "Charlie Airport", "status": "Active"},
    )
    assert r.status_code == 201, r.text
    pid = r.json()["id"]

    # Two work packages for cost-control and exposure tests.
    r = client.post(
        f"/projects/{pid}/work-packages",
        json={
            "code": "WP-CIV",
            "name": "Civils & Earthworks",
            "package_type": "Civil",
            "status": "Active",
        },
    )
    assert r.status_code == 201, r.text
    wp1_id = r.json()["id"]
    r = client.post(
        f"/projects/{pid}/work-packages",
        json={
            "code": "WP-MEP",
            "name": "Terminal MEP",
            "package_type": "MEP",
            "status": "Active",
        },
    )
    assert r.status_code == 201, r.text
    wp2_id = r.json()["id"]

    # Cost controls: both packages budget 1,000,000 minor, 50% complete, 400,000 actual.
    cost_payload = {
        "package_id": wp1_id,
        "budget_minor": 1_000_000,
        "committed_minor": 800_000,
        "forecast_minor": 1_050_000,
        "actual_minor": 400_000,
        "percent_complete": 50,
    }
    r = client.post(f"/projects/{pid}/commercial/cost-controls", json=cost_payload)
    assert r.status_code == 201, r.text

    # Duplicate cost-control for the same package is rejected 409.
    r = client.post(f"/projects/{pid}/commercial/cost-controls", json=cost_payload)
    assert r.status_code == 409, r.text

    cost_payload_2 = {**cost_payload, "package_id": wp2_id}
    r = client.post(f"/projects/{pid}/commercial/cost-controls", json=cost_payload_2)
    assert r.status_code == 201, r.text

    # Unknown package → 404 from the package validator.
    r = client.post(
        f"/projects/{pid}/commercial/cost-controls",
        json={**cost_payload, "package_id": "00000000-0000-0000-0000-000000000000"},
    )
    assert r.status_code == 404, r.text

    # Register a Compensation Event with Strong entitlement.
    change_payload = {
        "package_id": wp1_id,
        "ref": "CE-001",
        "title": "Unforeseen rock encountered in piling",
        "change_type": "Compensation Event",
        "status": "Notified",
        "cost_impact_minor": 250_000,
        "time_impact_weeks": 3,
        "entitlement": "Strong",
        "owner": "Commercial Manager",
        "cause": "Rock stratum 2m shallower than GI baseline; piling rig refusal (NEC cl.60.1(12)).",
    }
    r = client.post(f"/projects/{pid}/commercial/changes", json=change_payload)
    assert r.status_code == 201, r.text

    # Duplicate change ref → 409.
    r = client.post(f"/projects/{pid}/commercial/changes", json=change_payload)
    assert r.status_code == 409, r.text

    # Log an overdue EWN notice.
    notice_payload = {
        "package_id": wp1_id,
        "ref": "EWN-001",
        "contract_ref": "NEC-MC-001",
        "kind": "EWN",
        "due_days": 0,
        "status": "Overdue",
        "owner": "Project Manager",
    }
    r = client.post(f"/projects/{pid}/commercial/notices", json=notice_payload)
    assert r.status_code == 201, r.text

    # Commercial summary rollup.
    r = client.get(f"/projects/{pid}/commercial/summary")
    assert r.status_code == 200, r.text
    s = r.json()
    assert s["budget_minor"] == 2_000_000
    assert s["committed_minor"] == 1_600_000
    assert s["forecast_minor"] == 2_100_000
    assert s["actual_minor"] == 800_000
    assert s["forecast_variance_minor"] == 100_000  # forecast - budget
    assert s["change_exposure_minor"] == 250_000
    assert s["notice_count"] == 1
    assert s["overdue_notice_count"] == 1
    assert s["strong_entitlement_count"] == 1

    # EVM rollup: BAC 2M, EV 1M, AC 800k → CPI 1.25; PV = (50+10)/100 * 2M = 1.2M → SPI ≈ 0.8333.
    r = client.get(f"/projects/{pid}/commercial/evm-summary")
    assert r.status_code == 200, r.text
    e = r.json()
    assert e["bac_minor"] == 2_000_000
    assert e["ev_minor"] == 1_000_000
    assert e["ac_minor"] == 800_000
    assert e["pv_minor"] == 1_200_000
    assert e["cv_minor"] == 200_000
    assert e["sv_minor"] == -200_000
    assert e["average_percent_complete"] == 50
    assert abs(e["cpi"] - 1.25) < 0.001
    assert abs(e["spi"] - 0.8333) < 0.001

    # Per-package exposure: 2 packages, wp1 carries the change + notice.
    r = client.get(f"/projects/{pid}/commercial/exposure")
    assert r.status_code == 200, r.text
    exp = {row["package_id"]: row for row in r.json()}
    assert len(exp) == 2
    assert exp[wp1_id]["change_exposure_minor"] == 250_000
    assert exp[wp1_id]["notice_count"] == 1
    assert exp[wp1_id]["overdue_notice_count"] == 1
    assert exp[wp2_id]["change_exposure_minor"] == 0
    assert exp[wp2_id]["notice_count"] == 0

    # Filter changes by type returns only CEs.
    r = client.get(
        f"/projects/{pid}/commercial/changes",
        params={"change_type": "Compensation Event"},
    )
    assert r.status_code == 200
    assert len(r.json()) == 1

    # Filter notices by status=Overdue.
    r = client.get(
        f"/projects/{pid}/commercial/notices", params={"status": "Overdue"}
    )
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_design_management(client: TestClient) -> None:
    """End-to-end exercise of the Design Management surface."""
    r = client.post(
        "/projects",
        json={"code": "DDD", "name": "Delta Airport", "status": "Active"},
    )
    assert r.status_code == 201, r.text
    pid = r.json()["id"]

    # Two work packages used as endpoints for design interfaces.
    r = client.post(
        f"/projects/{pid}/work-packages",
        json={
            "code": "WP-TML",
            "name": "Terminal",
            "package_type": "Structural",
            "status": "Active",
        },
    )
    assert r.status_code == 201, r.text
    wp_terminal = r.json()["id"]
    r = client.post(
        f"/projects/{pid}/work-packages",
        json={
            "code": "WP-AFD",
            "name": "Airfield",
            "package_type": "Airside",
            "status": "Active",
        },
    )
    assert r.status_code == 201, r.text
    wp_airfield = r.json()["id"]

    # Design package — RIBA Stage 3, maturity 60%, freeze 2 months slipped.
    dp_payload = {
        "package_id": wp_terminal,
        "code": "DP-ARC-T1",
        "name": "Terminal 1 Architecture",
        "lead_discipline": "Architecture",
        "stage": "3",
        "maturity_pct": 60,
        "status": "Coordinating",
        "freeze_planned_month": 12,
        "freeze_current_month": 14,
    }
    r = client.post(f"/projects/{pid}/design/design-packages", json=dp_payload)
    assert r.status_code == 201, r.text
    dp_id = r.json()["id"]
    assert r.json()["code"] == "DP-ARC-T1"

    # Duplicate code rejected with 409.
    r = client.post(f"/projects/{pid}/design/design-packages", json=dp_payload)
    assert r.status_code == 409, r.text

    # Second design package — frozen, 100% maturity, on-plan freeze.
    dp2_payload = {
        "package_id": wp_terminal,
        "code": "DP-STR-T1",
        "name": "Terminal 1 Structure",
        "lead_discipline": "Structural",
        "stage": "4",
        "maturity_pct": 100,
        "status": "Frozen",
        "freeze_planned_month": 10,
        "freeze_current_month": 10,
    }
    r = client.post(f"/projects/{pid}/design/design-packages", json=dp2_payload)
    assert r.status_code == 201, r.text

    # Unknown work_package_id → 404.
    r = client.post(
        f"/projects/{pid}/design/design-packages",
        json={
            **dp_payload,
            "code": "DP-X",
            "package_id": "00000000-0000-0000-0000-000000000000",
        },
    )
    assert r.status_code == 404, r.text

    # Two deliverables — one Overdue, one WIP (default).
    deliv_overdue = {
        "design_package_id": dp_id,
        "ref": "DRG-ARC-001",
        "title": "Floor Plan L1",
        "discipline": "Architecture",
        "deliverable_type": "Drawing",
        "stage": "3",
        "due_month": 8,
        "status": "Overdue",
        "owner": "Lead Architect",
    }
    r = client.post(f"/projects/{pid}/design/deliverables", json=deliv_overdue)
    assert r.status_code == 201, r.text
    # Duplicate ref → 409.
    r = client.post(f"/projects/{pid}/design/deliverables", json=deliv_overdue)
    assert r.status_code == 409, r.text

    deliv_wip = {
        "design_package_id": dp_id,
        "ref": "RPT-ARC-001",
        "title": "Spatial Coordination Report",
        "discipline": "Architecture",
        "deliverable_type": "Report",
        "stage": "3",
        "due_month": 12,
        "owner": "Design Manager",
    }
    r = client.post(f"/projects/{pid}/design/deliverables", json=deliv_wip)
    assert r.status_code == 201, r.text

    # Interface — escalated, severity 5.
    iface_payload = {
        "ref": "IF-001",
        "title": "Terminal/Airfield apron edge interface",
        "package_a_id": wp_terminal,
        "package_b_id": wp_airfield,
        "owner": "Interface Manager",
        "severity": 5,
        "status": "Escalated",
        "due_month": 9,
    }
    r = client.post(f"/projects/{pid}/design/interfaces", json=iface_payload)
    assert r.status_code == 201, r.text
    # Duplicate ref → 409.
    r = client.post(f"/projects/{pid}/design/interfaces", json=iface_payload)
    assert r.status_code == 409, r.text

    # BIM coordination item — 3 critical clashes, federation not yet ready.
    bim_payload = {
        "workstream": "Architecture / MEP",
        "clash_open": 12,
        "clash_critical": 3,
        "federation_ready": False,
        "model_share_status": "Shared",
    }
    r = client.post(f"/projects/{pid}/design/bim-items", json=bim_payload)
    assert r.status_code == 201, r.text

    # Summary rollup.
    r = client.get(f"/projects/{pid}/design/summary")
    assert r.status_code == 200, r.text
    s = r.json()
    assert s["design_package_count"] == 2
    assert s["deliverable_count"] == 2
    assert s["interface_count"] == 1
    assert s["bim_item_count"] == 1
    # Avg maturity = (60 + 100) / 2 = 80
    assert s["average_maturity_pct"] == 80
    assert s["overdue_deliverable_count"] == 1
    assert s["frozen_package_count"] == 1
    assert s["escalated_interface_count"] == 1
    assert s["critical_clash_count"] == 3
    # Avg freeze variance = ((14-12) + (10-10)) / 2 = 1
    assert s["average_freeze_variance_months"] == 1

    # Freeze-control surface.
    r = client.get(f"/projects/{pid}/design/freeze-control")
    assert r.status_code == 200, r.text
    fc = r.json()
    assert fc["project_id"] == pid
    assert len(fc["entries"]) == 2
    by_code = {e["code"]: e for e in fc["entries"]}
    assert by_code["DP-ARC-T1"]["variance_months"] == 2
    assert by_code["DP-STR-T1"]["variance_months"] == 0

    # Filter deliverables by status=Overdue.
    r = client.get(
        f"/projects/{pid}/design/deliverables", params={"status": "Overdue"}
    )
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["ref"] == "DRG-ARC-001"

    # Filter design packages by stage=4 → just the Frozen one.
    r = client.get(
        f"/projects/{pid}/design/design-packages", params={"stage": "4"}
    )
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["code"] == "DP-STR-T1"


def test_document_control(client: TestClient) -> None:
    """End-to-end exercise of the Document Control surface."""
    r = client.post(
        "/projects",
        json={"code": "EEE", "name": "Echo Airport", "status": "Active"},
    )
    assert r.status_code == 201, r.text
    pid = r.json()["id"]

    # Work package used to scope a controlled document.
    r = client.post(
        f"/projects/{pid}/work-packages",
        json={
            "code": "WP-TML",
            "name": "Terminal",
            "package_type": "Structural",
            "status": "Active",
        },
    )
    assert r.status_code == 201, r.text
    wp_id = r.json()["id"]

    # Document 1 — Overdue Drawing, metadata 70%.
    doc_overdue = {
        "package_id": wp_id,
        "number": "EEE-ARC-DWG-T1-0001",
        "title": "Terminal 1 — Level 00 General Arrangement",
        "discipline": "Architecture",
        "document_type": "Drawing",
        "revision": "P03",
        "suitability": "S3",
        "workflow_status": "Overdue",
        "cde_stage": "Shared",
        "owner": "Lead Architect",
        "due_month": 6,
        "metadata_pct": 70,
        "source": "Meridian",
    }
    r = client.post(f"/projects/{pid}/documents", json=doc_overdue)
    assert r.status_code == 201, r.text
    doc1_id = r.json()["id"]
    assert r.json()["number"] == "EEE-ARC-DWG-T1-0001"

    # Duplicate document number → 409.
    r = client.post(f"/projects/{pid}/documents", json=doc_overdue)
    assert r.status_code == 409, r.text

    # Document 2 — Published Specification, metadata 90%.
    doc_published = {
        "number": "EEE-STR-SPE-T1-0002",
        "title": "Terminal 1 — Structural Specification",
        "discipline": "Structural",
        "document_type": "Specification",
        "revision": "C01",
        "suitability": "S4",
        "workflow_status": "Published",
        "cde_stage": "Published",
        "owner": "Structural Lead",
        "due_month": 10,
        "metadata_pct": 90,
        "source": "BIM360",
    }
    r = client.post(f"/projects/{pid}/documents", json=doc_published)
    assert r.status_code == 201, r.text
    doc2_id = r.json()["id"]

    # Unknown work_package_id → 404.
    r = client.post(
        f"/projects/{pid}/documents",
        json={
            **doc_overdue,
            "number": "EEE-X",
            "package_id": "00000000-0000-0000-0000-000000000000",
        },
    )
    assert r.status_code == 404, r.text

    # Review — Pending, against doc1.
    review_payload = {
        "document_id": doc1_id,
        "reviewer": "Design Manager",
        "role": "Technical Reviewer",
        "status": "Pending",
        "due_month": 7,
    }
    r = client.post(f"/projects/{pid}/documents/reviews", json=review_payload)
    assert r.status_code == 201, r.text

    # Second review — Approved, against doc2.
    r = client.post(
        f"/projects/{pid}/documents/reviews",
        json={
            "document_id": doc2_id,
            "reviewer": "Engineer of Record",
            "role": "Discipline Lead",
            "status": "Approved",
            "due_month": 10,
        },
    )
    assert r.status_code == 201, r.text

    # Review against an unknown document → 404.
    r = client.post(
        f"/projects/{pid}/documents/reviews",
        json={
            **review_payload,
            "document_id": "00000000-0000-0000-0000-000000000000",
        },
    )
    assert r.status_code == 404, r.text

    # Transmittal — Issued bundle of 2 docs.
    trans_payload = {
        "ref": "TRN-0001",
        "package_id": wp_id,
        "recipient": "Principal Contractor",
        "document_count": 2,
        "issue_month": 8,
        "status": "Issued",
    }
    r = client.post(f"/projects/{pid}/documents/transmittals", json=trans_payload)
    assert r.status_code == 201, r.text

    # Duplicate transmittal ref → 409.
    r = client.post(f"/projects/{pid}/documents/transmittals", json=trans_payload)
    assert r.status_code == 409, r.text

    # Repository link — doc1 in BIM360 with Out of Sync status.
    link_payload = {
        "document_id": doc1_id,
        "repository": "BIM360",
        "path": "/projects/meridian/terminal/L00-GA.dwg",
        "sync_status": "Out of Sync",
    }
    r = client.post(
        f"/projects/{pid}/documents/repository-links", json=link_payload
    )
    assert r.status_code == 201, r.text

    # Second link — doc2 in SharePoint, Linked.
    r = client.post(
        f"/projects/{pid}/documents/repository-links",
        json={
            "document_id": doc2_id,
            "repository": "SharePoint",
            "path": "/sites/meridian/Terminal/Specs/Structural.docx",
            "sync_status": "Linked",
        },
    )
    assert r.status_code == 201, r.text

    # Summary rollup.
    r = client.get(f"/projects/{pid}/documents/summary")
    assert r.status_code == 200, r.text
    s = r.json()
    assert s["document_count"] == 2
    assert s["review_count"] == 2
    assert s["transmittal_count"] == 1
    assert s["repository_link_count"] == 2
    # Avg metadata = (70 + 90) / 2 = 80
    assert s["average_metadata_pct"] == 80
    assert s["overdue_document_count"] == 1
    assert s["published_document_count"] == 1
    assert s["pending_review_count"] == 1
    assert s["sync_issue_count"] == 1
    assert s["issued_transmittal_count"] == 1

    # Filter documents by workflow_status=Overdue.
    r = client.get(
        f"/projects/{pid}/documents", params={"workflow_status": "Overdue"}
    )
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["number"] == "EEE-ARC-DWG-T1-0001"

    # Filter documents by source=BIM360.
    r = client.get(f"/projects/{pid}/documents", params={"source": "BIM360"})
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["number"] == "EEE-STR-SPE-T1-0002"

    # Filter reviews by status=Pending.
    r = client.get(
        f"/projects/{pid}/documents/reviews", params={"status": "Pending"}
    )
    assert r.status_code == 200
    assert len(r.json()) == 1

    # Filter transmittals by status=Issued.
    r = client.get(
        f"/projects/{pid}/documents/transmittals", params={"status": "Issued"}
    )
    assert r.status_code == 200
    assert len(r.json()) == 1

    # Filter repository links by sync_status=Out of Sync.
    r = client.get(
        f"/projects/{pid}/documents/repository-links",
        params={"sync_status": "Out of Sync"},
    )
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_accountability(client: TestClient) -> None:
    """End-to-end exercise of the Meetings, Actions & Compliance surface."""
    r = client.post(
        "/projects",
        json={"code": "FFF", "name": "Foxtrot Airport", "status": "Active"},
    )
    assert r.status_code == 201, r.text
    pid = r.json()["id"]

    # Two work packages used to anchor actions / compliance items and to
    # populate the per-package action-pressure heat map.
    r = client.post(
        f"/projects/{pid}/work-packages",
        json={
            "code": "WP-TML",
            "name": "Terminal",
            "package_type": "Structural",
            "status": "Active",
        },
    )
    assert r.status_code == 201, r.text
    wp_terminal = r.json()["id"]
    r = client.post(
        f"/projects/{pid}/work-packages",
        json={
            "code": "WP-AFD",
            "name": "Airfield",
            "package_type": "Airside",
            "status": "Active",
        },
    )
    assert r.status_code == 201, r.text
    wp_airfield = r.json()["id"]

    # ---- Meetings ----
    meeting_payload = {
        "ref": "MTG-001",
        "title": "March Governance Board",
        "meeting_type": "Governance Board",
        "month": 3,
        "chair": "Programme Director",
        "attendee_count": 12,
        "linked_module": "Programme",
    }
    r = client.post(f"/projects/{pid}/meetings", json=meeting_payload)
    assert r.status_code == 201, r.text
    assert r.json()["ref"] == "MTG-001"

    # Duplicate meeting ref → 409.
    r = client.post(f"/projects/{pid}/meetings", json=meeting_payload)
    assert r.status_code == 409, r.text

    # Second meeting — Package Review.
    r = client.post(
        f"/projects/{pid}/meetings",
        json={
            "ref": "MTG-002",
            "title": "Terminal Package Review",
            "meeting_type": "Package Review",
            "month": 4,
            "chair": "Design Manager",
            "attendee_count": 8,
            "linked_module": "Document",
        },
    )
    assert r.status_code == 201, r.text

    # ---- Action items ----
    # Overdue action, Critical priority, terminal package, 30% evidence.
    act_overdue = {
        "package_id": wp_terminal,
        "ref": "ACT-001",
        "title": "Close S3 review comments on Level 1 GA",
        "owner": "Lead Architect",
        "source_type": "Meeting",
        "source_ref": "MTG-001",
        "priority": "Critical",
        "due_month": 3,
        "status": "Overdue",
        "closure_evidence_pct": 30,
    }
    r = client.post(f"/projects/{pid}/meetings/actions", json=act_overdue)
    assert r.status_code == 201, r.text

    # Duplicate action ref → 409.
    r = client.post(f"/projects/{pid}/meetings/actions", json=act_overdue)
    assert r.status_code == 409, r.text

    # Open action — Critical, in progress, terminal, 60% evidence.
    r = client.post(
        f"/projects/{pid}/meetings/actions",
        json={
            "package_id": wp_terminal,
            "ref": "ACT-002",
            "title": "Resolve apron edge interface",
            "owner": "Interface Manager",
            "source_type": "Meeting",
            "source_ref": "MTG-002",
            "priority": "Critical",
            "due_month": 5,
            "status": "In Progress",
            "closure_evidence_pct": 60,
        },
    )
    assert r.status_code == 201, r.text

    # Closed action — no package, 100% evidence (programme-level governance).
    r = client.post(
        f"/projects/{pid}/meetings/actions",
        json={
            "ref": "ACT-003",
            "title": "Issue PMO monthly report",
            "owner": "PMO Director",
            "source_type": "Gate",
            "source_ref": "G2",
            "priority": "Medium",
            "due_month": 3,
            "status": "Closed",
            "closure_evidence_pct": 100,
        },
    )
    assert r.status_code == 201, r.text

    # Unknown package_id → 404 from the package validator.
    r = client.post(
        f"/projects/{pid}/meetings/actions",
        json={
            **act_overdue,
            "ref": "ACT-X",
            "package_id": "00000000-0000-0000-0000-000000000000",
        },
    )
    assert r.status_code == 404, r.text

    # ---- Compliance items ----
    # Non-Compliant, ORAT domain, airfield package.
    comp_nc = {
        "package_id": wp_airfield,
        "ref": "CMP-001",
        "title": "Aerodrome certificate application",
        "domain": "ORAT",
        "owner": "ORAT Lead",
        "due_month": 5,
        "status": "Non-Compliant",
        "evidence_pct": 20,
    }
    r = client.post(f"/projects/{pid}/meetings/compliance-items", json=comp_nc)
    assert r.status_code == 201, r.text

    # Duplicate compliance ref → 409.
    r = client.post(f"/projects/{pid}/meetings/compliance-items", json=comp_nc)
    assert r.status_code == 409, r.text

    # Compliant item — Document Control domain, terminal package.
    r = client.post(
        f"/projects/{pid}/meetings/compliance-items",
        json={
            "package_id": wp_terminal,
            "ref": "CMP-002",
            "title": "ISO 19650 CDE audit",
            "domain": "Document Control",
            "owner": "Document Controller",
            "due_month": 4,
            "status": "Compliant",
            "evidence_pct": 100,
        },
    )
    assert r.status_code == 201, r.text

    # ---- Summary rollup ----
    r = client.get(f"/projects/{pid}/meetings/summary")
    assert r.status_code == 200, r.text
    s = r.json()
    assert s["project_id"] == pid
    assert s["meeting_count"] == 2
    assert s["action_count"] == 3
    assert s["compliance_count"] == 2
    # Open = In Progress (ACT-002) — one action. Overdue = ACT-001.
    assert s["open_action_count"] == 1
    assert s["overdue_action_count"] == 1
    # Avg closure evidence = round((30 + 60 + 100) / 3) = 63
    assert s["average_closure_evidence_pct"] == 63
    assert s["compliant_count"] == 1
    # Non-compliant + overdue compliance = 1
    assert s["non_compliant_count"] == 1

    # ---- Action pressure heat map ----
    r = client.get(f"/projects/{pid}/meetings/action-pressure")
    assert r.status_code == 200, r.text
    by_pkg = {row["package_id"]: row for row in r.json()}
    assert len(by_pkg) == 2
    # Terminal carries both critical actions; one overdue.
    assert by_pkg[wp_terminal]["action_count"] == 2
    assert by_pkg[wp_terminal]["overdue_count"] == 1
    assert by_pkg[wp_terminal]["critical_count"] == 2
    # Avg evidence for terminal = (30 + 60) / 2 = 45
    assert by_pkg[wp_terminal]["average_closure_evidence_pct"] == 45
    # Airfield has no actions.
    assert by_pkg[wp_airfield]["action_count"] == 0
    assert by_pkg[wp_airfield]["overdue_count"] == 0
    assert by_pkg[wp_airfield]["critical_count"] == 0
    assert by_pkg[wp_airfield]["average_closure_evidence_pct"] == 0

    # ---- List filters ----
    # Filter actions by status=Overdue.
    r = client.get(
        f"/projects/{pid}/meetings/actions", params={"status": "Overdue"}
    )
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["ref"] == "ACT-001"

    # Filter actions by priority=Critical → ACT-001 and ACT-002.
    r = client.get(
        f"/projects/{pid}/meetings/actions", params={"priority": "Critical"}
    )
    assert r.status_code == 200
    assert len(r.json()) == 2

    # Filter meetings by meeting_type=Governance Board.
    r = client.get(
        f"/projects/{pid}/meetings", params={"meeting_type": "Governance Board"}
    )
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["ref"] == "MTG-001"

    # Filter compliance items by domain=ORAT.
    r = client.get(
        f"/projects/{pid}/meetings/compliance-items", params={"domain": "ORAT"}
    )
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["ref"] == "CMP-001"

    # Filter compliance items by status=Compliant.
    r = client.get(
        f"/projects/{pid}/meetings/compliance-items",
        params={"status": "Compliant"},
    )
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["ref"] == "CMP-002"


def test_orat(client: TestClient) -> None:
    """End-to-end exercise of the ORAT Readiness & Handover surface."""
    r = client.post(
        "/projects",
        json={"code": "HHH", "name": "Hotel Airport", "status": "Active"},
    )
    assert r.status_code == 201, r.text
    pid = r.json()["id"]

    # Two work packages used to anchor handover items and populate the
    # per-package handover-pressure heat map.
    r = client.post(
        f"/projects/{pid}/work-packages",
        json={
            "code": "WP-TML",
            "name": "Terminal",
            "package_type": "Structural",
            "status": "Active",
        },
    )
    assert r.status_code == 201, r.text
    wp_terminal = r.json()["id"]
    r = client.post(
        f"/projects/{pid}/work-packages",
        json={
            "code": "WP-AFD",
            "name": "Airfield",
            "package_type": "Airside",
            "status": "Active",
        },
    )
    assert r.status_code == 201, r.text
    wp_airfield = r.json()["id"]

    # ---- Workstreams ----
    ws_at_risk_payload = {
        "name": "Terminal Operations Readiness",
        "owner": "Terminal Ops Lead",
        "progress_pct": 40,
        "status": "At Risk",
        "due_month": 5,
    }
    r = client.post(
        f"/projects/{pid}/orat/workstreams", json=ws_at_risk_payload
    )
    assert r.status_code == 201, r.text
    ws_at_risk = r.json()["id"]

    # Duplicate workstream name → 409.
    r = client.post(
        f"/projects/{pid}/orat/workstreams", json=ws_at_risk_payload
    )
    assert r.status_code == 409, r.text

    # Second workstream — Ready at 100%.
    r = client.post(
        f"/projects/{pid}/orat/workstreams",
        json={
            "name": "Airside Operations Readiness",
            "owner": "Airside Ops Lead",
            "progress_pct": 100,
            "status": "Ready",
            "due_month": 4,
        },
    )
    assert r.status_code == 201, r.text
    ws_ready = r.json()["id"]

    # ---- Trials ----
    trial_failed = {
        "workstream_id": ws_at_risk,
        "ref": "T-001",
        "title": "Terminal partial trial — check-in to security",
        "month": 3,
        "participants": 80,
        "status": "Failed",
        "observations": "FIDS CUTE cut-over failure — rerun required.",
    }
    r = client.post(f"/projects/{pid}/orat/trials", json=trial_failed)
    assert r.status_code == 201, r.text

    # Duplicate trial ref → 409.
    r = client.post(f"/projects/{pid}/orat/trials", json=trial_failed)
    assert r.status_code == 409, r.text

    # Passed trial on the Ready workstream.
    r = client.post(
        f"/projects/{pid}/orat/trials",
        json={
            "workstream_id": ws_ready,
            "ref": "T-002",
            "title": "Airside integrated trial — aircraft turnaround",
            "month": 4,
            "participants": 40,
            "status": "Passed",
            "observations": "All 12 turnaround scenarios cleared.",
        },
    )
    assert r.status_code == 201, r.text

    # Planned trial — no workstream (cross-workstream dress rehearsal).
    r = client.post(
        f"/projects/{pid}/orat/trials",
        json={
            "ref": "T-003",
            "title": "Integrated dress rehearsal",
            "month": 5,
            "participants": 200,
            "status": "Planned",
            "observations": "Mass-participation trial — volunteer pax.",
        },
    )
    assert r.status_code == 201, r.text

    # Unknown workstream_id on a trial → 404.
    r = client.post(
        f"/projects/{pid}/orat/trials",
        json={
            **trial_failed,
            "ref": "T-X",
            "workstream_id": "00000000-0000-0000-0000-000000000000",
        },
    )
    assert r.status_code == 404, r.text

    # ---- Training groups ----
    # Ground Handling — 20 of 50 trained (40%).
    tg_gh_payload = {
        "function_name": "Ground Handling",
        "target_headcount": 50,
        "trained_headcount": 20,
        "status": "In Delivery",
        "owner": "Ground Handling Lead",
    }
    r = client.post(
        f"/projects/{pid}/orat/training-groups", json=tg_gh_payload
    )
    assert r.status_code == 201, r.text

    # Duplicate function_name → 409.
    r = client.post(
        f"/projects/{pid}/orat/training-groups", json=tg_gh_payload
    )
    assert r.status_code == 409, r.text

    # Security — 30 of 30 trained (100%).
    r = client.post(
        f"/projects/{pid}/orat/training-groups",
        json={
            "function_name": "Security",
            "target_headcount": 30,
            "trained_headcount": 30,
            "status": "Complete",
            "owner": "Security Lead",
        },
    )
    assert r.status_code == 201, r.text

    # Trained > target → 422.
    r = client.post(
        f"/projects/{pid}/orat/training-groups",
        json={
            "function_name": "Retail",
            "target_headcount": 10,
            "trained_headcount": 15,
            "status": "In Delivery",
            "owner": "Retail Lead",
        },
    )
    assert r.status_code == 422, r.text

    # ---- Handover items ----
    # Blocked — no package (programme-level artefact), 10% evidence.
    ho_blocked = {
        "ref": "HO-001",
        "asset_group": "Aerodrome certificate",
        "status": "Blocked",
        "evidence_pct": 10,
        "owner": "ORAT Lead",
    }
    r = client.post(f"/projects/{pid}/orat/handover-items", json=ho_blocked)
    assert r.status_code == 201, r.text

    # Duplicate handover ref → 409.
    r = client.post(f"/projects/{pid}/orat/handover-items", json=ho_blocked)
    assert r.status_code == 409, r.text

    # Accepted — terminal package, 100% evidence.
    r = client.post(
        f"/projects/{pid}/orat/handover-items",
        json={
            "package_id": wp_terminal,
            "ref": "HO-002",
            "asset_group": "BHS as-installed pack",
            "status": "Accepted",
            "evidence_pct": 100,
            "owner": "BHS Manager",
        },
    )
    assert r.status_code == 201, r.text

    # In Verification — terminal package, 60% evidence.
    r = client.post(
        f"/projects/{pid}/orat/handover-items",
        json={
            "package_id": wp_terminal,
            "ref": "HO-003",
            "asset_group": "FIDS/CUTE O&M manuals",
            "status": "In Verification",
            "evidence_pct": 60,
            "owner": "ICT Lead",
        },
    )
    assert r.status_code == 201, r.text

    # Unknown package_id → 404 from the package validator.
    r = client.post(
        f"/projects/{pid}/orat/handover-items",
        json={
            **ho_blocked,
            "ref": "HO-X",
            "package_id": "00000000-0000-0000-0000-000000000000",
        },
    )
    assert r.status_code == 404, r.text

    # ---- Summary rollup ----
    r = client.get(f"/projects/{pid}/orat/summary")
    assert r.status_code == 200, r.text
    s = r.json()
    assert s["project_id"] == pid
    assert s["workstream_count"] == 2
    assert s["trial_count"] == 3
    assert s["training_group_count"] == 2
    assert s["handover_item_count"] == 3
    # Avg progress = round((40 + 100) / 2) = 70
    assert s["average_workstream_progress_pct"] == 70
    # One At Risk workstream.
    assert s["at_risk_workstream_count"] == 1
    # One Passed trial (T-002).
    assert s["passed_trial_count"] == 1
    # Training completion = round((20 + 30) / (50 + 30) * 100) = round(62.5) = 62
    # (Python uses banker's rounding — halves round to even.)
    assert s["training_completion_pct"] == 62
    assert s["accepted_handover_count"] == 1
    assert s["blocked_handover_count"] == 1

    # ---- Handover pressure heat map ----
    r = client.get(f"/projects/{pid}/orat/handover-pressure")
    assert r.status_code == 200, r.text
    by_pkg = {row["package_id"]: row for row in r.json()}
    assert len(by_pkg) == 2
    # Terminal carries HO-002 (Accepted) + HO-003 (In Verification).
    assert by_pkg[wp_terminal]["handover_count"] == 2
    assert by_pkg[wp_terminal]["accepted_count"] == 1
    assert by_pkg[wp_terminal]["blocked_count"] == 0
    assert by_pkg[wp_terminal]["pending_count"] == 1  # In Verification
    # Avg evidence for terminal = (100 + 60) / 2 = 80
    assert by_pkg[wp_terminal]["average_evidence_pct"] == 80
    # Airfield has no handover items.
    assert by_pkg[wp_airfield]["handover_count"] == 0
    assert by_pkg[wp_airfield]["accepted_count"] == 0
    assert by_pkg[wp_airfield]["blocked_count"] == 0
    assert by_pkg[wp_airfield]["pending_count"] == 0
    assert by_pkg[wp_airfield]["average_evidence_pct"] == 0

    # ---- List filters ----
    # Filter workstreams by status=At Risk.
    r = client.get(
        f"/projects/{pid}/orat/workstreams", params={"status": "At Risk"}
    )
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["name"] == "Terminal Operations Readiness"

    # Filter trials by status=Failed.
    r = client.get(
        f"/projects/{pid}/orat/trials", params={"status": "Failed"}
    )
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["ref"] == "T-001"

    # Filter trials by workstream_id → ws_at_risk has one trial (T-001).
    r = client.get(
        f"/projects/{pid}/orat/trials", params={"workstream_id": ws_at_risk}
    )
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["ref"] == "T-001"

    # Filter training groups by status=Complete.
    r = client.get(
        f"/projects/{pid}/orat/training-groups",
        params={"status": "Complete"},
    )
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["function_name"] == "Security"

    # Filter handover items by status=Blocked.
    r = client.get(
        f"/projects/{pid}/orat/handover-items",
        params={"status": "Blocked"},
    )
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["ref"] == "HO-001"


def test_reporting(client: TestClient) -> None:
    """End-to-end exercise of the Reporting & Export surface."""
    r = client.post(
        "/projects",
        json={"code": "III", "name": "India Airport", "status": "Active"},
    )
    assert r.status_code == 201, r.text
    pid = r.json()["id"]

    # ---- Templates ----
    board_payload = {
        "name": "Board Pack — Monthly",
        "template_type": "Board Pack",
        "audience": "Board",
        "section_count": 8,
        "default_format": "PDF",
        "enabled": True,
    }
    r = client.post(
        f"/projects/{pid}/reporting/templates", json=board_payload
    )
    assert r.status_code == 201, r.text
    board_tpl_id = r.json()["id"]

    # Duplicate template name → 409.
    r = client.post(
        f"/projects/{pid}/reporting/templates", json=board_payload
    )
    assert r.status_code == 409, r.text

    # Second template — Monthly PMO, enabled.
    r = client.post(
        f"/projects/{pid}/reporting/templates",
        json={
            "name": "Monthly PMO Report",
            "template_type": "Monthly PMO Report",
            "audience": "PMO",
            "section_count": 12,
            "default_format": "PDF + Excel",
            "enabled": True,
        },
    )
    assert r.status_code == 201, r.text
    pmo_tpl_id = r.json()["id"]

    # Third template — Risk Report, disabled (sunset template).
    r = client.post(
        f"/projects/{pid}/reporting/templates",
        json={
            "name": "Risk Report — Legacy",
            "template_type": "Risk Report",
            "audience": "Risk Committee",
            "section_count": 5,
            "default_format": "Excel",
            "enabled": False,
        },
    )
    assert r.status_code == 201, r.text
    risk_tpl_id = r.json()["id"]

    # ---- Export Jobs ----
    # Failed job on the Board Pack template.
    job_failed = {
        "template_id": board_tpl_id,
        "ref": "EXP-001",
        "title": "Board Pack — April",
        "format": "PDF",
        "created_by": "PMO Director",
        "created_month": 4,
        "status": "Failed",
        "progress_pct": 80,
        "error_message": "Chart library timeout on the risk heat-map section.",
    }
    r = client.post(
        f"/projects/{pid}/reporting/export-jobs", json=job_failed
    )
    assert r.status_code == 201, r.text

    # Duplicate export job ref → 409.
    r = client.post(
        f"/projects/{pid}/reporting/export-jobs", json=job_failed
    )
    assert r.status_code == 409, r.text

    # Generating job on the PMO template at 50%.
    r = client.post(
        f"/projects/{pid}/reporting/export-jobs",
        json={
            "template_id": pmo_tpl_id,
            "ref": "EXP-002",
            "title": "Monthly PMO — April",
            "format": "PDF + Excel",
            "created_by": "Controls Manager",
            "created_month": 4,
            "status": "Generating",
            "progress_pct": 50,
        },
    )
    assert r.status_code == 201, r.text

    # Ready job on the PMO template at 100%, with artefact URL.
    r = client.post(
        f"/projects/{pid}/reporting/export-jobs",
        json={
            "template_id": pmo_tpl_id,
            "ref": "EXP-003",
            "title": "Monthly PMO — March",
            "format": "PDF + Excel",
            "created_by": "Controls Manager",
            "created_month": 3,
            "status": "Ready",
            "progress_pct": 100,
            "artifact_url": "https://meridian.example/exports/EXP-003.zip",
        },
    )
    assert r.status_code == 201, r.text
    ready_job_id = r.json()["id"]

    # Ad-hoc job — no template.
    r = client.post(
        f"/projects/{pid}/reporting/export-jobs",
        json={
            "ref": "EXP-AD1",
            "title": "Ad-hoc export — CAA submission",
            "format": "PDF",
            "created_by": "ORAT Lead",
            "created_month": 4,
            "status": "Queued",
            "progress_pct": 0,
        },
    )
    assert r.status_code == 201, r.text

    # Unknown template_id on an export job → 404 from the template validator.
    r = client.post(
        f"/projects/{pid}/reporting/export-jobs",
        json={
            **job_failed,
            "ref": "EXP-X",
            "template_id": "00000000-0000-0000-0000-000000000000",
        },
    )
    assert r.status_code == 404, r.text

    # ---- Archive records ----
    # Archive tied to the Ready PMO job.
    ar_payload = {
        "export_job_id": ready_job_id,
        "ref": "AR-001",
        "title": "Monthly PMO — March (archived)",
        "format": "PDF + Excel",
        "generated_month": 3,
        "size_mb": 18,
        "tags": ["monthly-pmo", "march", "pmo"],
        "artifact_url": "https://meridian.example/archive/AR-001.zip",
    }
    r = client.post(f"/projects/{pid}/reporting/archive", json=ar_payload)
    assert r.status_code == 201, r.text
    # Tags are exposed as list on the wire.
    assert r.json()["tags"] == ["monthly-pmo", "march", "pmo"]

    # Duplicate archive ref → 409.
    r = client.post(f"/projects/{pid}/reporting/archive", json=ar_payload)
    assert r.status_code == 409, r.text

    # Externally-uploaded artefact — no parent job.
    r = client.post(
        f"/projects/{pid}/reporting/archive",
        json={
            "ref": "AR-002",
            "title": "Gate G4 Evidence Pack — external",
            "format": "PDF",
            "generated_month": 2,
            "size_mb": 42,
            "tags": ["gate-pack", "g4"],
        },
    )
    assert r.status_code == 201, r.text

    # Unknown export_job_id on archive → 404 from the job validator.
    r = client.post(
        f"/projects/{pid}/reporting/archive",
        json={
            **ar_payload,
            "ref": "AR-X",
            "export_job_id": "00000000-0000-0000-0000-000000000000",
        },
    )
    assert r.status_code == 404, r.text

    # size_mb must be >= 1 → 422.
    r = client.post(
        f"/projects/{pid}/reporting/archive",
        json={
            "ref": "AR-Y",
            "title": "Zero-byte artefact",
            "format": "PDF",
            "generated_month": 4,
            "size_mb": 0,
            "tags": [],
        },
    )
    assert r.status_code == 422, r.text

    # ---- Summary rollup ----
    r = client.get(f"/projects/{pid}/reporting/summary")
    assert r.status_code == 200, r.text
    s = r.json()
    assert s["project_id"] == pid
    assert s["template_count"] == 3
    assert s["enabled_template_count"] == 2
    assert s["job_count"] == 4
    # Active queue = Generating (EXP-002) + Queued (EXP-AD1) = 2.
    assert s["active_job_count"] == 2
    assert s["ready_job_count"] == 1
    assert s["failed_job_count"] == 1
    assert s["archive_count"] == 2
    # Avg progress = round((80 + 50 + 100 + 0) / 4) = round(57.5) = 58
    # (Python uses banker's rounding — halves round to even, so round(57.5) = 58.)
    assert s["average_job_progress_pct"] == 58

    # ---- Template pressure heat map ----
    r = client.get(f"/projects/{pid}/reporting/template-pressure")
    assert r.status_code == 200, r.text
    by_tpl = {row["template_id"]: row for row in r.json()}
    assert len(by_tpl) == 3
    # Board Pack carries EXP-001 (Failed).
    assert by_tpl[board_tpl_id]["job_count"] == 1
    assert by_tpl[board_tpl_id]["failed_count"] == 1
    assert by_tpl[board_tpl_id]["ready_count"] == 0
    assert by_tpl[board_tpl_id]["active_count"] == 0
    # PMO carries EXP-002 (Generating) + EXP-003 (Ready).
    assert by_tpl[pmo_tpl_id]["job_count"] == 2
    assert by_tpl[pmo_tpl_id]["active_count"] == 1
    assert by_tpl[pmo_tpl_id]["ready_count"] == 1
    assert by_tpl[pmo_tpl_id]["failed_count"] == 0
    # Risk Report (disabled) has no jobs.
    assert by_tpl[risk_tpl_id]["job_count"] == 0
    assert by_tpl[risk_tpl_id]["enabled"] is False

    # ---- List filters ----
    # Filter templates by template_type=Monthly PMO Report.
    r = client.get(
        f"/projects/{pid}/reporting/templates",
        params={"template_type": "Monthly PMO Report"},
    )
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["name"] == "Monthly PMO Report"

    # Filter templates by enabled=false.
    r = client.get(
        f"/projects/{pid}/reporting/templates", params={"enabled": False}
    )
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["name"] == "Risk Report — Legacy"

    # Filter export jobs by status=Failed.
    r = client.get(
        f"/projects/{pid}/reporting/export-jobs",
        params={"status": "Failed"},
    )
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["ref"] == "EXP-001"

    # Filter export jobs by template_id → PMO has two jobs.
    r = client.get(
        f"/projects/{pid}/reporting/export-jobs",
        params={"template_id": pmo_tpl_id},
    )
    assert r.status_code == 200
    assert len(r.json()) == 2
    refs = {row["ref"] for row in r.json()}
    assert refs == {"EXP-002", "EXP-003"}

    # Filter archive by format=PDF.
    r = client.get(
        f"/projects/{pid}/reporting/archive", params={"format": "PDF"}
    )
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["ref"] == "AR-002"

    # ---- PATCH ----
    # Patch the Failed job to Ready (operator re-run).
    r = client.patch(
        f"/projects/{pid}/reporting/export-jobs/{ready_job_id}",
        json={"title": "Monthly PMO — March (re-issued)"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["title"] == "Monthly PMO — March (re-issued)"

    # Patch archive tags.
    archive_list = client.get(f"/projects/{pid}/reporting/archive").json()
    ar_001 = next(a for a in archive_list if a["ref"] == "AR-001")
    r = client.patch(
        f"/projects/{pid}/reporting/archive/{ar_001['id']}",
        json={"tags": ["monthly-pmo", "re-issued"]},
    )
    assert r.status_code == 200, r.text
    assert r.json()["tags"] == ["monthly-pmo", "re-issued"]

    # Patch unknown archive id → 404.
    r = client.patch(
        f"/projects/{pid}/reporting/archive/00000000-0000-0000-0000-000000000000",
        json={"title": "nope"},
    )
    assert r.status_code == 404, r.text


def test_search(client: TestClient) -> None:
    """End-to-end exercise of the Enterprise Search & Retrieval surface."""
    r = client.post(
        "/projects",
        json={"code": "JJJ", "name": "Juliet Airport", "status": "Active"},
    )
    assert r.status_code == 201, r.text
    pid = r.json()["id"]

    # ---- Index records ----
    risk_payload = {
        "entity_type": "Risk",
        "entity_ref": "R-042",
        "title": "Piling refusal exposure",
        "summary": "Unexpected rock encountered on TWY-A piling rig.",
        "source": "Meridian",
        "group_name": "Technical",
        "package_code": "TWY-A",
        "status_text": "Active",
        "tags": ["rock", "geotech", "twy-a"],
    }
    r = client.post(f"/projects/{pid}/search/index", json=risk_payload)
    assert r.status_code == 201, r.text
    risk_rec = r.json()
    risk_id = risk_rec["id"]
    # Tags are exposed as list on the wire.
    assert risk_rec["tags"] == ["rock", "geotech", "twy-a"]
    # Default permission scope applied.
    assert risk_rec["permission_scope"] == "tenant:all"

    # Duplicate (entity_type, entity_ref) in same project → 409.
    r = client.post(f"/projects/{pid}/search/index", json=risk_payload)
    assert r.status_code == 409, r.text

    # Document record sourced from SharePoint.
    r = client.post(
        f"/projects/{pid}/search/index",
        json={
            "entity_type": "Document",
            "entity_ref": "JJJ-ARC-DWG-T1-0042",
            "title": "Terminal 1 — Concept Plan",
            "summary": "RIBA Stage 2 concept plan for T1 landside envelope.",
            "source": "SharePoint",
            "group_name": "Delivery",
            "package_code": "T1",
            "status_text": "S2",
            "tags": ["terminal-1", "concept", "riba-2"],
        },
    )
    assert r.status_code == 201, r.text

    # BIM item record sourced from BIM360.
    r = client.post(
        f"/projects/{pid}/search/index",
        json={
            "entity_type": "Design",
            "entity_ref": "BIM-MEP-001",
            "title": "MEP clash — plant room 4",
            "summary": "Ducting clash against structural transfer beam.",
            "source": "BIM360",
            "group_name": "Technical",
            "package_code": "T1",
            "status_text": "Open",
            "tags": ["mep", "clash", "plant-room"],
        },
    )
    assert r.status_code == 201, r.text

    # ORAT record — Teams source, no package.
    r = client.post(
        f"/projects/{pid}/search/index",
        json={
            "entity_type": "ORAT",
            "entity_ref": "ORAT-W-001",
            "title": "ORAT workstream — Airside Operations",
            "summary": "Airside ops tabletop scheduled for Month -4.",
            "source": "Teams",
            "group_name": "Operations",
            "tags": ["orat", "airside"],
        },
    )
    assert r.status_code == 201, r.text

    # ---- Index list + filters ----
    r = client.get(f"/projects/{pid}/search/index")
    assert r.status_code == 200
    assert len(r.json()) == 4

    # Filter by entity_type.
    r = client.get(
        f"/projects/{pid}/search/index", params={"entity_type": "Risk"}
    )
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["entity_ref"] == "R-042"

    # Filter by source.
    r = client.get(
        f"/projects/{pid}/search/index", params={"source": "BIM360"}
    )
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["entity_ref"] == "BIM-MEP-001"

    # Filter by group_name + package_code combination.
    r = client.get(
        f"/projects/{pid}/search/index",
        params={"group_name": "Technical", "package_code": "T1"},
    )
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["entity_ref"] == "BIM-MEP-001"

    # ---- Retrieval ----
    # Search over title — "Terminal" matches the SharePoint doc.
    r = client.get(f"/projects/{pid}/search/query", params={"q": "Terminal"})
    assert r.status_code == 200, r.text
    result = r.json()
    assert result["total"] == 1
    assert result["grouped_counts"] == {"Document": 1}
    assert result["results"][0]["entity_ref"] == "JJJ-ARC-DWG-T1-0042"

    # Search over tags_csv — "clash" matches the BIM item.
    r = client.get(f"/projects/{pid}/search/query", params={"q": "clash"})
    assert r.status_code == 200
    assert r.json()["total"] == 1
    assert r.json()["results"][0]["entity_ref"] == "BIM-MEP-001"

    # Search over summary + filter by source.
    r = client.get(
        f"/projects/{pid}/search/query",
        params={"q": "ops", "source": "Teams"},
    )
    assert r.status_code == 200
    assert r.json()["total"] == 1
    assert r.json()["results"][0]["entity_ref"] == "ORAT-W-001"

    # Search with no hits.
    r = client.get(
        f"/projects/{pid}/search/query", params={"q": "nothing-here"}
    )
    assert r.status_code == 200
    assert r.json()["total"] == 0
    assert r.json()["grouped_counts"] == {}

    # ---- PATCH index record ----
    r = client.patch(
        f"/projects/{pid}/search/index/{risk_id}",
        json={"status_text": "Mitigated", "tags": ["rock", "geotech", "closed"]},
    )
    assert r.status_code == 200, r.text
    assert r.json()["status_text"] == "Mitigated"
    assert r.json()["tags"] == ["rock", "geotech", "closed"]

    # Patch unknown index record id → 404.
    r = client.patch(
        f"/projects/{pid}/search/index/00000000-0000-0000-0000-000000000000",
        json={"title": "nope"},
    )
    assert r.status_code == 404, r.text

    # ---- Saved searches ----
    r = client.post(
        f"/projects/{pid}/search/saved-searches",
        json={
            "name": "Open Risks",
            "query_text": "status:Active",
            "scope": "Module Specific",
            "type_filter": "Risk",
        },
    )
    assert r.status_code == 201, r.text

    # Duplicate saved search name → 409.
    r = client.post(
        f"/projects/{pid}/search/saved-searches",
        json={
            "name": "Open Risks",
            "query_text": "status:Active",
        },
    )
    assert r.status_code == 409, r.text

    # Second saved search — repository-scoped.
    r = client.post(
        f"/projects/{pid}/search/saved-searches",
        json={
            "name": "BIM Clashes",
            "query_text": "clash",
            "scope": "Repository Only",
            "source_filter": "BIM360",
        },
    )
    assert r.status_code == 201, r.text
    bim_saved_id = r.json()["id"]

    # List + scope filter.
    r = client.get(f"/projects/{pid}/search/saved-searches")
    assert r.status_code == 200
    assert len(r.json()) == 2

    r = client.get(
        f"/projects/{pid}/search/saved-searches",
        params={"scope": "Repository Only"},
    )
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["name"] == "BIM Clashes"

    # PATCH a saved search.
    r = client.patch(
        f"/projects/{pid}/search/saved-searches/{bim_saved_id}",
        json={"query_text": "clash plant-room"},
    )
    assert r.status_code == 200
    assert r.json()["query_text"] == "clash plant-room"

    # ---- Connector references ----
    # Pointer linked to the risk index record, Indexed state.
    r = client.post(
        f"/projects/{pid}/search/connector-references",
        json={
            "source": "Meridian",
            "external_ref": "MRD-RISK-R042",
            "path": "/risks/R-042",
            "sync_status": "Indexed",
            "index_record_id": risk_id,
        },
    )
    assert r.status_code == 201, r.text
    meridian_ref_id = r.json()["id"]

    # Duplicate external_ref → 409.
    r = client.post(
        f"/projects/{pid}/search/connector-references",
        json={
            "source": "Meridian",
            "external_ref": "MRD-RISK-R042",
            "path": "/risks/R-042",
        },
    )
    assert r.status_code == 409, r.text

    # Pending SharePoint reference.
    r = client.post(
        f"/projects/{pid}/search/connector-references",
        json={
            "source": "SharePoint",
            "external_ref": "SP-CONCEPT-T1",
            "path": "https://sharepoint.example/JJJ/concept/T1",
            "sync_status": "Pending",
        },
    )
    assert r.status_code == 201, r.text

    # Stale BIM360 reference.
    r = client.post(
        f"/projects/{pid}/search/connector-references",
        json={
            "source": "BIM360",
            "external_ref": "BIM360-MEP-PR4",
            "path": "bim360://JJJ/T1/PR4",
            "sync_status": "Stale",
        },
    )
    assert r.status_code == 201, r.text

    # Failed Teams reference.
    r = client.post(
        f"/projects/{pid}/search/connector-references",
        json={
            "source": "Teams",
            "external_ref": "TMS-ORAT-W001",
            "path": "https://teams.example/JJJ/ORAT/W-001",
            "sync_status": "Failed",
        },
    )
    assert r.status_code == 201, r.text

    # Unknown index_record_id on connector reference → 404.
    r = client.post(
        f"/projects/{pid}/search/connector-references",
        json={
            "source": "Meridian",
            "external_ref": "MRD-BAD-LINK",
            "path": "/nope",
            "index_record_id": "00000000-0000-0000-0000-000000000000",
        },
    )
    assert r.status_code == 404, r.text

    # List + filters.
    r = client.get(f"/projects/{pid}/search/connector-references")
    assert r.status_code == 200
    assert len(r.json()) == 4

    r = client.get(
        f"/projects/{pid}/search/connector-references",
        params={"sync_status": "Failed"},
    )
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["external_ref"] == "TMS-ORAT-W001"

    r = client.get(
        f"/projects/{pid}/search/connector-references",
        params={"source": "SharePoint"},
    )
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["external_ref"] == "SP-CONCEPT-T1"

    # PATCH a connector reference — Pending → Indexed + link to doc record.
    sp_ref = client.get(
        f"/projects/{pid}/search/connector-references",
        params={"source": "SharePoint"},
    ).json()[0]
    doc_rec = client.get(
        f"/projects/{pid}/search/index", params={"entity_type": "Document"}
    ).json()[0]
    r = client.patch(
        f"/projects/{pid}/search/connector-references/{sp_ref['id']}",
        json={"sync_status": "Indexed", "index_record_id": doc_rec["id"]},
    )
    assert r.status_code == 200, r.text
    assert r.json()["sync_status"] == "Indexed"
    assert r.json()["index_record_id"] == doc_rec["id"]

    # PATCH unknown connector reference id → 404.
    r = client.patch(
        f"/projects/{pid}/search/connector-references/00000000-0000-0000-0000-000000000000",
        json={"sync_status": "Indexed"},
    )
    assert r.status_code == 404, r.text

    # PATCH — index_record_id set to unknown id → 404.
    r = client.patch(
        f"/projects/{pid}/search/connector-references/{meridian_ref_id}",
        json={"index_record_id": "00000000-0000-0000-0000-000000000000"},
    )
    assert r.status_code == 404, r.text

    # ---- Summary rollup ----
    r = client.get(f"/projects/{pid}/search/summary")
    assert r.status_code == 200, r.text
    s = r.json()
    assert s["project_id"] == pid
    assert s["indexed_record_count"] == 4
    assert s["saved_search_count"] == 2
    assert s["connector_reference_count"] == 4
    # After the PATCH above: Meridian(Indexed) + SharePoint(Indexed) = 2 indexed.
    assert s["indexed_connector_count"] == 2
    # Stale + Failed = 2.
    assert s["stale_connector_count"] == 2
    # records_by_type includes Risk / Document / Design / ORAT, one each.
    assert s["records_by_type"] == {
        "Risk": 1,
        "Document": 1,
        "Design": 1,
        "ORAT": 1,
    }
    # records_by_source — Meridian / SharePoint / BIM360 / Teams, one each.
    assert s["records_by_source"] == {
        "Meridian": 1,
        "SharePoint": 1,
        "BIM360": 1,
        "Teams": 1,
    }

    # ---- Connector source pressure ----
    r = client.get(f"/projects/{pid}/search/connector-pressure")
    assert r.status_code == 200, r.text
    by_source = {row["source"]: row for row in r.json()}
    # Four sources represented, none empty.
    assert set(by_source.keys()) == {"Meridian", "SharePoint", "BIM360", "Teams"}
    assert by_source["Meridian"]["indexed_count"] == 1
    assert by_source["SharePoint"]["indexed_count"] == 1
    assert by_source["SharePoint"]["pending_count"] == 0
    assert by_source["BIM360"]["stale_count"] == 1
    assert by_source["Teams"]["failed_count"] == 1
    for row in by_source.values():
        assert row["total_count"] == 1
