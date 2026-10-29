# WP5 — The LangGraph pipeline port

Discharges RG-030.

This is the riskiest package in the plan. The graph is the product. If its routing behaviour
changes, resume quality regresses invisibly — there is no error, no failing build, just worse
output that nobody notices for a month. The v1 test suite is the only thing that catches it.

**This is a port, not a rewrite.** Do not restructure the graph, rename a node, reorder a routing
condition, adjust a threshold, or simplify a branch. Read
`/Users/liv-extech/Documents/Personal/Resume/resume_generator/resume_agent/graph.py` end to end
before writing anything, and keep it open beside you.

Root: `apps/resume-pipeline/`.

---

## Already built, import it — do not reimplement

| Module | From |
| --- | --- |
| `pipeline/scoring.py` | `attach_scores`, `RESUME_RUBRIC` (WP2) |
| `pipeline/budgets.py` | `RunBudget`, every `MAX_*`, `ATS_PASS_THRESHOLD`, `RESUME_PASS_SCORE`, `COVER_LETTER_PASS_SCORE`, `RECURSION_LIMIT` (WP2) |
| `pipeline/template_select.py` | `recommend_template` (WP2) |
| `pipeline/jd_loader.py` | `fetch_jd_from_url`, `load_jd_from_text` (WP2) |
| `pipeline/prompts.py` | `render_prompt`, `governance_prompt` (WP2) |
| `services/ats_service.py` | `check` (WP2) |
| `llm/base.py` | `LLMClient`, `Completion`, `parse_strict_json_object` (WP4) |
| `llm/factory.py` | `RunClients` (WP4) |
| `services/latex.py` | `compile_tex`, `CompileResult` (WP7) |

---

## 1. `resume_pipeline/pipeline/state.py`

Ported from v1 `state.py`. `ResumeGraphState` is a `TypedDict, total=False` and is the run
contract. Keep **every** key v1 declares, with the same names — the persisted `runs` row and the
result view both read them. Add only:

```python
application_id: str
user_id: str
prompt_versions: dict[str, int]     # stage → version actually used (RG-022)
```

`DocumentKey = Literal["resume", "cover_letter"]` stays.

## 2. `resume_pipeline/pipeline/inputs.py`

`load_inputs` no longer reads files. The caller assembles everything:

```python
@dataclass(frozen=True)
class RunInputs:
    source_of_truth: str                  # rendered by sot_render (WP2)
    governance_prompt: str
    template_key: str
    template_id: str | None
    base_resume_tex: str
    prompt_bodies: Mapping[str, str]      # stage → body, six stages
    prompt_versions: Mapping[str, int]
    budget: RunBudget
```

## 3. `resume_pipeline/pipeline/sinks.py`

`persist_outputs` and `compile_pdfs` must not import a database. They take protocols, so the whole
graph runs in tests with in-memory doubles and no Postgres:

```python
class RunSink(Protocol):
    async def persist(self, state: ResumeGraphState, review: dict[str, Any]) -> dict[str, str]: ...
    async def store_document(self, kind: str, content: bytes, content_type: str) -> str: ...

class Compiler(Protocol):
    async def compile(self, tex: str) -> CompileResult: ...
```

`persist` returns a mapping of document kind → document id, which the graph writes into state in
place of v1's filesystem paths.

## 4. `resume_pipeline/pipeline/graph.py`

Ported from v1. The graph, unchanged:

```
START → resolve_jd_input →(stop if no JD)→ load_inputs → create_targeting_brief
      → generate_resume → review_documents → ats_check_resume
      →(revise)→ revise_documents → review_documents        (loop)
      →(persist)→ generate_cover_letter → persist_outputs → compile_pdfs → END
```

```python
def build_graph(*, clients: RunClients, inputs: RunInputs, sink: RunSink,
                compiler: Compiler, checkpointer: Any | None = None) -> Any: ...

async def stream_graph(initial_state: ResumeGraphState, *, clients, inputs, sink, compiler,
                       checkpointer=None) -> AsyncIterator[tuple[str, ResumeGraphState]]: ...

async def invoke_graph(initial_state, *, clients, inputs, sink, compiler,
                       checkpointer=None) -> ResumeGraphState: ...
```

### What changes, and only this

1. **Async.** Nodes become `async def` because `LLMClient.complete` is async. `stream_graph` uses
   LangGraph's `astream` and yields `(node_name, node_state)` at exactly v1's granularity — one
   yield per completed node. That granularity is what RG-032's event log depends on.
2. **Clients injected.** Never constructed inside the graph, never from environment defaults.
   Each `complete` returns a `Completion`; nodes read `.text` and the caller records `.input_tokens`
   / `.output_tokens`.
3. **`load_inputs` reads `RunInputs`** instead of the filesystem. It still computes
   `company_slug`/`role_slug` via `slugify`, still calls `recommend_template`, and still honours an
   explicitly `selected_template` over the recommendation.
