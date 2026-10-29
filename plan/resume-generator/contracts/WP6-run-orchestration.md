# WP6 — Run orchestration and live progress

Discharges RG-032. Decision D4 stands: FastAPI `BackgroundTasks` with all run state in Postgres,
so moving to a real queue later is an enqueue-call change rather than a redesign. **RG-052 is not
in scope** — its own ticket forbids starting until one of three triggers fires, and none has.

Root: `apps/resume-pipeline/`.

The problem this solves: a generation takes minutes and makes up to sixteen paid LLM calls. In v1
it ran inside the Streamlit process, so closing the tab lost the run and the money spent on it.

---

## 1. `resume_pipeline/services/run_events.py`

```python
@dataclass(frozen=True)
class RunEvent:
    seq: int
    node: str
    status: Literal["completed", "failed", "started", "cancelled"]
    label: str
    payload: dict[str, Any]
    at: datetime

NODE_LABELS: dict[str, str]

async def append(conn, run_id: str, *, node: str, status: str, payload: dict) -> RunEvent: ...
async def replay(conn, run_id: str, after_seq: int = 0) -> list[RunEvent]: ...
async def tail(run_id: str, after_seq: int = 0) -> AsyncIterator[RunEvent]: ...
```

- `seq` is allocated per run, gapless and monotonic, by `select coalesce(max(seq),0)+1 … for
  update` inside the same transaction as the insert. Ordering is what makes replay exact.
- `label` is computed **server-side** from `NODE_LABELS` so the client never maps node names to
  prose. The ten labels are exactly those in RG-042:
  `resolve_jd_input` "Read the job description" · `load_inputs` "Loaded your source of truth" ·
  `create_targeting_brief` "Built the targeting brief" · `generate_resume` "Wrote the resume" ·
  `review_documents` "Reviewed against the rubric" · `ats_check_resume` "Scored for ATS" ·
  `revise_documents` "Revised the resume" · `generate_cover_letter` "Wrote the cover letter" ·
  `persist_outputs` "Saved" · `compile_pdfs` "Compiled the PDF".
  An unknown node falls back to the node name rather than raising.
- **`payload` carries only scalars.** Never a document body, never `jd_text`, never `.tex`. The
  useful fields are `resume_score`, `ats_total_score`, `revision_count`, `elapsed_ms`. A test must
  assert that a state containing a large `final_resume_tex` produces an event whose serialised
  payload does not contain it — this is the leak that would put a resume into the event log.
- `tail` listens on the `resume_run_events` Postgres channel (the trigger already exists in
  migration 0006) and yields new events. It must not busy-poll.

## 2. `resume_pipeline/services/run_service.py`

```python
@dataclass(frozen=True)
class RunRequest:
    application_id: str
    template_id: str | None = None
    compile_pdf: bool = True
    kind: Literal["generate", "import", "apply_keywords"] = "generate"

async def create(conn, user_id: str, request: RunRequest) -> str: ...      # returns run_id
async def execute(run_id: str, user_id: str) -> None: ...                 # the background task
async def cancel(conn, user_id: str, run_id: str) -> None: ...
async def sweep_stale(conn, *, older_than_minutes: int = 30) -> int: ...
```

### `create` — preflight, in this order, all before any LLM call

1. The application exists and belongs to the caller, else `NotFound`.
2. `jd_text` is present and at least `MIN_JD_TEXT_LENGTH` (300) characters, else `400
   jd_too_short`. **No run row is created.** This is v1's guard and it must fire before anything
   is spent.
3. A template is selected or recommendable, else `400 template_unavailable`.
4. Every provider key the selected models require resolves, else `400 missing_api_key` with
   `details.provider`. In fake mode this check is skipped entirely.
5. Only then: insert `resume_runs(status='queued')` and return. The caller gets a run id before
   any work starts.

Each failure is a 400 with a named, stable code the UI switches on.

### `execute` — the background task

- Claims the run with `update resume_runs set status='running', started_at=now() where id=$1 and
  status='queued' returning *`. **No row returned means someone else has it — return immediately.**
  That claim is what makes the later move to a queue safe, and it costs nothing now.
