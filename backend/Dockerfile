# Meridian Airport PMO suite — backend image
# (c) GV Softwares. Developed by Gaurav Vatsa. All rights reserved.
# Proprietary — unauthorised copying, distribution, modification or use prohibited.

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Build deps for psycopg/openpyxl/reportlab; curl for healthchecks.
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential \
      curl \
    && rm -rf /var/lib/apt/lists/*

# Copy the full source first so that `pip install -e .` can find the `app/`
# package referenced by pyproject.toml. The compose bind-mount overlays /app
# at runtime so live reload still works.
COPY . /app

RUN pip install --upgrade pip && pip install -e ".[dev]"

# Artifact storage volume — created here so it exists even before compose
# attaches the named volume.
RUN mkdir -p /data/artifacts

EXPOSE 8000

# Startup chain (run in a shell so && works): migrate schema, seed, serve.
# - alembic upgrade head is idempotent (no-op on up-to-date DBs)
# - app.seed uses get-or-create, safe to re-run on every container start
# - uvicorn binds 0.0.0.0:8000 for Render/Compose health checks
#
# Render's Docker Command override is tokenized as exec-form (no shell),
# so the chain MUST live in the Dockerfile itself (exec form with an
# explicit /bin/sh -c). Clear any Docker Command override on the service.
CMD ["/bin/sh", "-c", "alembic upgrade head && python -m app.seed && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
