"""JWT validation with a developer-mode bypass.

In production set `ALLOW_DEV_AUTH_BYPASS=false` and configure
`JWT_ISSUER` / `JWT_AUDIENCE` / `JWT_JWKS_URL` to your IdP.

Dev mode returns the seed admin principal so the frontend works without IdP.
"""
from __future__ import annotations

from dataclasses import dataclass

import jwt
from fastapi import HTTPException, Request, status
from jwt import PyJWKClient

from app.core.config import settings

_jwks_client: PyJWKClient | None = None


def _get_jwks_client() -> PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        _jwks_client = PyJWKClient(settings.jwt_jwks_url)
    return _jwks_client


@dataclass
class TokenClaims:
    subject: str
    email: str
    role: str
    tenant_hint: str | None = None


def decode_and_validate_token(token: str) -> TokenClaims:
    try:
        client = _get_jwks_client()
        signing_key = client.get_signing_key_from_jwt(token).key
        payload = jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            audience=settings.jwt_audience,
            issuer=settings.jwt_issuer,
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {exc}",
        ) from exc

    return TokenClaims(
        subject=str(payload.get("sub", "")),
        email=str(payload.get("email", "")),
        role=str(payload.get("role", "Viewer")),
        tenant_hint=payload.get("tenant") or payload.get("tid"),
    )


def extract_bearer(request: Request) -> str | None:
    auth = request.headers.get("Authorization") or request.headers.get("authorization")
    if not auth or not auth.lower().startswith("bearer "):
        return None
    return auth.split(" ", 1)[1].strip() or None


def dev_bypass_enabled() -> bool:
    return bool(settings.allow_dev_auth_bypass)
