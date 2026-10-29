# RG-050 — Run cost accounting

**Epic:** F — Operations · **Depends on:** RG-007, RG-031 · **Estimate:** S · **Labels:** ops, product

## Product requirement

**Problem.** BYOK means the user pays directly, so the product owes them an honest number. v1
counts calls but not tokens or money.

**User story.** I see what each run cost me and what I have spent this month.

**Acceptance criteria**
- Every run shows a cost broken down by stage.
- A monthly total is visible in settings.
- The estimate shown before a run and the actual after it are within a stated tolerance.

## Technical plan

### Files
```
apps/api/resume_api/llm/pricing.py          per-model input/output prices, dated
apps/api/resume_api/routers/usage.py        GET /v1/usage?from=&to=
apps/web/src/components/result/RunCost.tsx
apps/web/src/components/settings/UsageSection.tsx
```

### Steps
1. `pricing.py` is a plain table with an `as_of` date per entry and a test asserting every model
   in `catalog.py` has a price. A missing price is a hard failure, not a silent zero.
2. `record_llm_call` (RG-007) already captures usage per call; roll it into `runs.cost_usd` and
   keep the per-node breakdown in `runs.token_usage`.
3. `RunCost` renders in the result view: total in mono, expandable to per-stage rows.
4. `UsageSection` shows a monthly total and a simple per-day bar list — no charting library for
   this; a list of rows with proportional widths is enough and stays on-brand.

### Tests
- Every catalogued model has a price.
- A three-call run totals correctly across two providers.
- The pre-run estimate is within 25% of actual for a seeded fixture run.

### Definition of done
Three tests green.

### Out of scope
Budgets that hard-stop on spend, invoicing.
