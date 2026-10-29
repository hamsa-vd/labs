# RG-030 — Port the LangGraph pipeline to the API

**Epic:** D — Pipeline · **Depends on:** RG-004, RG-020, RG-021, RG-022 · **Estimate:** L · **Labels:** pipeline, api

## Product requirement

**Problem.** The generation pipeline is the product. It works today in v1 and must not regress
while moving off Streamlit.

**Outcome.** The same graph, the same nodes, the same termination behaviour — running inside
FastAPI, per user, against database-backed inputs.

**Acceptance criteria**
- The node sequence is unchanged from v1 and observable in a run's event log.
- Every v1 pipeline test passes against the ported code with import-path changes only.
- Two users running simultaneously never see each other's state.

## Technical plan

This is a **port, not a rewrite**. Do not restructure the graph, rename nodes, or "simplify" the
routing. Read `plan/01-v1-reuse-map.md` before starting.

### Files
```
apps/api/resume_api/pipeline/state.py       ← v1 resume_agent/state.py
apps/api/resume_api/pipeline/graph.py       ← v1 resume_agent/graph.py
apps/api/resume_api/pipeline/budgets.py     ← v1 config.py MAX_* constants
apps/api/resume_api/pipeline/jd_loader.py   ← v1 jd_loader.py
apps/api/tests/pipeline/                    ← v1 tests/, ported
```

### The graph, unchanged
```
START → resolve_jd_input →(stop if no JD)→ load_inputs → create_targeting_brief
      → generate_resume → review_documents → ats_check_resume
      →(revise)→ revise_documents → review_documents   (loop)
      →(persist)→ generate_cover_letter → persist_outputs → compile_pdfs → END
```

### What changes, and only this
1. **Checkpointer.** `make_sqlite_checkpointer` → `AsyncPostgresSaver` against Supabase, with
   `thread_id = run_id`. v1's own comment already calls for this. Delete the SQLite path entirely.
2. **Input loading.** `load_inputs` no longer reads files. It takes a `RunInputs` dataclass
   assembled by the caller: rendered source of truth (RG-020), governance prompt, template
   `tex_source` (RG-021), and the six resolved prompt bodies (RG-022).
3. **Persistence.** `persist_outputs` writes to `runs` + `documents` + Storage (RG-006) instead of
   `companies/<slug>/<slug>/`. The `review` dict it builds maps field-for-field onto the `runs`
   columns — keep the same keys.
4. **Compilation.** `compile_pdfs` calls the LaTeX service (RG-035), not a local binary.
5. **Clients.** Injected per run with the user's BYOK credentials (RG-031), never constructed
   from environment defaults inside the graph.

### What must not change
`route_after_review` in full: the total-call cap, the revision-call cap, the max-revisions cap,
the empty-`failing_documents` exit, **and the <50% fix-resolution-rate bail-out**. The cover
letter still generates exactly once, after the loop. `failing_documents` still considers both
`resume_score` and `ats_total_score`. `ats_check_resume` still swallows its own errors into
`ats_error`. `build_persist_warnings` still runs. `strip_code_fence` still runs on every LLM
output. `_ensure_llm_budget` still guards every provider call.

Note a latent v1 bug to fix in passing: `build_persist_warnings` references
`COVER_LETTER_PASS_SCORE`, which is not imported in `graph.py`. Import it from `budgets.py`.

### Reuse from v1
`graph.py`, `state.py`, `jd_loader.py` — near-verbatim. `tests/test_graph_helpers.py`,
`test_graph_integration.py`, `test_jd_loader.py` — the regression net for this whole ticket.

### Tests
- All ported v1 tests pass.
- New: routing table test over `route_after_review` — one case per exit condition, including the
  fix-resolution bail-out.
- New: two concurrent runs for different users produce independent final states.
- New: a run resumed from its checkpoint after a simulated process restart completes correctly.

### Definition of done
Ported tests green, routing table complete, concurrency test green.

### Out of scope
HTTP routes (RG-032), ATS internals (RG-033), compilation (RG-035).
