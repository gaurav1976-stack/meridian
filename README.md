# Meridian Platform

**© GV Softwares. Developed by Gaurav Vatsa. All rights reserved.**
*Meridian Airport PMO suite is proprietary software. Unauthorised copying, distribution, modification, or use is prohibited.*

Multi-tenant PMO, programme controls, document control, design management, ORAT and enterprise search platform for airport and major-infrastructure programmes.

This repository is the **assembled** Meridian application — produced by consolidating the loose Track A / Integration Pack / JSX module artifacts in `../meridian app/` into a coherent monorepo.

---

## Quick start

```bash
# One-shot bring-up (recommended)
./scripts/first-run.sh

# …or manually
cp .env.example .env
docker compose up --build
```

Alembic migrations and the demo seed run automatically on backend startup via
the compose `command:` — you do not need to run them separately.

For the full pilot-demo deploy runbook (prereqs, demo URLs, demo script,
troubleshooting, production-hardening roadmap), see **[DEPLOY.md](./DEPLOY.md)**.

For a publicly-reachable hosted demo URL (Render.com, Basic Auth front door,
managed Postgres), see **[DEPLOY-RENDER.md](./DEPLOY-RENDER.md)**.

Then:

| Service       | URL                                                     |
| ------------- | ------------------------------------------------------- |
| Frontend (Next.js) | http://localhost:3000                              |
| Backend (FastAPI)  | http://localhost:8000                              |
| API docs (Swagger) | http://localhost:8000/docs                         |
| Postgres           | localhost:5432 (user: `meridian`, db: `meridian`)  |
| Redis              | localhost:6379                                     |

Demo login (dev-auth bypass is on by default):
- Email: `admin@meridian.local`
- Tenant: `Meridian Demo Tenant`
- Role: `Tenant Admin`

---

## Repository layout

```
meridian/
├── backend/                 # FastAPI app
│   ├── app/
│   │   ├── core/            # config, security, permissions
│   │   ├── db/              # Base, engine, session
│   │   ├── models/          # SQLAlchemy ORM (one file per domain)
│   │   ├── schemas/         # Pydantic request/response models
│   │   ├── services/        # cross-cutting service layer
│   │   ├── api/
│   │   │   ├── deps.py      # shared deps (DB, auth, principal)
│   │   │   ├── router.py    # aggregator
│   │   │   └── routes/      # one APIRouter per domain
│   │   ├── workers/         # RQ worker entrypoints
│   │   ├── reports/         # PDF/XLSX report generators
│   │   ├── connectors/      # BIM 360 / SharePoint / MS Graph
│   │   ├── storage/         # local / S3 / Azure adapters
│   │   ├── seed.py          # demo data
│   │   └── main.py          # FastAPI bootstrap + lifespan
│   ├── alembic/             # migrations
│   ├── tests/               # pytest
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/                # Next.js 14 App Router
│   ├── src/
│   │   ├── app/             # routes (one folder per page)
│   │   ├── components/
│   │   │   ├── shell/       # Sidebar, GlobalHeader, AppShell
│   │   │   └── ui/          # shadcn primitives
│   │   └── lib/             # context, types, api client, mocks
│   ├── package.json
│   └── Dockerfile
├── infra/                   # nginx / observability / future
├── scripts/                 # local dev helpers
├── docker-compose.yml
├── Makefile
├── .env.example
└── README.md (this file)
```

---

## Architectural decisions (ADR-style summary)

1. **One Base, one engine, one Settings.** The Track A files in `../meridian app/` each declared their own — that pattern does not scale beyond a single file. Consolidated in `backend/app/db/base.py` and `backend/app/core/config.py`.

2. **Track A modules become `APIRouter`s, not `FastAPI()` apps.** Each domain (project setup, schedule, gates, risks, commercial, design, documents, meetings, ORAT, reporting, search) is mounted by `backend/app/api/router.py`. See `CONVERSION_PLAYBOOK.md` for the mechanical conversion pattern.

3. **Postgres for prod, SQLite for tests.** `Settings.database_url` defaults to a local Postgres URL via docker-compose; pytest overrides it to in-memory SQLite via `conftest.py`.

4. **JWT auth with dev bypass.** `backend/app/core/security.py` validates real JWTs; `ALLOW_DEV_AUTH_BYPASS=true` in `.env` returns the seed admin principal so the frontend works without an IdP. Disable in production.

5. **Single Next.js app hosting all 13 modules.** The 13 JSX modules in `../meridian app/` were 13 independent prototypes; here they become App Router pages under `frontend/src/app/(platform)/<slug>/page.tsx`, all sharing the `MeridianProvider` and shell components.

6. **Stone+navy palette from the JSX modules wins.** The HTML prototype's navy/gold "command centre" theme is preserved as a secondary surface for the Aerodrome Command Centre page only.

---

## What's done in this assembly pass

✅ Repo skeleton + docker-compose + Makefile
✅ Shared backend foundation (config, db, security, permissions, deps, main)
✅ Consolidated core models (Tenant, User, Project, AuditLog, WorkPackage, ProjectMembership)
✅ Reference router conversions: `system`, `auth`, `projects`, `project_setup`, `schedule`, `risks`
✅ Alembic baseline migration
✅ Next.js shell with module registry, sidebar, global header, MeridianProvider, API client
✅ Reference frontend pages: dashboard, projects list, project detail, project setup, schedule, risks
✅ `CONVERSION_PLAYBOOK.md` with the exact mechanical pattern for the remaining 6 backend domains and 7 frontend modules

## What's not done (and how to finish)

🟡 Convert Track A modules 4, 6, 7, 8, 9, 10, 11, 12 to routers — see `CONVERSION_PLAYBOOK.md` §A
🟡 Build the matching Next.js pages for stage-gates, commercial, design, documents, meetings, ORAT, reporting, search — see §B
🟡 Wire Integration Pack Parts 5–10 (workers, storage, reports, connectors) — see §C
🟡 Real JWT IdP (Azure AD / Auth0) — see §D
🟡 Apply search/ingestion stack migrations 0007–0012 — see §E

The pattern is set. Each remaining piece is mechanical translation, not design work.
