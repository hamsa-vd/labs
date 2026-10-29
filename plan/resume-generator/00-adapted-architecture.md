# ADR-100 — Resume generator inside Ascend

Status: accepted · Date: 2026-09-16 · Supersedes `resume_generator_v2_plan/00-architecture.md`
for the tiers it changes. Everything that ADR does not contradict still holds.

## Context

Three codebases are being combined:

| Source | What it contributes |
| --- | --- |
| `Resume/resume_generator` (v1, Streamlit) | The domain logic. LangGraph pipeline, rubric, template heuristic, JD loader, prompts. **Functional base.** |
| `Resume/ats-checker` | The deterministic ATS scorer, 2.6k lines with its own test suite. |
| `labs/apps/ascend` | The Next.js job tracker and the arey design language. **Design base.** |
| `resume_generator_v2_plan` | The 39-ticket specification. Followed except where the four decisions below override it. |

## Decisions that override the v2 plan

**D100 — The pipeline is a Python sidecar, not a rewrite.**
`resume_agent` and `ats_checker` move to `apps/resume-pipeline` near-verbatim. Rewriting the
scorer or the routing in TypeScript was rejected: the v2 plan names RG-030 and RG-033 as the two
tickets where an invisible regression is most likely, and both are protected only by their
existing Python tests.

**D101 — Ascend owns the UI, the database, and the public surface.**
There is no `apps/web`. The screens in Epic E become routes inside `apps/ascend` under
`/resume/*`, using `@labs/design/arey` and `app/ascend.css`. RG-005, RG-010…013 and RG-048 are
therefore *extensions of the existing shell*, not new scaffolding.

**D102 — Ascend's Postgres and Cloudflare Access replace Supabase Auth, RLS, and Storage.**
- `app_users` is the user table. Every resume row carries `user_id uuid references app_users(id)`.
- Ownership is enforced in the repository layer plus a `user_id = $1` predicate on every query,
  and asserted by a test suite that stands in for RG-002's pgTAP RLS suite.
- Blobs live on the Mac Mini under `RESUME_DOCUMENTS_DIR`, behind the `BlobStore` protocol that
  D1 mandated. "Signed URL" is an HMAC-signed, TTL-bounded token redeemed at an ascend route.
  Swapping to S3 or Supabase Storage is still one class.
- The pipeline binds to `127.0.0.1` and is never internet-reachable. Ascend is the only client.

**D103 — Tests are written blind.**
For each work package, a test-authoring agent writes the suite from the contract alone and never
reads the implementation; a separate implementation agent writes the code from the same contract
and never reads the tests. Neither sees the other's output until both are done. The contract is
the only shared artefact, which is what makes a disagreement between them informative.

## Topology

```
apps/ascend            Next.js 16. All UI, all public HTTP, the durable Postgres schema.
                       Calls the pipeline over http://127.0.0.1:8000 with a shared service token.
apps/resume-pipeline   FastAPI + uv. LangGraph graph, vendored ats_checker, LLM providers,
                       run orchestration, document repositories. No public ingress.
apps/resume-latex      Tectonic in a container. POST /compile → PDF. No network egress.
packages/typescript/
  resume-contracts     Generated TS client from the pipeline's OpenAPI + the mirrored rubric.
```

Data flow for a generation run:

```
browser → ascend route handler (Cloudflare Access identity)
        → POST /v1/runs on the pipeline (service token + user_id)
        → run row written, 202 returned
        → background task streams the graph, appending run_events
browser ← ascend SSE route ← pipeline SSE tail
```

Ascend proxies the SSE stream rather than exposing the pipeline, so Cloudflare Access stays the
single front door.

## What must not be lost from v1

Reproduced from `01-v1-reuse-map.md` because it is the acceptance bar for the port:

1. `route_after_review` terminates on the total-call cap, the revision-call cap, `max_revisions`,
   an empty `failing_documents`, **and a fix-resolution rate below 50% after a revision.**
2. The cover letter is generated exactly once, after the last revision.
3. ATS score gates revision alongside the LLM review score.
4. Warnings are persisted, not merely displayed.
5. A failed ATS check sets `ats_error` and the run continues.
6. A JD shorter than 300 characters is rejected before any LLM call.

## Deliberate deferrals

- **RG-052 (queue migration)** is not built. Its own ticket forbids starting until one of three
  triggers fires; none has. `BackgroundTasks` plus Postgres-resident run state is shipped exactly
  as D4 specifies, which keeps the swap a one-call change.
- **RG-054 (cloud environments)** is adapted, not implemented as written. Ascend deploys to a Mac
  Mini via launchd behind a Cloudflare tunnel; the ticket's Vercel/Fly topology does not apply.
  Its substance — secret discipline, no public LaTeX service, backups, rollback, a go-live
  checklist — is delivered against that deployment instead.
