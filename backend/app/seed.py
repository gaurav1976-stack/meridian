"""Idempotent seed for local dev.

Creates: 1 tenant, 1 admin user (dev bypass target), 1 project, 1 work package,
2 contracts, a sample schedule activity, and 3 risks. Re-run safely — uses
get-or-create per row.

Run with:
    python -m app.seed

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
from app.models import (  # noqa: F401  (registers all tables)
    AuditLog,
    Contract,
    OpportunityItem,
    Project,
    ProjectMembership,
    RiskItem,
    ScheduleActivity,
    ScheduleFile,
    Tenant,
    User,
    WorkPackage,
)
from app.models.enums import (
    ActivityStatus,
    ContractForm,
    ContractStatus,
    PackageStatus,
    PackageType,
    ProjectStatus,
    RiskCategory,
    RiskStatus,
    ScheduleFileCategory,
    ScheduleFileStatus,
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


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        tenant, _ = _get_or_create(
            db,
            Tenant,
            defaults={"id": str(uuid4()), "region": "EMEA"},
            name="Meridian Demo Tenant",
        )

        admin, _ = _get_or_create(
            db,
            User,
            defaults={
                "id": str(uuid4()),
                "tenant_id": tenant.id,
                "name": "Demo Admin",
                "role": UserRole.tenant_admin,
            },
            email="admin@meridian.local",
        )

        project, project_created = _get_or_create(
            db,
            Project,
            defaults={
                "id": str(uuid4()),
                "name": "Zanzibar International Airport — Terminal Expansion",
                "location": "Zanzibar",
                "status": ProjectStatus.active,
                "stage": "G3 Detailed Design",
                "description": "Reference project seeded for local development.",
            },
            tenant_id=tenant.id,
            code="ZNZ-T1",
        )

        _get_or_create(
            db,
            ProjectMembership,
            defaults={"id": str(uuid4()), "tenant_id": tenant.id, "role": UserRole.tenant_admin},
            project_id=project.id,
            user_id=admin.id,
        )

        package, _ = _get_or_create(
            db,
            WorkPackage,
            defaults={
                "id": str(uuid4()),
                "tenant_id": tenant.id,
                "name": "Terminal Substructure",
                "package_type": PackageType.structural.value,
                "status": PackageStatus.active.value,
            },
            project_id=project.id,
            code="WP-STR-01",
        )

        _get_or_create(
            db,
            Contract,
            defaults={
                "id": str(uuid4()),
                "tenant_id": tenant.id,
                "title": "Main Works Contract",
                "contractor": "Mwanza Construction Ltd.",
                "form": ContractForm.nec4_ecc,
                "status": ContractStatus.active,
                "value_amount": 245_000_000,
                "value_currency": "USD",
            },
            project_id=project.id,
            reference="C-001",
        )
        _get_or_create(
            db,
            Contract,
            defaults={
                "id": str(uuid4()),
                "tenant_id": tenant.id,
                "title": "Lead Designer (PSC)",
                "contractor": "Skyline Architects LLP",
                "form": ContractForm.nec4_psc,
                "status": ContractStatus.active,
                "value_amount": 18_500_000,
                "value_currency": "USD",
            },
            project_id=project.id,
            reference="C-002",
        )

        sf, _ = _get_or_create(
            db,
            ScheduleFile,
            defaults={
                "id": str(uuid4()),
                "tenant_id": tenant.id,
                "category": ScheduleFileCategory.programme_master,
                "status": ScheduleFileStatus.issued,
                "revision": "R3",
                "issued_date": date.today() - timedelta(days=14),
            },
            project_id=project.id,
            title="Programme Master Schedule R3",
        )

        for ext_id, name, days_offset, is_critical, total_float in [
            ("A1000", "Site Establishment", -45, False, 30),
            ("A1010", "Piling — Zone A", -10, True, 5),
            ("A1020", "Pile Cap Construction — Zone A", 14, True, 0),
            ("A1030", "Substructure — Zone A", 60, True, 0),
        ]:
            _get_or_create(
                db,
                ScheduleActivity,
                defaults={
                    "id": str(uuid4()),
                    "tenant_id": tenant.id,
                    "schedule_file_id": sf.id,
                    "package_id": package.id,
                    "name": name,
                    "status": ActivityStatus.in_progress
                    if days_offset < 0
                    else ActivityStatus.not_started,
                    "planned_start": date.today() + timedelta(days=days_offset),
                    "planned_finish": date.today() + timedelta(days=days_offset + 30),
                    "duration_days": 30,
                    "total_float_days": total_float,
                    "is_critical": is_critical,
                    "percent_complete": 50 if days_offset < 0 else 0,
                },
                project_id=project.id,
                activity_id_external=ext_id,
            )

        for code, title, category, l, i in [
            ("R-001", "Piling refusal due to unforeseen rock", RiskCategory.technical, 3, 4),
            ("R-002", "Late issue of MEP detail design", RiskCategory.programme, 4, 4),
            ("R-003", "CAA aerodrome certification delay", RiskCategory.regulatory, 2, 5),
        ]:
            _get_or_create(
                db,
                RiskItem,
                defaults={
                    "id": str(uuid4()),
                    "tenant_id": tenant.id,
                    "title": title,
                    "category": category,
                    "status": RiskStatus.assessed,
                    "likelihood": l,
                    "impact": i,
                    "owner": "Risk Manager",
                    "target_closure_date": date.today() + timedelta(days=120),
                },
                project_id=project.id,
                code=code,
            )

        _get_or_create(
            db,
            OpportunityItem,
            defaults={
                "id": str(uuid4()),
                "tenant_id": tenant.id,
                "title": "Modular pile cap design — value engineering",
                "likelihood": 3,
                "benefit": 4,
                "owner": "Design Manager",
            },
            project_id=project.id,
            code="O-001",
        )

        db.commit()
        if project_created:
            print(f"Seeded tenant {tenant.id} and project {project.code}")
        else:
            print("Seed already present — refreshed any missing rows.")


if __name__ == "__main__":  # pragma: no cover
    seed()
