# RG-001 — Scaffold the resume-generator monorepo

**Epic:** A — Foundations · **Depends on:** none · **Estimate:** M · **Labels:** foundation, infra

## Product requirement

**Problem.** v1 is a single Python folder with a Streamlit entrypoint. v2 has a web app, an API,
a compile service, and shared packages that must version together.

**Outcome.** A new `resume-generator` repo where `pnpm dev` starts the web app and API together,
and every subsequent ticket has an obvious place to put its files.

**Acceptance criteria**
- `pnpm install && pnpm dev` boots Next.js on :3000 and FastAPI on :8000 from a clean checkout.
- `pnpm lint`, `pnpm typecheck`, `pnpm test` each run across every workspace and pass.
- `README.md` gets a new engineer running in under ten minutes with no tribal knowledge.

## Technical plan

### Files
```
package.json                pnpm workspaces, scripts: dev, build, lint, typecheck, test, ds:sync
pnpm-workspace.yaml         apps/*, packages/*
turbo.json                  task graph + caching
.nvmrc                      22
apps/web/                   create-next-app: TS, App Router, no Tailwind, src dir, ESLint
apps/api/pyproject.toml     uv project, Python 3.12, deps: fastapi uvicorn[standard] pydantic-settings
                            supabase langgraph langgraph-checkpoint-postgres httpx anthropic openai
apps/api/resume_api/__init__.py
apps/api/Makefile           dev, test, lint targets
packages/tokens/            placeholder, filled by RG-010
packages/ui/                placeholder, filled by RG-011
packages/contracts/         placeholder, filled by RG-004
services/latex/             placeholder, filled by RG-035
supabase/                   placeholder, filled by RG-002
.github/workflows/ci.yml    placeholder, filled by RG-008
AGENTS.md                   implementation rules (copy the "Rules" section of plan/README.md)
.env.example                every var any workspace reads, with a comment per line
```

### Steps
1. `pnpm create next-app@latest apps/web --ts --app --src-dir --eslint --no-tailwind --import-alias "@/*"`.
   Tailwind is deliberately off — styling is token-based CSS Modules (ADR-002).
2. Add Turborepo; declare `build` depends on `^build`, and cache `lint`/`typecheck`/`test`.
3. `uv init apps/api` with the dep list above. Add `ruff` + `mypy` (strict on `resume_api`) + `pytest`.
4. Root `dev` script uses `concurrently` to run `turbo dev --filter=web` and `make -C apps/api dev`.
5. Wire `pnpm lint/typecheck/test` to fan out to both ecosystems (turbo for JS, make for Python).
6. Write `AGENTS.md`: no unlisted files, tokens only for visual values, tests ship with the ticket,
   reuse v1 where `plan/01-v1-reuse-map.md` says to.
7. Commit `plan/` into the new repo so implementing models can read their own tickets.

### Tests
- CI-equivalent smoke: fresh clone → install → `pnpm build` succeeds.
- `apps/api`: one `test_smoke.py` asserting the package imports.

### Definition of done
Clean clone to running dev environment in one documented command. No TODOs in `.env.example`.

### Out of scope
Deployment, Docker Compose for the full stack (RG-008), any product code.
