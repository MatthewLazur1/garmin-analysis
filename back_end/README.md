# Back End

Backend for the Garmin performance analytics app: Garmin Connect + OpenWeatherMap data ingestion, marathon plan persistence, and pace prediction. Built for a **single local user** — there is currently no concept of accounts, multiple users, or remote access.

---

## Current structure

```
back_end/
├── db.py                        # Supabase Postgres engine (SQLAlchemy)
├── constants.py                 # HR targets, default lat/lon, regression window
├── main.py                      # Ad-hoc script entry point (not the app entry point — see front_end/)
├── marathon_objects/
│   ├── marathon_plan_manager.py # PlanRun / PlanWeek / MarathonPlan — in-memory plan object model
│   └── plan_repository.py       # Postgres schema + CRUD for marathon plans
├── report_objects/
│   ├── report_reader.py         # Garmin Connect + OpenWeatherMap API clients
│   ├── report_builder.py        # Feature engineering (weekly mileage, PRs, activity+weather+sleep merges)
│   └── report_manager.py        # Orchestration layer used by front_end/app.py
├── predictive_models/
│   ├── regression_predictive_model.py  # Ridge/LR pace model
│   └── pca_predictive_model.py         # PCA + LR variant
├── garmin_examples/             # Reference scripts/notebooks for the Garmin Connect API (not imported by the app)
└── gc_examples/                 # Additional Garmin Connect reference material
```

### Data flow

```
Streamlit UI (front_end/app.py)
        │
        ▼
  ReportManager  ──────────────┬─────────────────────┐
        │                      │                      │
        ▼                      ▼                      ▼
ReportReader            ReportBuilder          plan_repository
(Garmin + weather        (feature/report          (Postgres CRUD)
 API clients)             assembly)                    │
        │                                               ▼
        ▼                                        Supabase Postgres
 garminconnect lib                          marathon_plans → plan_weeks → plan_runs
```

`ReportManager` is the single orchestration point the front end talks to — it owns a `MarathonPlan` object per loaded plan, a Supabase engine (`back_end/db.py`), and the predictive model instance.

### Persistence today (Supabase)

Marathon plans live in Postgres, not local files:

| Table | Purpose |
|---|---|
| `marathon_plans` | One row per plan: `name` (unique), `start_date`, `race_date` |
| `plan_weeks` | One row per week of a plan, Forieng Key → `marathon_plans` |
| `plan_runs` | One row per day (Mon–Sun) of a week: distance, type, notes, Foriegn Key → `plan_weeks` |

Schema is created on `ReportManager()` construction via `plan_repository.ensure_schema()` — no separate migration step required today.

**Everything else is still local, not in the database:**
- Garmin credentials (`GARMIN_EMAIL` / `GARMIN_PASSWORD`) — `.env`, read by `ReportReader`
- Garmin session token cache — written by the `garminconnect`/`garth` libraries to disk
- OpenWeatherMap API key — `.env`
- `SUPABASE_DB_URL` — `.env`

This is intentional for a local single-user app: credentials never need to leave your machine or be encrypted at rest in a shared database, because nothing shared exists yet.

---

## What's needed for an actual (multi-user, hosted) app

Turning this into something other people could sign up for is a genuine architecture change, not an incremental addition. Rough order of what that requires:

### 1. Identity — Supabase Auth
Enable Supabase Auth (email/password, magic link, or OAuth). This creates an `auth.users` table and gives every signup a UUID. Nothing here today has a "user" concept — the plan/activity tables assume a single implicit owner.

### 2. Ownership on every table
Add `user_id uuid references auth.users(id)` to `marathon_plans` and any future activity/health tables. Change `marathon_plans.name` from a globally-unique constraint to `unique(user_id, name)` — two users will both name a plan "Fall Marathon."

### 3. Row Level Security (RLS)
Postgres policies (`user_id = auth.uid()`) on every table so the database itself enforces that user A can never read or write user B's rows — not just application-level filtering.

### 4. Per-user Garmin credentials
The biggest jump. Today Garmin auth lives in a local `.env` because there's one user. A hosted app needs:
- Each user's Garmin session token stored **server-side**, encrypted at rest, keyed to their `user_id`.
- A flow for users to authenticate their own Garmin account (not yours) — Garmin has no public OAuth app-partner program for this, so this needs careful handling of the login flow and token refresh.
- Never store the raw Garmin password — only the session/refresh tokens the `garminconnect`/`garth` libraries produce.

### 5. A real frontend/auth flow
Streamlit doesn't have first-class session/auth primitives. Multi-user access likely means either:
- A different frontend (FastAPI + a JS framework) with proper session handling, or
- Streamlit with `st.session_state` + `supabase-py`'s auth client as a lighter-weight stopgap.

### 6. Hosting
Local-only stops working the moment there's more than one user — `back_end` (and whatever serves the frontend) needs to run somewhere reachable: a small VM, Fly.io/Railway/Render, etc. This also reopens the credential-storage question for `SUPABASE_DB_URL` and the Anthropic/OpenWeatherMap API keys — they'd move from a local `.env` to the host's secret manager.

### 7. Rate limits and quota per user
Garmin Connect's unofficial API, OpenWeatherMap's free tier, and any LLM usage are currently sized for one person. Multi-user usage needs per-user or global rate limiting so one user's activity doesn't exhaust another's quota (or your API budget).

None of this is required for the current personal-use goal — it's here so the jump in scope is explicit if "an actual app" ever becomes a real target.
