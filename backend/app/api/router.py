"""Aggregate every domain router into one API surface.

Add new routers here — nowhere else — so `main.py` stays simple.
"""
from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import (
    accountability,
    auth,
    commercial,
    design,
    documents,
    governance,
    orat,
    projects,
    project_setup,
    reporting,
    risks,
    schedule,
    search,
    system,
)

api_router = APIRouter()
api_router.include_router(system.router, tags=["system"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(project_setup.router, tags=["project-setup"])
api_router.include_router(schedule.router, tags=["schedule"])
api_router.include_router(risks.router, tags=["risks"])
api_router.include_router(risks.opportunities_router, tags=["opportunities"])
api_router.include_router(governance.router, tags=["governance"])
api_router.include_router(commercial.router, tags=["commercial"])
api_router.include_router(design.router, tags=["design"])
api_router.include_router(documents.router, tags=["documents"])
api_router.include_router(accountability.router, tags=["accountability"])
api_router.include_router(orat.router, tags=["orat"])
api_router.include_router(reporting.router, tags=["reporting"])
api_router.include_router(search.router, tags=["search"])
