# MISTY Production Deployment Guide

**Stack:** Render (FastAPI backend) + Vercel (Next.js frontend) + Supabase (PostgreSQL)

MISTY no longer depends on SQLite for production. The persistence layer
(`apps/api/database.py`) inspects the `MISTY_DB_URL` environment variable:

| `MISTY_DB_URL` value | Backend driver | Use case |
|---|---|---|
| Not set (default) | `aiosqlite` → `data/misty_brain.db` | Local development, CI |
| `postgresql://...` | `asyncpg` → Supabase/Postgres | Production |

All public `Database` methods keep the same API, so nothing else in the
codebase needs to change.

---

## 1. Supabase (PostgreSQL)

The schema lives in `database/schema_postgres.sql`. On the connected Supabase
project (PostgreSQL 17, ap-south-1) apply it once via the Supabase MCP
migration tool (or the Dashboard → SQL Editor). The schema is
`CREATE TABLE IF NOT EXISTS`-safe, so re-running it is a no-op.

Tables created: `concepts`, `relations`, `episodes`, `brain_states`,
`procedures` with indexes on name/type/source/target/type/timestamp columns.

The Supabase connection string is found in the Dashboard under
Settings → Database → Connection string → Direct. It looks like:

```
postgresql://postgres:<DB_PASS>@db.<project_ref>.supabase.co:5432/postgres
```

Keep the service-role key for backend-only operations; never expose it to
the browser.

## 2. Render (backend)

Two build options, both supported by this repo:

1. **Docker (recommended):** New Web Service → Build & Deploy →
   Repository: `salauddinmir/Misty-Ai` → Build type **Docker**. Render
   auto-detects `Dockerfile`.
2. **Native Python build:** Set Build Command
   `pip install -r requirements.txt` and Start Command
   `uvicorn apps.api.main:app --host 0.0.0.0 --port $PORT` (a `Procfile` is
   also committed). `render.yaml` documents the service blueprint.

### Required environment variables on Render

| Variable | Value |
|---|---|
| `MISTY_DB_URL` | Supabase direct connection string (see above) |
| `PYTHONUNBUFFERED` | `1` |

Optional: `MISTY_LOG_LEVEL`, espeak/ffmpeg for the speech endpoints
(installed in the Docker image).

After deploy, verify: `GET https://<service>.onrender.com/health` →
`{"status":"healthy"}`.

## 3. Vercel (frontend)

The Next.js app at `apps/web/` ships a `vercel.json` describing the build
(`next build`, output `.next`).

1. In the Vercel dashboard, import the GitHub repo `salauddinmir/Misty-Ai`.
2. Set **Root Directory** to `apps/web`.
3. Add the environment variable:

| Variable | Value |
|---|---|
| `NEXT_PUBLIC_API_URL` | `https://<render-service>.onrender.com` |

The frontend routes every API call through `NEXT_PUBLIC_API_URL`
(`apps/web/lib/api.ts`) and derives the WebSocket URL from the same
variable (`apps/web/lib/websocket.ts`), so no code change is needed when
the backend host changes. Local development keeps using the
`next.config.js` rewrite to `localhost:8000`.

## 4. Local development (unchanged)

```bash
pip install -r requirements.txt
PYTHONPATH=$(pwd) uvicorn apps.api.main:app --port 8000
cd apps/web && npm install && npm run dev
```

## 5. CI

GitHub Actions (`.github/workflows/ci.yml`) runs the full test suite on
Python 3.10/3.11/3.12 plus `ruff` on every push to `main`. CI always uses
the SQLite backend (no `MISTY_DB_URL`), which is sufficient because the
persistence layer's logic is driver-uniform.
