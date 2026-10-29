# RG-009 — Continuous integration and quality gates

**Epic:** A — Foundations · **Depends on:** RG-001, RG-004, RG-005, RG-008 · **Estimate:** M · **Labels:** foundation, infra

## Product requirement

**Problem.** A single-maintainer project with small models writing code needs the pipeline, not
the reviewer, to catch mistakes.

**Outcome.** Nothing merges that fails lint, types, tests, migrations, or the contract freshness
check. Merging to `main` deploys.

**Acceptance criteria**
- A PR that breaks the API contract fails CI with a message naming the drift.
- A PR touching `supabase/migrations` runs them against a throwaway database.
- Every gate runs offline in fake-LLM mode (RG-008) — CI never spends money.

## Technical plan

### Files
```
.github/workflows/ci.yml         lint, typecheck, test, migrate, contracts, bootstrap
apps/api/Dockerfile
services/latex/Dockerfile
```

### Steps
1. CI jobs: `web` (eslint, tsc, vitest, playwright), `api` (ruff, mypy strict, pytest),
   `db` (spin Postgres, apply migrations, run the pgTAP RLS suite from RG-002),
   `contracts` (regenerate and `git diff --exit-code`).
2. A `bootstrap` job runs `scripts/bootstrap.sh` (RG-008) on a clean runner and smoke-tests both ports.
3. `LLM_MODE=fake` is forced in CI, and the socket guard from RG-008 fails any test that reaches a provider.
4. Images for `apps/api` and `services/latex` build on every PR so a broken Dockerfile is caught before RG-054 needs it.

### Tests
CI is the test. Add one deliberately-broken branch to prove each gate fires, then delete it.

### Definition of done
Green pipeline on `main`; every gate proven to fire once.

### Out of scope
Deployment and cloud environments — RG-054.
