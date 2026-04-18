"""HTTP Basic Auth front-door middleware.

Lightweight shared-secret wrapper used in the pilot-demo deploy profile
(Render.com / single-VM) before a real OIDC issuer is wired. Reads
`BASIC_AUTH_USER` and `BASIC_AUTH_PASSWORD` from the application settings.

Behaviour:
- When either env var is empty → middleware is a no-op (dev / local default).
- When both are set → every request except `/health` and the OpenAPI surface
  (`/openapi.json`, `/docs`, `/redoc`) requires HTTP Basic Auth with those
  credentials. Anything else returns 401 with `WWW-Authenticate: Basic realm`.
- Constant-time comparison via `hmac.compare_digest` to avoid timing oracles.

This is **not** authentication for the application — it sits in front of the
real auth stack as a gate, so the pilot URL isn't crawlable / accidentally
public. Disable in production.

Meridian Airport PMO suite
(c) GV Softwares. Developed by Gaurav Vatsa. All rights reserved.
Proprietary software — unauthorised copying, distribution, modification or use prohibited.
"""
from __future__ import annotations

import base64
import hmac

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings

# Paths that must NEVER require Basic Auth — the host platform's healthcheck
# probe (Render, Docker, k8s) hits /health and expects 200 without creds.
_BYPASS_PATHS = {"/health"}


def _is_bypassed(path: str) -> bool:
    if path in _BYPASS_PATHS:
        return True
    # Allow OpenAPI surface to remain accessible behind the same shared
    # secret? No — keep them gated. If you want them public, add to bypass.
    return False


def _credentials_match(auth_header: str, expected_user: str, expected_pw: str) -> bool:
    """Parse `Basic <base64>` and constant-time compare to expected creds."""
    if not auth_header.lower().startswith("basic "):
        return False
    try:
        decoded = base64.b64decode(auth_header.split(" ", 1)[1].strip()).decode("utf-8")
    except Exception:  # noqa: BLE001 — any decode failure = bad creds
        return False
    if ":" not in decoded:
        return False
    user, _, pw = decoded.partition(":")
    user_ok = hmac.compare_digest(user.encode("utf-8"), expected_user.encode("utf-8"))
    pw_ok = hmac.compare_digest(pw.encode("utf-8"), expected_pw.encode("utf-8"))
    return user_ok and pw_ok


class BasicAuthMiddleware(BaseHTTPMiddleware):
    """Gate every request behind HTTP Basic Auth when configured.

    No-op when `basic_auth_user` or `basic_auth_password` is empty so local
    dev (and existing tests) are unaffected.
    """

    async def dispatch(self, request: Request, call_next):  # noqa: D401
        user = settings.basic_auth_user
        pw = settings.basic_auth_password
        if not user or not pw:
            # No-op mode — middleware disabled.
            return await call_next(request)

        if _is_bypassed(request.url.path):
            return await call_next(request)

        auth_header = request.headers.get("authorization", "")
        if _credentials_match(auth_header, user, pw):
            return await call_next(request)

        return Response(
            status_code=401,
            content="Authentication required.",
            headers={"WWW-Authenticate": 'Basic realm="Meridian"'},
            media_type="text/plain",
        )
