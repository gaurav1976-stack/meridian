"""Pytest fixtures — spin up an isolated SQLite DB per test.

The app defaults to SQLite anyway; we just force a fresh file per test run and
seed a tenant + admin so the dev-bypass auth works.
"""
from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

# Write the test DB to /tmp to avoid sandbox/path-with-spaces I/O errors.
_TEST_DB = Path("/tmp/_meridian_test.sqlite")


@pytest.fixture(scope="session", autouse=True)
def _configure_env() -> None:
    if _TEST_DB.exists():
        _TEST_DB.unlink()
    os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB}"
    os.environ["ALLOW_DEV_AUTH_BYPASS"] = "true"


@pytest.fixture()
def client() -> TestClient:
    # Import after env vars are set so settings pick up the override.
    from app.db.base import Base
    from app.db.session import engine
    from app import models  # noqa: F401 — register tables
    from app.main import app
    from app.models.core import Tenant, User
    from app.models.enums import UserRole

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    SessionLocal = sessionmaker(bind=engine, future=True)
    with SessionLocal() as db:
        tenant = Tenant(id=str(uuid4()), name="Test Tenant")
        db.add(tenant)
        db.flush()
        admin = User(
            id=str(uuid4()),
            tenant_id=tenant.id,
            name="Test Admin",
            email="admin@test.local",
            role=UserRole.tenant_admin,
        )
        db.add(admin)
        db.commit()

    return TestClient(app)
