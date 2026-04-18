# Meridian — Hosted Pilot Demo on Render.com

**© GV Softwares. Developed by Gaurav Vatsa. All rights reserved.**
*Meridian Airport PMO suite is proprietary software. Unauthorised copying,
distribution, modification or use is prohibited.*

Companion to [DEPLOY.md](./DEPLOY.md). Takes Meridian from a local laptop
stack to a publicly-reachable URL on Render.com, gated by HTTP Basic Auth.
End-to-end wall-clock time on first run: ~25 minutes, most of which is
Render's free-tier build time.

---

## What this runbook gives you

- A public HTTPS URL like `https://meridian-frontend.onrender.com`.
- A shared-secret Basic Auth prompt as the front door.
- A managed Postgres 16 instance, wired to the backend automatically.
- The full seed dataset (tenant, admin, project ZNZ-T1, risks, contracts).

## What it does **not** give you

- Real SSO / OIDC. `ALLOW_DEV_AUTH_BYPASS=true` remains on inside the Basic
  Auth wrapper.
- High availability, backups, or SLA. Render's free tier sleeps after 15
  minutes of inactivity and the managed Postgres instance is deleted after
  90 days.
- Production observability, rate limiting, or multi-tenant isolation beyond
  the app-layer checks.

Treat this as a **sales / investor demo URL**, not a production deployment.
See DEPLOY.md §10 (Production Hardening) before any real tenant traffic
touches an instance.

---

## 1. One-time prerequisites (on your laptop)

| Tool | Install | Verify |
| ---- | ------- | ------ |
| git  | `brew install git` (macOS) / already present on most Linux | `git --version` |
| gh CLI | `brew install gh` / https://cli.github.com/ | `gh --version` |
| gh auth | `gh auth login` — GitHub.com → HTTPS → browser | `gh auth status` |
| Render account | https://dashboard.render.com — free tier | — |
| Render → GitHub | Render dashboard → Account Settings → GitHub → **Connect account** | — |

The Render ↔ GitHub connection is the step most people miss. Without it the
Blueprint apply step can't see your repo.

---

## 2. Push the repo to GitHub (5 min)

From the `meridian/` directory on your laptop:

```bash
./scripts/push-to-github.sh
```

Default behaviour: creates a **private** repo called `meridian` under your
GitHub account and pushes `main`. Override with environment variables:

```bash
REPO_NAME=meridian-pilot VISIBILITY=private ./scripts/push-to-github.sh
```

The script is idempotent — if the repo or the `origin` remote already
exists it will just push.

Confirm by opening the repo URL the script prints. You should see
`render.yaml` at the root.

---

## 3. Pick your Basic Auth credentials

Pick now; you'll paste them in the Render UI in step 5.

- **User:** anything short. Suggest `meridian-demo`.
- **Password:** treat as a shared secret — 24+ random characters. Generate with:

  ```bash
  LC_ALL=C tr -dc 'A-Za-z0-9' </dev/urandom | head -c 32 ; echo
  ```

Write them down in your password manager. Same pair is entered twice (once
per service — backend and frontend).

---

## 4. Apply the Blueprint in Render (2 min of clicking + 15 min of builds)

1. **Render dashboard → Blueprints**
   https://dashboard.render.com/blueprints
2. Click **New Blueprint Instance**.
3. Under *Connect a repository*, pick the `meridian` repo you just pushed.
   If it doesn't appear: click **Configure account** and grant Render
   access to this repo.
4. Give the Blueprint instance a name — e.g. `meridian-pilot`.
5. Render parses `render.yaml` and shows three resources to be created:

   | Resource | Type | Plan |
   | -------- | ---- | ---- |
   | `meridian-postgres` | Postgres | Free |
   | `meridian-backend`  | Web Service (Docker) | Free |
   | `meridian-frontend` | Web Service (Docker) | Free |

6. Render will prompt you for the `sync: false` env values. Fill as
   follows:

   | Service | Key | Value |
   | ------- | --- | ----- |
   | meridian-backend  | `CORS_ORIGINS`         | Leave blank for now — you'll set this after step 5 when the frontend URL is known. Or put `*` for the duration of the demo. |
   | meridian-backend  | `BASIC_AUTH_USER`      | (your chosen user) |
   | meridian-backend  | `BASIC_AUTH_PASSWORD`  | (your chosen password) |
   | meridian-frontend | `NEXT_PUBLIC_API_BASE_URL` | Leave blank for now — fill after step 5 with the backend URL. |
   | meridian-frontend | `BASIC_AUTH_USER`      | (same user as above) |
   | meridian-frontend | `BASIC_AUTH_PASSWORD`  | (same password as above) |

