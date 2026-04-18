"""Single source of truth for Meridian backend configuration.

Every module imports `settings` from here — never redeclare Settings.

Meridian Airport PMO suite
(c) GV Softwares. Developed by Gaurav Vatsa. All rights reserved.
"""
from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    # ----- App -----
    app_name: str = "Meridian API"
    api_version: str = "0.1.0"
    debug: bool = True

    # ----- Database -----
    database_url: str = "sqlite:///./meridian.db"

    # ----- Redis / queues -----
    redis_url: str = "redis://localhost:6379/0"

    # ----- CORS -----
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    # ----- Auth -----
    jwt_audience: str = "meridian-api"
    jwt_issuer: str = "https://example.com/oauth2"
    jwt_jwks_url: str = "https://example.com/.well-known/jwks.json"
    allow_dev_auth_bypass: bool = True

    # ----- Storage -----
    artifact_storage_provider: str = "local"
    artifact_storage_local_dir: str = "/data/artifacts"

    # ----- Vector / retrieval -----
    vector_store_provider: str = "mock"
    embedding_provider: str = "mock"
    embedding_model_name: str = "mock-deterministic-32d"
    hybrid_keyword_weight: float = Field(default=0.30, ge=0, le=1)
    hybrid_chunk_weight: float = Field(default=0.30, ge=0, le=1)
    hybrid_semantic_weight: float = Field(default=0.40, ge=0, le=1)

    # ----- Connectors -----
    aps_client_id: str = ""
    aps_client_secret: str = ""
    aps_default_hub_id: str = ""
    ms_graph_tenant_id: str = ""
    ms_graph_client_id: str = ""
    ms_graph_client_secret: str = ""

    # ----- Seeding -----
    default_tenant_name: str = "Meridian Demo Tenant"

    # ----- Basic Auth front door -----
    # When both are set, a small middleware gates every request except /health
    # behind HTTP Basic Auth. Intended as a lightweight shared-secret wrapper
    # for pilot-demo hosting (Render.com, single-VM) before a real IdP is wired.
    # When either is empty the middleware is a no-op.
    basic_auth_user: str = ""
    basic_auth_password: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
