"""FastAPI bootstrap for Meridian.

This is the ONLY place `app = FastAPI(...)` is called.

Meridian Airport PMO suite
(c) GV Softwares. Developed by Gaurav Vatsa. All rights reserved.
Proprietary software — unauthorised copying, distribution, modification or use prohibited.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.basic_auth import BasicAuthMiddleware
from app.core.config import settings
from app.db.base import Base  # noqa: F401 — imported for MetaData side-effects
from app.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """On startup ensure tables exist (no-op when Alembic has run)."""
    # In production, Alembic owns schema. Keep this as a safety-net for local SQLite.
    if settings.database_url.startswith("sqlite"):
        # Importing the full model tree here ensures metadata is populated.
        import app.models  # noqa: F401

        Base.metadata.create_all(bind=engine)
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.api_version,
        lifespan=lifespan,
        description=(
            "Meridian Airport PMO suite — multi-tenant Programme Management "
            "Information System for airport and major-infrastructure delivery.\n\n"
            "© GV Softwares. Developed by Gaurav Vatsa. All rights reserved. "
            "Proprietary software — unauthorised copying, distribution, modification "
            "or use is prohibited."
        ),
        contact={"name": "Gaurav Vatsa — GV Softwares", "email": "gaurav1976@gmail.com"},
        license_info={"name": "Proprietary — (c) GV Softwares. All rights reserved."},
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # Basic Auth front-door — no-op unless BASIC_AUTH_USER/PASSWORD are set.
    # Add AFTER CORS so preflight OPTIONS still get the right headers.
    app.add_middleware(BasicAuthMiddleware)
    app.include_router(api_router)
    return app


app = create_app()
