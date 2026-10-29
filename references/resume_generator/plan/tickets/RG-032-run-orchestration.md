# RG-032 — Run orchestration and live progress

**Epic:** D — Pipeline · **Depends on:** RG-030, RG-031, RG-006 · **Estimate:** L · **Labels:** pipeline, api

## Product requirement

**Problem.** v1 streams graph nodes straight into the Streamlit process. If the tab closes, the
run is gone. A generation takes minutes and makes real, paid LLM calls — losing one is expensive.

**User story.** As a user I start a generation, watch each stage complete, navigate away, close
the tab, come back, and still see the run's progress and its result.

**Acceptance criteria**
- Starting a run returns immediately with a run id.
- Progress is visible within a second of each stage completing.
- Refreshing the page mid-run resumes the live view with no lost events.
- A failed run shows which stage failed and why, in one sentence.
- A run can be cancelled, and cancelling stops further LLM spend.

## Technical plan

Decision D4: FastAPI `BackgroundTasks` for v2.0, with run state entirely in Postgres so the swap
to a real queue is an enqueue-call change.

### Files
```
apps/api/resume_api/routers/runs.py
apps/api/resume_api/services/run_service.py     create, execute, cancel
apps/api/resume_api/services/run_events.py      append + SSE tail
apps/web/src/hooks/useRunStream.ts
```

### Routes
```
POST   /v1/applications/{id}/runs      { template_id?, compile_pdf } → { run_id } (202)
GET    /v1/runs/{id}                   full run record
GET    /v1/runs/{id}/events            SSE: replay all, then tail
POST   /v1/runs/{id}/cancel
```

### Event contract
One event per completed graph node, plus lifecycle events:
```json
{ "seq": 4, "node": "review_documents", "status": "completed",
  "label": "Reviewed against the rubric",
  "payload": { "resume_score": 8.4, "revision_count": 0 },
  "at": "2026-07-31T14:02:11Z" }
```
`label` is arey-voice display copy computed server-side, so the client never maps node names to
prose. `payload` carries only scalars — never document bodies.

### Steps
1. `POST /runs` validates: JD present and ≥ 300 chars (v1's `MIN_JD_TEXT_LENGTH`), keys resolvable
   (RG-023), a template selected or recommendable. It writes `runs(status='queued')` and returns
   before any LLM call. All preflight failures are 400s with named codes.
2. Execution wraps v1's `stream_graph` generator: for each `(node_name, node_state)` yielded,
   append a `run_events` row in the same transaction as the `runs` partial update. Ordering comes
   from a per-run `seq` sequence, so replay is exact.
3. SSE handler: `?after_seq=N` replays everything after N from the table, then tails via Postgres
   `LISTEN/NOTIFY`. Heartbeat comment every 15 s so proxies do not drop the connection.
4. `useRunStream` reconnects with the last seen `seq`, so a refresh or a dropped connection loses
   nothing. On `succeeded` it invalidates the run query and stops.
5. Cancellation sets `runs.status='cancelled'`; the executor checks the flag between nodes and
   stops. Mid-node LLM calls are allowed to finish — killing them wastes the spend already made.
6. Terminal states always write `finished_at`, and `error` on failure. A crashed process leaves a
   run `running`; a startup sweep marks runs older than 30 minutes as `failed` with a stale-run
   message.

### Reuse from v1
`graph.stream_graph` — the streaming generator already yields exactly the right granularity.
v1's `app.py run_generation` shows which node names map to which user-facing stage labels.

### Tests
- Start → all events appear in order → run reaches `succeeded`.
- Disconnect after seq 3, reconnect with `after_seq=3`, receive 4..n with no gap and no duplicate.
- Cancel mid-run: status is `cancelled`, and no further `run_events` are appended.
- Preflight: a 200-char JD is rejected with `jd_too_short` and no run row is created.

### Definition of done
Four tests green; a refresh mid-run visibly resumes.

### Out of scope
The generation screen UI (RG-042).
