# RG-023 — BYOK provider keys

**Epic:** C — User data · **Depends on:** RG-002, RG-007 · **Estimate:** M · **Labels:** data, api, security

## Product requirement

**Problem.** v1 reads `OPENAI_API_KEY` and `ANTHROPIC_API_KEY` from `.env` — a single operator's
keys. v2 is bring-your-own-key: each user pays for their own runs.

**User story.** As a user I add my Anthropic and OpenAI keys once, see only the last four
characters afterwards, and can rotate or revoke them at any time.

**Acceptance criteria**
- A key is never returned by any API response after it is saved, in any form.
- A key is encrypted at rest with a key the database alone does not hold.
- Starting a run without the required provider key gives a clear, actionable message naming the
  provider — not a 500 from the LLM SDK.
- I can test a key before saving it.

## Technical plan

### Files
```
apps/api/resume_api/crypto.py               envelope encryption helpers
apps/api/resume_api/repositories/keys.py
apps/api/resume_api/routers/keys.py
apps/api/resume_api/llm/credentials.py      resolve keys for a run
```

### Routes
```
GET    /v1/keys                 [{ provider, label, last_four, created_at, last_used_at }]
POST   /v1/keys                 { provider, label, secret } → 201, body has no secret
POST   /v1/keys/test            { provider, secret } → { ok, model_count } — never persists
DELETE /v1/keys/{id}
```

### Steps
1. Encrypt with AES-256-GCM using a data key derived per user from a master key held in the API's
   secret store (never in Postgres). Store `ciphertext = nonce || tag || payload` as bytea.
   `crypto.py` exposes only `seal(user_id, plaintext)` / `open(user_id, ciphertext)`.
2. Decryption happens once per run, in memory, inside the pipeline process. Keys are never bound
   to a log context, never in an exception message, never in `runs` jsonb. The RG-007 redaction
   processor is the second line of defence, not the first.
3. `POST /v1/keys/test` calls the provider's cheapest metadata endpoint (`GET /v1/models`) and
   returns only `ok` and a count.
4. Preflight in the run creator (RG-032): resolve every provider the selected models require; if
   one is missing return `400 missing_api_key` with `details.provider`. The UI deep-links to
   settings from that code.

### Tests
- `seal`/`open` round-trips; a ciphertext sealed for user A fails to open for user B.
- No response schema in the OpenAPI document contains a `secret` field — assert this in a test
  that walks the generated schema.
- A run started without the needed key returns `missing_api_key`, and no LLM call is attempted.
- Redaction test: force an exception carrying a key; assert it is absent from the log output.

### Definition of done
All four tests green; a security note in the README explaining the threat model plainly.

### Out of scope
Billing, usage limits per key, org-shared keys.