7. Click **Apply**. Render provisions Postgres first, then builds both
   Docker services in parallel. First build is 10–15 minutes; watch the
   Events tab on each service.

---

## 5. Wire the cross-service URLs (2 min)

Once both services show **Live**, Render has assigned them public URLs like:

- Backend:  `https://meridian-backend.onrender.com`
- Frontend: `https://meridian-frontend.onrender.com`

(Your URLs may include a numeric suffix if those names are taken. Check
each service's dashboard page — top right.)

1. **meridian-backend → Environment tab**:
   - Set `CORS_ORIGINS` = `https://meridian-frontend.onrender.com`
     (no trailing slash).
2. **meridian-frontend → Environment tab**:
   - Set `NEXT_PUBLIC_API_BASE_URL` = `https://meridian-backend.onrender.com`.
3. Both services will auto-redeploy when you save. Wait ~3 minutes.

*Why this is manual:* Render doesn't let one service in a Blueprint
reference another service's **public URL** at Blueprint-apply time (the
URLs don't exist yet). The internal `API_BASE_URL` (server-side SSR) is
wired via `fromService.hostport` in `render.yaml` and needs no touch.

---

## 6. Verify (1 min)

Open a private/incognito window and hit the frontend URL. You should get:

- An HTTP Basic Auth prompt (browser-native modal).
- After entering the user+password from step 3: the Meridian dashboard,
  logged in as `admin@meridian.local` under `Meridian Demo Tenant`,
  showing project `ZNZ-T1`.

Smoke tests (from your laptop, with your Basic Auth creds):

```bash
# Backend health — Basic Auth bypass path
curl -fsS https://meridian-backend.onrender.com/health
# → {"status":"ok"}

# Backend modules — Basic Auth required
curl -fsS -u 'meridian-demo:<password>' \
  https://meridian-backend.onrender.com/modules | jq '. | length'
# → 13
```

---

## 7. Troubleshooting

### Frontend shows Basic Auth prompt but dashboard fails to load data

Browser console shows `Failed to fetch` or CORS errors. Either:

- Step 5.1 not done — `CORS_ORIGINS` still has the default. Set it to the
  frontend's exact origin.
- `NEXT_PUBLIC_API_BASE_URL` wasn't set before the frontend build that
  Render ran. Open the frontend service → *Manual Deploy* → *Clear build
  cache and deploy*.

### 502 Bad Gateway on the backend

Check the backend's *Logs* tab. Most common cause: Alembic migration
failed (Render killed the container before it finished booting). Usually
transient on cold-wake — click *Manual Deploy* → *Deploy latest commit*.

If persistent: open a shell from the dashboard and run:

```bash
alembic upgrade head
python -m app.seed
```

### Backend stuck in "Build failed — process exited with code 137"

Out-of-memory during build. The free tier has 512 MB. Workarounds:

- Upgrade the backend service to the Starter plan ($7/mo, 512 MB RAM,
  same build but without the OOM killer on heavy layers).
- Temporarily comment out `psycopg[binary]` and use a pre-built wheel
  via `uv` — see DEPLOY.md §10.

### Free-tier Postgres about to expire

Render free Postgres lives for 90 days. Inside the Render dashboard, the
database page will show the expiry. Either:

- Upgrade to the $7/mo Starter plan (no expiry).
- Back up first (`pg_dump`) and let the free instance rotate — the
  Blueprint will re-provision on next apply.

---

## 8. Turning it off

```
Render dashboard → each of the three resources → Settings → Delete.
```

Or delete the Blueprint instance, which tears down all three atomically.

Your GitHub repo is untouched; re-apply the Blueprint any time.

---

## 9. Promotion path (beyond pilot)

When this URL graduates from demo-for-a-prospect to anything more serious:

1. Disable `ALLOW_DEV_AUTH_BYPASS` and wire a real OIDC issuer (Azure AD /
   Auth0 / Keycloak). See DEPLOY.md §10 → Auth.
2. Replace Basic Auth middleware with an IP allow-list at the Render edge
   or drop it entirely once SSO is live.
3. Move Postgres off the free plan (or to RDS / Azure Database for
   Postgres) and wire PITR + snapshots.
4. Move secrets from Render env to a secrets manager.
5. Add a CDN in front of the frontend (Cloudflare).

Everything in this runbook is a sales asset. The hard questions — SOC 2
readiness, DPAs, customer DPIA — still need answering before you take a
production cheque.

---

*End of Render Pilot Deployment Runbook.*
*© GV Softwares. Developed by Gaurav Vatsa. All rights reserved.*
