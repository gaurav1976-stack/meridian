# Meridian — Pilot Demo Deployment Runbook

**© GV Softwares. Developed by Gaurav Vatsa. All rights reserved.**
*Meridian Airport PMO suite is proprietary software. Unauthorised copying, distribution, modification or use is prohibited.*

This runbook covers the **pilot client / investor demo** profile — a single-host
docker-compose stack running on a laptop or a single VM, backed by Postgres 16,
suitable for live walkthroughs and screen-share demos. It is **not** a
production deployment. For multi-tenant production hardening (SSO, backups,
secrets management, observability), see the *Production Hardening* section at
the end.

---

## 1. Prerequisites

| Component        | Minimum version | Notes                                                   |
| ---------------- | --------------- | ------------------------------------------------------- |
| OS               | macOS 13 / Ubuntu 22.04 / Windows 11 + WSL2 | x86_64 or arm64                  |
| Docker Desktop   | 4.30+           | Or Docker Engine 24+ with the compose plugin            |
| RAM available    | 6 GB            | Postgres + FastAPI + Node dev server                    |
| Disk             | 4 GB free       | Image layers + Postgres data volume                     |
| Network ports    | 3000, 5432, 6379, 8000 free | The compose stack binds these on the host   |

No Python, Node, or Postgres install on the host is required — everything runs
in containers.

---

## 2. One-command bring-up

From the `meridian/` repo root:

```bash
./scripts/first-run.sh
```

The helper script will:

1. Copy `.env.example` to `.env` if `.env` is missing.
2. Run `docker compose up --build -d`.
3. Poll the backend `/health` endpoint until it returns 200 OK (up to 3 min).
4. Poll the Next.js dev server on port 3000.
5. Print the demo URLs and seed login.

If you prefer to do it manually:

```bash
cp .env.example .env
docker compose up --build
```

The first build takes 5–10 minutes (downloading base images, building Python
wheels, running `npm install`). Subsequent starts complete in under 30 seconds.

---

## 3. Demo URLs

| Service              | URL                                   |
| -------------------- | ------------------------------------- |
| Frontend (Next.js)   | http://localhost:3000                 |
| Backend (FastAPI)    | http://localhost:8000                 |
| OpenAPI / Swagger    | http://localhost:8000/docs            |
| Health check         | http://localhost:8000/health          |
| Postgres             | localhost:5432 (db: `meridian`)       |
| Redis                | localhost:6379 (currently idle)       |

---

## 4. Demo login (dev-auth bypass)

In `.env` the flag `ALLOW_DEV_AUTH_BYPASS=true` is on by default. The seed
script creates a single admin principal that the backend impersonates for every
request:

| Field   | Value                       |
| ------- | --------------------------- |
| Email   | `admin@meridian.local`      |
| Tenant  | `Meridian Demo Tenant`      |
| Role    | `Tenant Admin`              |
| Project | `ZNZ-T1` (Zanzibar International Airport — Terminal Expansion) |

The seed also creates: 1 work package, 2 contracts (NEC4 ECC + PSC), 1
schedule file with 4 activities, 3 risks, and 1 opportunity. All other module
data (gates, design packages, RFIs, ORAT trials, search index records …) is
empty until you exercise the API or use the UI to add records.

