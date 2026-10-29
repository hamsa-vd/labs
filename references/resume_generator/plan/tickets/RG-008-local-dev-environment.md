# RG-008 — One-command local development environment

**Epic:** A — Foundations · **Depends on:** RG-001, RG-002 · **Estimate:** M · **Labels:** foundation, infra, dx

## Product requirement

**Problem.** The stack is five moving parts — Next.js, FastAPI, Postgres, Storage, and a LaTeX
compiler — plus three paid LLM providers. Without a scripted local environment, every
implementing model burns its first hour on setup and some of them will reach for a real API key
to run a test.

**Outcome.** `make bootstrap && pnpm dev` produces a fully working app with seeded data, on a
machine with no LaTeX, no Postgres, and no API keys.

**Acceptance criteria**
- A clean machine reaches a working, signed-in app with sample data in under ten minutes.
- The full test suite runs offline, with zero real LLM calls and zero cost.
- Compiling a resume to PDF works locally with no TeX installation.
- A single command resets the database to a known seeded state.

## Technical plan

This ticket is the reason the other 36 can be implemented cheaply. Treat developer experience
here as a product requirement, not a nicety.

### Files
```
Makefile                              bootstrap, dev, reset, seed, test, doctor
docker-compose.dev.yml                supabase stack + latex service
scripts/bootstrap.sh                  preflight checks → install → migrate → seed
scripts/doctor.sh                     diagnose a broken environment
supabase/seed/dev_seed.sql            one demo user with realistic data
apps/api/resume_api/llm/fake.py       deterministic offline LLM client
apps/api/tests/fixtures/llm/*.json    recorded responses per prompt stage
.env.development                      committed; safe non-secret local defaults
```

### The offline LLM client — the important part
`FakeLLMClient` implements the `LLMClient` protocol (RG-031) and returns recorded fixtures keyed
by `(stage, hash(prompt))`, falling back to a generic valid response for that stage. It must
return **schema-valid** output for every stage: strict JSON for targeting and review (so
`parse_strict_json_object` succeeds), compilable LaTeX for generation and revision.

`LLM_MODE=fake` is the default in `.env.development` and in CI. `LLM_MODE=live` requires real
keys and is opt-in, never the default. A test that makes a network call to a provider fails —
enforce it with a socket guard in `conftest.py`.

This is what makes RG-030's graph testable: the whole pipeline, including revision loops, runs
end to end in under two seconds with no money spent.

### Steps
1. `docker-compose.dev.yml` runs the Supabase local stack (Postgres, GoTrue, Storage, Kong) and
   the RG-035 LaTeX container. Nothing else needs Docker.
2. `make bootstrap`: check versions (Node 22, pnpm, uv, Python 3.12, Docker) and print a specific
   fix for each missing one → `pnpm install` → `uv sync` → start compose → apply migrations →
   seed system prompts and templates → seed the demo user.
3. `dev_seed.sql` creates `dev@localhost` in `allowed_emails` and `auth.users` with a known
   password, a populated source of truth derived from `base/source_of_truth.txt`, three
   applications in different statuses, and one completed run with real scores. A seeded app that
   looks like a used app is worth an hour of manual clicking on every ticket in Epic E.
4. Local sign-in bypass: when `AUTH_MODE=local`, a "Sign in as dev@localhost" button appears on
   the sign-in page. It is compiled out entirely unless `NODE_ENV === 'development'` — assert that
   with a test, because an auth bypass reaching production is the worst possible outcome of this
   ticket.
5. `make reset` drops, re-migrates, and re-seeds. `make doctor` reports which of the five services
   is unhealthy and how to fix it.
6. `README.md` gets a "Getting started" section that is exactly these commands and nothing else.

### Tests
- CI runs `scripts/bootstrap.sh` on a clean runner and asserts the app answers on both ports.
- The socket guard: a test attempting a real provider call fails with a clear message.
- A full pipeline run completes in fake mode in under 5 s, with the same node sequence as live.
- The dev sign-in bypass is absent from a production build (assert against the built bundle).

### Definition of done
Four tests green; a second machine bootstraps from the README with no undocumented steps.

### Out of scope
Cloud environments (RG-054).
