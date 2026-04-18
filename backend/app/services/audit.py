"""Immutable audit-log writer.

Extracted from the Track A foundation file so every router writes audit
entries the same way. Keep this pure — no HTTP concerns, just a DB call.
"""
from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.core import AuditLog


def write_audit_log(
    db: Session,
    *,
    tenant_id: str,
    actor_user_id: Optional[str],
    entity_type: str,
    entity_id: str,
    action: str,
    details: Optional[Any] = None,
) -> AuditLog:
    """Persist a single audit entry. Caller is responsible for the commit."""
    entry = AuditLog(
        tenant_id=tenant_id,
        actor_user_id=actor_user_id,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        details=None if details is None else str(details),
    )
    db.add(entry)
    db.flush()
    return entry