> ⚠️ **Production note:** disable `ALLOW_DEV_AUTH_BYPASS` and wire a real
> JWT issuer (Azure AD, Auth0, or your customer's IdP) before exposing the
> instance to anyone outside your demo team. See *Production Hardening* below.

---

## 5. Recommended demo script (10–15 min walkthrough)

| Step | Module                | What to show                                                                   |
| ---- | --------------------- | ------------------------------------------------------------------------------ |
| 1    | Dashboard             | Tenant context, multi-project portfolio header                                 |
| 2    | Projects → ZNZ-T1     | Project status, stage, membership                                              |
| 3    | Schedule              | Activity register, critical-path flagging, total-float column                  |
| 4    | Stage Gates           | G0–G8 framework, gate evidence checklist                                       |
| 5    | Risks & Opportunities | Pre-seeded R-001/R-002/R-003, 5×5 matrix, opportunity register                 |
| 6    | Commercial            | Contract register (NEC4 ECC + PSC), CE/EWN registers                           |
| 7    | Design                | RIBA stages, design packages, BIM coordination, design interfaces              |
| 8    | Documents             | ISO 19650 status codes (S0–S6), transmittal log, CDE workflow                  |
| 9    | Meetings & Actions    | Meeting register, action accountability, decision log                          |
| 10   | ORAT                  | Workstream readiness, trial register, regulatory gates                         |
| 11   | Reporting             | Report templates, scheduled jobs, archive                                      |
| 12   | Search                | Cross-module index, saved searches, connector pressure                         |

Most modules currently render with empty registers — use the **Swagger UI** at
`/docs` to POST sample records on stage, or pre-script POST calls before the
demo. (A future seed-rich script will do this automatically.)

---

## 6. Common operations

```bash
# Tail all logs
docker compose logs -f

# Tail a single service
docker compose logs -f backend
docker compose logs -f frontend

# Open a shell in the backend container
docker compose exec backend bash

# Run pytest inside the backend container
docker compose exec backend pytest -q

# Open psql against the demo database
docker compose exec postgres psql -U meridian -d meridian

# Re-run seed (idempotent)
docker compose exec backend python -m app.seed

# Re-run migrations (idempotent)
docker compose exec backend alembic upgrade head

# Stop everything (data preserved)
docker compose down

# Stop everything AND drop the database volume (clean slate)
docker compose down -v
```

The `Makefile` at the repo root wraps all of these as `make logs`, `make psql`,
`make test`, `make reset`, etc.

---

## 7. Troubleshooting

### Backend container exits immediately

Almost always one of:

- **Port 8000 already in use** — another process owns it.
  `lsof -i :8000` then `kill <pid>`, or change the host-side port mapping in
  `docker-compose.yml`.
- **Postgres not yet ready** — check `docker compose logs postgres`. The
  backend `depends_on` clause waits for the healthcheck, but if the volume
  is corrupt, Postgres won't start. `docker compose down -v` and re-run
  to rebuild from scratch.
- **Migration failure** — usually a half-applied state from a prior run.
  `docker compose down -v && ./scripts/first-run.sh` to reset.

### Frontend pages return 500 / "ECONNREFUSED localhost:8000"

The frontend container can't reach `localhost:8000` from inside the container.
Confirm `API_BASE_URL=http://backend:8000` is in the frontend service's
`environment:` block in `docker-compose.yml` (it should be set already).
Restart the frontend service:

```bash
docker compose restart frontend
```

### Frontend pages render with the sidebar but no data

The browser uses `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`. Open the
browser console — if you see CORS errors, confirm `CORS_ORIGINS` in `.env`
includes `http://localhost:3000`.

### Browser shows "module pending port" on a sidebar item

The module registry in `backend/app/api/routes/system.py` returns
`is_enabled: false` for that module. All 13 modules are enabled in the current
build, so this should not happen — if it does, check that container logs were
not truncated and that the registry endpoint at
`http://localhost:8000/modules` returns the full list.

### "no space left on device" during build

Docker layer cache filling the disk. Reclaim:

```bash
docker system prune -a --volumes
```

(Note: this also drops the Postgres data volume.)

---

## 8. Backup & restore (demo-grade)

For a pilot client demo where you want to preserve a curated dataset:

```bash
# Backup
docker compose exec postgres pg_dump -U meridian -d meridian -Fc -f /tmp/meridian.dump
docker compose cp postgres:/tmp/meridian.dump ./meridian-demo-backup.dump

# Restore (after `down -v` and bring up)
docker compose cp ./meridian-demo-backup.dump postgres:/tmp/meridian.dump
docker compose exec postgres pg_restore -U meridian -d meridian --clean --if-exists /tmp/meridian.dump
```

For production, replace this with managed RDS snapshots + point-in-time recovery.

---

## 9. Hosting on a single demo VM (optional)

If you want a stable URL for an investor or pilot client to hit between calls,
provision any small Linux VM (4 vCPU / 8 GB RAM is plenty) and:

1. Install Docker + the compose plugin.
2. `git clone` the Meridian repo (or rsync the directory).
3. Run `./scripts/first-run.sh`.
4. Put Nginx in front to terminate TLS:
   - `meridian.example.com` → `proxy_pass http://localhost:3000` (frontend)
   - `api.meridian.example.com` → `proxy_pass http://localhost:8000` (backend)
5. Issue Let's Encrypt certs with `certbot --nginx`.
6. Update `.env`:
   - `NEXT_PUBLIC_API_BASE_URL=https://api.meridian.example.com`
   - `CORS_ORIGINS=https://meridian.example.com`
7. `docker compose up --build -d`.

A sample Nginx config will live in `infra/nginx/` once that profile is wired.

---

## 10a. Hosted demo URL (Render.com)

For a publicly-reachable pilot-demo URL gated by HTTP Basic Auth, see
**[DEPLOY-RENDER.md](./DEPLOY-RENDER.md)**. It covers the GitHub push, the
Render Blueprint apply, the cross-service URL wiring, and the verify step.
Wall-clock: ~25 min on first run.

---

## 10. Production hardening (NOT covered by this runbook)

Before any real-tenant traffic touches an instance, the following must be done.
Each is significant work — do not assume a pilot-demo deploy is production-ready.

| Area               | What's needed                                                                      |
| ------------------ | ---------------------------------------------------------------------------------- |
| **Auth**           | Replace dev-bypass with a real OIDC issuer (Azure AD, Auth0, Keycloak). Rotate JWKs. |
| **Database**       | Move to managed Postgres (RDS / Azure Database for Postgres). Enable PITR + daily snapshots. |
| **Secrets**        | Move `.env` values into a secrets manager (AWS Secrets Manager / Azure Key Vault). |
| **TLS**            | Terminate at a load balancer or a managed reverse proxy. Force HTTPS, HSTS.        |
| **Backups**        | Daily Postgres dump, weekly off-site copy, monthly restore drill.                  |
| **Observability** | Wire structured logging to a log aggregator (CloudWatch / Datadog / Grafana Loki). Add APM.|
| **Audit log**      | The `audit_log` table is already populated by every write — pipe it to a tamper-evident store for SOX/ISO27001. |
| **Rate limiting**  | Put an API gateway in front (AWS API Gateway / Azure APIM) with per-tenant quotas. |
| **Frontend build** | Replace `npm run dev` with `npm run build && npm run start` and run behind a CDN.  |
| **Worker tier**    | Implement `app/workers/run.py` with RQ or Celery for long-running tasks (PDF generation, ingestion). |
| **Scaling**        | Move to ECS/EKS/AKS or Cloud Run; horizontal-scale the backend behind a load balancer. |
| **Compliance**     | Run a DPIA, sign DPAs with all sub-processors, complete the ISO 27001 / SOC 2 readiness checklist. |
| **Disaster Recovery** | RPO/RTO targets agreed with the customer; failover region; runbooks.            |

Treat the pilot-demo deploy as a sales asset, not the start of production
infrastructure. Production deployment is an engagement of its own — a separate
DEPLOY-PROD.md will cover it when the first paying customer is signed.

---

*End of Pilot Deployment Runbook.*
*© GV Softwares. Developed by Gaurav Vatsa. All rights reserved.*