- Assembles `RunInputs` (WP5): renders the source of truth, resolves the six prompt bodies and
  their versions, loads the template `tex_source`, clamps the budget.
- Iterates `stream_graph`, and for each `(node_name, node_state)` yielded appends a `run_events`
  row **and** applies the run's partial update **in the same transaction**. A visible event whose
  state was not saved is worse than a slow one.
- Between nodes, re-reads `status`. If it is `cancelled`, stop. A mid-node LLM call is allowed to
  finish — killing it wastes money already spent.
- Terminal states always write `finished_at`, and `error` on failure. The user-facing `error` is
  one sentence; the detail goes to the log.
- An exception anywhere marks the run `failed` with the failing node recorded, and **does not
  raise out of the background task** — an unhandled exception in a background task is silent.

### `cancel` and `sweep_stale`

`cancel` sets `status='cancelled'` and appends a final event. It is idempotent: cancelling an
already-terminal run is a no-op, not an error.

`sweep_stale` runs at startup and marks runs stuck in `running` for over 30 minutes as `failed`
with a stale-run message, and re-queues runs stuck in `queued`. A crashed process must not leave a
run spinning forever in the UI.

## 3. `resume_pipeline/routers/runs.py`

```
POST   /v1/applications/{id}/runs      {template_id?, compile_pdf} → 202 {"run_id": "..."}
GET    /v1/runs/{id}                   full run record
GET    /v1/runs/{id}/events            SSE; ?after_seq=N
POST   /v1/runs/{id}/cancel            → 200
GET    /v1/runs/active                 the caller's in-flight run, or null
```

The SSE handler replays everything after `after_seq` from the table, then tails. It emits a
heartbeat comment every 15 seconds so a proxy does not drop the connection, and closes cleanly
when the run reaches a terminal state. Every route scopes by `user_id`; another user's run id is
`NotFound`.

## Acceptance criteria

1. `create` returns a run id before any LLM call is made — assert with a counting fake client.
2. A 200-character JD is rejected with `jd_too_short` and **no `resume_runs` row is created**.
3. A missing provider key in live mode returns `missing_api_key` with `details.provider`, no run
   row, and no LLM call attempted.
4. Start → every node event appears in order with gapless `seq` → the run reaches `succeeded`.
5. Disconnect after seq 3 and reconnect with `after_seq=3`: events 4..n arrive with no gap and no
   duplicate.
6. Cancel mid-run: status becomes `cancelled` and no further `run_events` are appended after the
   current node.
7. Cancelling an already-succeeded run is a no-op and returns success.
8. Two workers calling `execute` on the same run: exactly one does the work — assert the claim.
9. An exception inside the graph marks the run `failed` with the failing node named, and does not
   propagate out of the background task.
10. `sweep_stale` fails a run that has been `running` for 31 minutes and leaves a 29-minute one alone.
11. An event payload never contains a document body — assert against a state carrying a large
    `final_resume_tex` and a long `jd_text`.
12. Another user's run id returns `NotFound` from every route, including the SSE one.
13. A full fake-mode run completes in under five seconds.

## Test paths (test agent writes only here)

```
tests/services/test_run_events.py
tests/services/test_run_service.py
tests/services/test_run_preflight.py
tests/routers/test_runs_router.py
tests/routers/test_run_sse.py
```

Postgres-backed; read `RESUME_DATABASE_URL` then `TEST_DATABASE_URL` and skip cleanly when absent.
Dev database: `postgres://ascend:ascend@127.0.0.1:55432/ascend`. Use `FakeLLMClient` throughout.
Do **not** run `make reset` — other agents share that database.

## Source paths (implementing agent writes only here)

```
resume_pipeline/services/run_events.py
resume_pipeline/services/run_service.py
resume_pipeline/services/run_sink.py       (the RunSink/Compiler implementations WP5 declares)
resume_pipeline/routers/runs.py
resume_pipeline/schemas/runs.py
```
