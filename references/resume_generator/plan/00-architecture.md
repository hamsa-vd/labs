# ADR-000 — v2 architecture

Status: accepted · Date: 2026-07-31 · Supersedes: the v1 Streamlit monolith

## Context

v1 (`Resume/resume_generator`) is a single-user Streamlit app. It holds genuinely good domain
logic — a LangGraph pipeline, a deterministic ATS scorer, a weighted review rubric, LaTeX
template selection — behind a UI and a storage model that cannot go multi-user. State lives in
`st.session_state`, outputs live on the local filesystem under `companies/<company>/<role>/`,
and the LangGraph checkpointer is a local SQLite file with `check_same_thread=False`.

## Decision

Re-platform to a three-tier system, keeping the domain logic almost unchanged.

| Tier | Technology | Responsibility |
| --- | --- | --- |
| Web | Next.js 15 (App Router, TypeScript, RSC) | All UI. No LLM calls. No LaTeX. |
| API | Python 3.12 + FastAPI | Auth-guarded REST + SSE. Owns the pipeline. |
| Data | Supabase Postgres | Users, applications, runs, templates, prompts, source of truth, keys |
| Blobs | Supabase Storage | `.tex`, `.pdf`, JD snapshots, uploaded resumes |
| Compile | Containerised Tectonic sidecar | LaTeX → PDF, no shell-out from the API process |

### Repository

One repo, `resume-generator`, pnpm + uv workspaces:

```
resume-generator/
  apps/
    web/                 Next.js 15
    api/                 FastAPI
  packages/
    ui/                  React primitives built on arey tokens (RG-011)
    tokens/              Generated CSS vars + TS types, synced from the design-system repo
    contracts/           OpenAPI-generated TS client + shared zod schemas
  services/
    latex/               Tectonic container + tiny HTTP wrapper
  supabase/
    migrations/          SQL migrations, one file per ticket
  plan/                  This folder
  AGENTS.md              Rules for implementing models
```

Monorepo, not polyrepo: the API's OpenAPI schema generates the web client, so they must move
together. Two repos would mean a version-skew problem for a one-person team.

### Service boundaries

- The web app **never** talks to Supabase directly for domain data. It calls the API. The one
  exception is Supabase Auth (session in the browser) and signed-URL downloads from Storage.
- Row Level Security is on for every table anyway, as defence in depth, keyed on `auth.uid()`.
- The API is stateless. A generation run's state lives in Postgres (`runs`, `run_events`), not
  in memory — so a redeploy mid-run resumes rather than loses.

### Generation execution model

v1 runs the LangGraph pipeline synchronously inside the Streamlit process and streams node
events into the UI. v2 keeps LangGraph but moves execution to a background task:

1. `POST /applications/{id}/runs` inserts a `runs` row (`status=queued`), returns immediately.
2. A worker (FastAPI `BackgroundTasks` for v2.0; swap to arq/Redis at RG-052 if concurrency
   demands it) executes the graph, appending one `run_events` row per completed node.
3. `GET /runs/{id}/events` is an SSE endpoint replaying `run_events` then tailing new ones.

This is why the client can reconnect and why the "live generation" screen survives a refresh.

### Multi-tenancy

Every domain row carries `user_id uuid references auth.users`. There is no shared content in
v2.0 — templates, prompts, and source of truth are all per-user, seeded from a system default
on first sign-in. Access is invite-only: a `allowed_emails` table gates the OAuth callback.

### Non-goals for v2.0

Team accounts, sharing, billing, mobile apps, non-Google auth, and a public API.
