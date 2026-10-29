# RG-031 — Provider abstraction and per-user model budgets

**Epic:** D — Pipeline · **Depends on:** RG-023, RG-030 · **Estimate:** M · **Labels:** pipeline, api

## Product requirement

**Problem.** v1 hard-splits work between a Claude review client and an OpenAI generation client
with env-var keys and global call caps. v2 needs the same split, but per user, with the user's
keys and their own ceilings.

**User story.** As a user I choose which model handles generation, review, and revision, and I
set how many revision cycles a run may spend.

**Acceptance criteria**
- Three model roles are configurable: generation, review, revision.
- A run stops at my configured budget, and tells me it stopped rather than failing silently.
- A hard server-side ceiling above my setting protects me from a runaway configuration.
- A provider outage produces a retryable, named error — not a stack trace.

## Technical plan

### Files
```
apps/api/resume_api/llm/base.py         LLMClient protocol: complete(system, user, max_tokens)
apps/api/resume_api/llm/anthropic.py    ← v1 claude_client.py
apps/api/resume_api/llm/openai.py       ← v1 openai_client.py
apps/api/resume_api/llm/catalog.py      ← v1 catalog.py, extended with pricing
apps/api/resume_api/llm/factory.py      ← v1 factory.py, now user-scoped
apps/api/resume_api/llm/pricing.py
apps/api/resume_api/pipeline/budgets.py
```

### Budget contract
Defaults are v1's numbers, now per-user editable with a server ceiling:

| Setting | v1 | Default | User max | Server ceiling |
| --- | --- | --- | --- | --- |
| max_revisions | 1 | 1 | 5 | 5 |
| resume_pass_score | 8.0 | 8.0 | 9.5 | — |
| ats_pass_threshold | 80 | 80 | 95 | — |
| max_total_llm_calls | 16 | 16 | 24 | 30 |
| max_openai_calls | 4 | 4 | 8 | 10 |
| max_claude_calls | 8 | 8 | 12 | 16 |
| max_revision_calls | 5 | 5 | 8 | 10 |

### Steps
1. Keep `parse_strict_json_object` from v1's `claude_client.py` — the review and targeting nodes
   depend on strict JSON parsing, and it already handles fenced output.
2. `factory.for_run(user_id, profile)` resolves the three role clients from the profile's model
   choices plus the user's decrypted keys, raising `missing_api_key` before the graph starts.
3. Retries: 3 attempts, exponential backoff with jitter, on 429 and 5xx only. Never retry a 400 —
   that is a prompt bug and retrying burns the user's money.
4. `_ensure_llm_budget` reads the per-run budget object rather than module constants. Exceeding a
   budget raises `BudgetExceeded`, which the graph turns into a persisted warning, exactly as v1
   does — a budget stop still produces usable output.
5. Every call goes through `telemetry.record_llm_call` (RG-007).

### Reuse from v1
`llm/factory.py`, `catalog.py`, `claude_client.py`, `openai_client.py` — ported.
`tests/test_model_catalog.py` — ported. `cli_proxy/` — **dropped**, do not port.

### Tests
- Ported catalog test passes.
- A fake client that always 429s retries three times, then raises `upstream_failed`.
- A 400 is not retried.
- A user budget above the server ceiling is clamped to the ceiling, not honoured.

### Definition of done
Tests green; budgets visible in the run record.

### Out of scope
Settings UI (RG-047).
