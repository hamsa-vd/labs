# RG-052 — Move run execution to a queue (conditional)

**Epic:** F — Operations · **Depends on:** RG-032 · **Estimate:** M · **Labels:** ops, pipeline

## Product requirement

**Problem.** `BackgroundTasks` ties a run's execution to the lifetime of one API process. A
deploy mid-run, or more than a handful of concurrent runs, becomes a real problem.

**Trigger — do not start this ticket until one of these is true:**
- more than five concurrent runs are observed, or
- a deploy has interrupted a run in production, or
- p95 run latency degrades measurably under load.

**Acceptance criteria**
- A deploy during a run does not lose it.
- Runs execute at a bounded concurrency with a queue behind them.
- Nothing about the client's SSE contract changes.

## Technical plan

RG-032 was built to make this a swap, not a redesign: run state already lives in `runs` and
`run_events`, and the executor is a pure function of a run id.

### Files
```
apps/api/resume_api/queue/__init__.py       arq settings + worker entrypoint
apps/api/resume_api/services/run_service.py change: enqueue instead of add_task
services/worker/Dockerfile
```

### Steps
1. arq + Redis (Upstash is sufficient at this scale). One task: `execute_run(run_id)`.
2. Concurrency limit of 3 per worker; one worker to start.
3. Idempotency: `execute_run` claims the run with
   `update runs set status='running' where id=$1 and status='queued' returning *`. No row returned
   means another worker has it — return immediately. This is what makes retries safe.
4. Startup sweep re-enqueues runs stuck in `queued`, and fails runs stuck in `running` past 30
   minutes with a stale-run message.
5. Graceful shutdown: finish the current node, checkpoint, requeue the remainder.

### Tests
- A killed worker mid-run has the run picked up and completed by another.
- Double-enqueue executes once (the claim test).
- The SSE contract is unchanged — RG-032's tests pass without modification.

### Definition of done
Three tests green; RG-032's suite untouched and passing.

### Out of scope
Multi-region workers, priority queues.
