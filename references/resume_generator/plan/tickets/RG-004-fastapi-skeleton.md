# RG-004 — FastAPI application skeleton and API contract

**Epic:** A — Foundations · **Depends on:** RG-001, RG-002 · **Estimate:** M · **Labels:** foundation, api

## Product requirement

**Problem.** Every later API ticket will otherwise re-invent error shapes, pagination, and
settings loading, and the web app will hand-write fetch calls that drift from the server.

**Outcome.** One consistent, typed API surface; the web client is generated from it, so a
breaking server change fails the web typecheck.

**Acceptance criteria**
- Every error response has the same JSON shape.
- `/docs` describes every route accurately.
- The web app imports a generated client; no hand-written `fetch` to the API anywhere.

## Technical plan

### Files
```
apps/api/resume_api/main.py            app factory, CORS, routers, exception handlers
apps/api/resume_api/settings.py        pydantic-settings, fails fast on a missing var
apps/api/resume_api/errors.py          AppError hierarchy + handler
apps/api/resume_api/schemas/common.py  Page[T], ErrorBody, IdResponse
apps/api/resume_api/routers/health.py
apps/api/resume_api/deps.py            db session, current user, blob store
packages/contracts/package.json        openapi-typescript + openapi-fetch
packages/contracts/src/client.ts       typed client factory
scripts/gen-contracts.sh               boots the API, dumps openapi.json, generates TS
```

### Contracts
Error envelope, used by every failure path:
```json
{ "error": { "code": "run_budget_exceeded", "message": "Human sentence.", "details": {} } }
```
`code` is a stable snake_case string the UI can switch on. `message` follows the arey voice:
what happened, then what to do, no exclamation marks.

List responses: `{ "items": [...], "next_cursor": null }`. Cursor pagination, never offset.

### Steps
1. App factory with routers mounted under `/v1`. CORS allows only the web origin from settings.
2. `AppError(code, message, status, details)`; subclasses `NotFound`, `Forbidden`, `Conflict`,
   `BudgetExceeded`, `UpstreamFailed`, `ValidationFailed`. One handler renders them all.
   A bare `Exception` handler logs with a request id and returns `internal_error` — never a stack.
3. Request-id middleware: accept or mint `X-Request-Id`, bind it to structured logs, echo it back.
4. `/v1/health` returns `{status, version, db: ok|degraded}`.
5. `scripts/gen-contracts.sh` runs in CI and fails the build if the committed client is stale.

### Tests
- Error handler: a raised `NotFound` renders the envelope with status 404.
- Settings: a missing required env var raises at import, not at first request.
- Contract freshness check runs in CI.

### Definition of done
`/docs` clean, generated client committed, CI enforces freshness.

### Out of scope
Any domain route.
