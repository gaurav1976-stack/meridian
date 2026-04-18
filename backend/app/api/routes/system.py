"""System-level endpoints: health check and the module registry that drives the
frontend sidebar. Keeping the registry server-side means the UI never has to
hard-code module availability per tenant.
"""
from __future__ import annotations

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter()

# Single source of truth for the module registry. The frontend `Sidebar`
# component fetches this and renders based on `is_enabled`.
MODULE_REGISTRY: list[dict] = [
    {"key": "dashboard", "label": "Dashboard", "icon": "LayoutDashboard", "route": "/dashboard", "is_enabled": True},
    {"key": "projects", "label": "Projects", "icon": "FolderKanban", "route": "/projects", "is_enabled": True},
    {"key": "project-setup", "label": "Project Setup", "icon": "Settings2", "route": "/project-setup", "is_enabled": True},
    {"key": "schedule", "label": "Schedule", "icon": "CalendarClock", "route": "/schedule", "is_enabled": True},
    {"key": "risks", "label": "Risks & Opportunities", "icon": "ShieldAlert", "route": "/risks", "is_enabled": True},
    {"key": "stage-gates", "label": "Stage Gates", "icon": "GitBranch", "route": "/stage-gates", "is_enabled": True},
    {"key": "commercial", "label": "Commercial", "icon": "Banknote", "route": "/commercial", "is_enabled": True},
    {"key": "design", "label": "Design", "icon": "Ruler", "route": "/design", "is_enabled": True},
    {"key": "documents", "label": "Documents", "icon": "FileText", "route": "/documents", "is_enabled": True},
    {"key": "meetings", "label": "Meetings & Actions", "icon": "Users", "route": "/meetings", "is_enabled": True},
    {"key": "orat", "label": "ORAT", "icon": "PlaneTakeoff", "route": "/orat", "is_enabled": True},
    {"key": "reporting", "label": "Reporting", "icon": "BarChart3", "route": "/reporting", "is_enabled": True},
    {"key": "search", "label": "Search", "icon": "Search", "route": "/search", "is_enabled": True},
]


@router.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.api_version,
        "dev_bypass": settings.allow_dev_auth_bypass,
    }


@router.get("/modules")
def list_modules() -> list[dict]:
    """Registry consumed by the Next.js shell to render the sidebar."""
    return MODULE_REGISTRY
