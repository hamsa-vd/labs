# RG-007 — Structured logging, errors, and run telemetry

**Epic:** A — Foundations · **Depends on:** RG-004 · **Estimate:** S · **Labels:** foundation, ops

## Product requirement

**Problem.** A generation run makes up to sixteen LLM calls across three providers. When one
fails or a run costs more than expected, there must be a record of why.

**Outcome.** Every run is reconstructable after the fact: which node, which model, how many
tokens, how long, what failed.

**Acceptance criteria**
- Any run id can be traced end to end from the logs.
- A failed run shows the user a plain sentence and the operator a full trace.
- No API key, resume body, or JD text is ever written to a log.

## Technical plan

### Files
```
apps/api/resume_api/logging.py       structlog JSON config, secret redaction processor
apps/api/resume_api/telemetry.py     record_llm_call(run_id, node, provider, model, usage, ms)
apps/web/src/lib/errors.ts           error code → user sentence map
```

### Steps
1. structlog to JSON on stdout. Bind `request_id`, `user_id`, `run_id` for the request's lifetime.
2. A redaction processor drops keys matching `api_key|authorization|ciphertext|tex|jd_text|
   resume_text` and truncates any string over 500 chars.
3. `record_llm_call` appends to `runs.token_usage` jsonb and increments `runs.cost_usd` using a
   static price table in `llm/pricing.py`.
4. Sentry on both apps, with the same redaction rules and `request_id` as a tag.
5. `errors.ts` maps each server `code` to arey-voice copy. Unknown codes fall back to
   "Something failed on our side. Try again in a moment."

### Tests
- The redaction processor removes each named key, verified per key.
- `record_llm_call` accumulates cost correctly over three calls.

### Definition of done
A deliberately failed run produces one traceable log chain and zero secret leaks.

### Out of scope
Dashboards, alerting.