4. **`render_prompt` takes a body**, resolved from `inputs.prompt_bodies[stage]`, not a filename.
   Record the version used into `state["prompt_versions"]`.
5. **`persist_outputs` calls `sink.persist`** instead of writing `companies/<slug>/<slug>/`. It
   still builds the same `review` dict, key for key — those keys map onto the `resume_runs`
   columns and the result view reads them.
6. **`compile_pdfs` calls `compiler.compile`** instead of a local binary.
7. **Checkpointer.** `AsyncPostgresSaver` with `thread_id = run_id`. **Delete the SQLite path
   entirely** — v1's own comment asks for this. `checkpointer=None` means no checkpointing, which
   is what the unit tests use.
8. **`COVER_LETTER_PASS_SCORE` is imported from `budgets.py`.** v1's `build_persist_warnings`
   references it without importing it — a latent `NameError` on the cover-letter warning branch.
   Fixing it is explicitly in scope.
9. **`_ensure_llm_budget` reads `inputs.budget`**, not module constants. Exceeding a budget raises
   `BudgetExceeded`, which the graph turns into a persisted warning exactly as v1 does — a budget
   stop still produces usable output.

### What must not change — each of these is an acceptance test

- **`route_after_review` in full.** All five exits: the total-call cap, the revision-call cap, the
  `max_revisions` cap, an empty `failing_documents`, **and the below-50% fix-resolution-rate
  bail-out after a revision has already happened.** That last one is the near-zero-revision design
  goal and it is the easiest to drop by accident.
- **The cover letter is generated exactly once, after the loop.** Not per cycle. v1 documents this
  as a deliberate cost decision in `graph.py`.
- **`failing_documents` considers both `resume_score` and `ats_total_score`.** ATS gates revision
  too, not just the LLM review score.
- **`ats_check_resume` never raises.** It returns `ats_error` and the run continues.
- **A JD under `MIN_JD_TEXT_LENGTH` (300) stops the run at `resolve_jd_input`**, before any LLM
  call, via `route_after_jd_resolution`.
- **`strip_code_fence` runs on every LLM text output.**
- **`build_persist_warnings` runs, and its warnings are persisted**, not merely displayed.
- **`review_documents` reviews only the resume.** The cover letter is regenerated fresh from the
  final resume, never revised in place.
- **`revise_documents` runs a fresh ATS check** on the current resume and feeds `ats_top_actions`
  and unmet hard requirements into the reviser prompt.
- **`fix_resolution_matrix` accumulates across review passes**, it does not overwrite.

## Acceptance criteria

1. v1's `tests/test_graph_helpers.py` and `test_graph_integration.py` pass against the port with
   import-path and async changes only. Copies are at `tests/fixtures/v1/`.
2. A routing table test over `route_after_review` with one case per exit condition, including the
   fix-resolution bail-out, and one case that proceeds to revise.
3. A full run in fake mode emits the node sequence
   `resolve_jd_input, load_inputs, create_targeting_brief, generate_resume, review_documents,
   ats_check_resume, generate_cover_letter, persist_outputs, compile_pdfs` when the first review
   passes — with `revise_documents, review_documents, ats_check_resume` inserted once when
   `score_sequence=[6.5, 8.6]` forces a single cycle.
4. `generate_cover_letter` is called exactly once across a two-revision run — assert with a counter.
5. A JD of 200 characters ends the run at `resolve_jd_input` with `status="jd_input_required"` and
   zero LLM calls.
6. An ATS scorer that raises leaves `ats_error` set and the run still reaches `compile_pdfs`.
7. A compile failure leaves `compile_errors` populated and `status="complete_with_compile_errors"`,
   and the `.tex` documents are still persisted. A PDF failure never loses the `.tex`.
8. Two concurrent runs for different users produce independent final states — run them with
   `asyncio.gather` over two graphs and assert no field crosses over.
9. A run resumed from its checkpoint after a simulated interruption completes correctly.
10. `build_persist_warnings` produces the cover-letter warning without raising `NameError` — the
    v1 latent bug, now fixed.
11. Budget exhaustion produces a persisted warning and usable output, not an exception to the caller.
12. The whole fake-mode suite runs offline in under five seconds.

## Test paths (test agent writes only here)

```
tests/pipeline/test_graph_helpers.py
tests/pipeline/test_graph_routing.py
tests/pipeline/test_graph_integration.py
tests/pipeline/test_graph_concurrency.py
tests/pipeline/test_inputs.py
tests/pipeline/doubles.py            (in-memory RunSink / Compiler doubles)
```

Use `FakeLLMClient` from `resume_pipeline.llm.fake` for every LLM interaction. No test may open a
socket; the guard in `tests/conftest.py` enforces it. Checkpointer tests read `RESUME_DATABASE_URL`
and skip cleanly when it is absent.

## Source paths (implementing agent writes only here)

```
resume_pipeline/pipeline/state.py
resume_pipeline/pipeline/inputs.py
resume_pipeline/pipeline/sinks.py
resume_pipeline/pipeline/graph.py
```
