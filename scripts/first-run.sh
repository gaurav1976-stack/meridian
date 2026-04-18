#!/usr/bin/env bash
# Meridian Airport PMO suite — first-run bring-up helper.
# (c) GV Softwares. Developed by Gaurav Vatsa. All rights reserved.
# Proprietary — unauthorised copying, distribution, modification or use prohibited.
#
# Purpose: run once on a fresh laptop / demo VM to bring up the full stack.
# Copies .env from .env.example if missing, builds & starts docker compose,
# waits for the backend health check to go green, then prints the demo URLs.
#
# Usage:
#   ./scripts/first-run.sh

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

echo "==> Meridian pilot-demo bring-up"
echo "    working dir: $ROOT_DIR"

# --- 1. .env -------------------------------------------------------------
if [[ ! -f .env ]]; then
  echo "==> Creating .env from .env.example"
  cp .env.example .env
else
  echo "==> .env already exists — leaving untouched"
fi

# --- 2. prerequisites ----------------------------------------------------
if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: docker is not installed or not on PATH." >&2
  exit 1
fi
if ! docker compose version >/dev/null 2>&1; then
  echo "ERROR: docker compose plugin is not available." >&2
  echo "       Install Docker Desktop 4.x+, or the docker-compose-plugin apt package." >&2
  exit 1
fi

# --- 3. build + up -------------------------------------------------------
echo "==> docker compose up --build -d"
docker compose up --build -d

# --- 4. wait for backend health -----------------------------------------
echo "==> Waiting for backend to become healthy (up to 3 min)"
ATTEMPTS=0
MAX_ATTEMPTS=36     # 36 * 5s = 3 min
until curl -fsS http://localhost:8000/health >/dev/null 2>&1; do
  ATTEMPTS=$((ATTEMPTS + 1))
  if (( ATTEMPTS >= MAX_ATTEMPTS )); then
    echo "ERROR: backend did not become healthy within 3 minutes." >&2
    echo "       Check logs with:  docker compose logs backend" >&2
    exit 1
  fi
  sleep 5
done
echo "    backend is healthy."

# --- 5. wait for frontend port ------------------------------------------
echo "==> Waiting for frontend to serve on :3000"
ATTEMPTS=0
MAX_ATTEMPTS=36
until curl -fsS http://localhost:3000 >/dev/null 2>&1; do
  ATTEMPTS=$((ATTEMPTS + 1))
  if (( ATTEMPTS >= MAX_ATTEMPTS )); then
    echo "WARN: frontend has not responded yet (Next.js first-run compile can be slow)." >&2
    echo "      It is probably still compiling. Tail with:  docker compose logs -f frontend" >&2
    break
  fi
  sleep 5
done

# --- 6. summary ----------------------------------------------------------
cat <<EOF

==> Meridian is up.

    Frontend (Next.js)   http://localhost:3000
    Backend (FastAPI)    http://localhost:8000
    OpenAPI / Swagger    http://localhost:8000/docs
    Postgres             localhost:5432  (user: meridian / db: meridian)

    Demo login (dev-auth bypass is ON by default):
      Email    admin@meridian.local
      Tenant   Meridian Demo Tenant
      Role     Tenant Admin

    To stop:       docker compose down
    To reset DB:   docker compose down -v && ./scripts/first-run.sh
    Logs:          docker compose logs -f

(c) GV Softwares. Developed by Gaurav Vatsa. All rights reserved.
EOF
