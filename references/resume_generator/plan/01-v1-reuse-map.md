# v1 → v2 reuse map

v1 is working software. The default is **port, not rewrite**. Anything marked *Lift* moves
across with only import-path and I/O changes; the logic is not to be "improved" in flight.

| v1 file | Verdict | Where it lands | Notes |
| --- | --- | --- | --- |
| `resume_agent/graph.py` | **Lift** | `apps/api/pipeline/graph.py` | Node functions unchanged. Only the checkpointer, storage calls, and prompt loading get swapped. RG-030 |
| `resume_agent/state.py` | **Lift** | `apps/api/pipeline/state.py` | `ResumeGraphState` TypedDict is the run contract. RG-030 |
| `resume_agent/scoring.py` | **Lift verbatim** | `apps/api/pipeline/scoring.py` | `RESUME_RUBRIC`, `COVER_LETTER_RUBRIC`, `weighted_score`, `attach_scores` — no changes. RG-034 |
| `ats-checker/ats_checker/*` | **Lift as package** | `apps/api/ats_checker/` (vendored) | Deterministic, no I/O, already a clean package. RG-033 |
| `resume_agent/resume_selection.py` | **Lift** | `apps/api/pipeline/template_select.py` | Keyword→template heuristic. Template keys become DB ids. RG-021 |
| `resume_agent/jd_loader.py` | **Lift** | `apps/api/pipeline/jd_loader.py` | URL fetch + `MIN_JD_TEXT_LENGTH` guard stays. RG-032 |
| `resume_agent/prompts/*.md` | **Lift as seed data** | `supabase/seed/prompts/` | The five prompt files become the system default rows. RG-022 |
| `resume_agent/prompt_loader.py` | **Port** | `apps/api/pipeline/prompts.py` | `render_prompt` keeps `{{VAR}}` substitution but reads from DB, not disk. RG-022 |
| `resume_agent/llm/factory.py`, `catalog.py`, `claude_client.py`, `openai_client.py` | **Port** | `apps/api/llm/` | Keep the provider abstraction and `parse_strict_json_object`. Keys now come per-request from the user's BYOK record, not env. RG-031 |
| `resume_agent/config.py` budgets (`MAX_*`, `ATS_PASS_THRESHOLD`, `RESUME_PASS_SCORE`) | **Lift as values** | `apps/api/pipeline/budgets.py` | Same numbers, now overridable per user in settings. RG-031 |
| `resume_agent/latex_compile.py` | **Rewrite** | `services/latex/` | v1 shells out to a local `pdflatex`. v2 needs a sandboxed container. RG-035 |
| `resume_agent/storage.py` | **Rewrite** | `apps/api/repositories/` | Filesystem paths → Postgres rows + Storage objects. `slugify` is the one function worth keeping. RG-002 |
| `resume_agent/cli_proxy/*` | **Drop** | — | The Claude/Codex CLI proxy was a no-API-key workaround. v2 is BYOK. |
| `resume_agent/ui/styles.py`, `app.py` | **Drop** | — | Replaced by the Next.js app. Read them for behaviour, not for code. |
| `tests/*` | **Lift** | `apps/api/tests/` | `test_scoring`, `test_resume_selection`, `test_jd_loader`, `test_graph_helpers` port with import changes only and are the regression net for the whole port. RG-030 |
| `single_page/*.tex`, `multi_page/*.tex` | **Lift as seed data** | `supabase/seed/templates/` | Ten templates become the seeded template library. RG-021 |
| `base/source_of_truth.txt` | **Model, then lift content** | `source_of_truth` tables | Flat text becomes structured rows (companies, projects, bullets, skills) so the evidence gate can reference them. RG-020 |

## The v1 behaviour that must not be lost

These are easy to drop by accident in a re-platform. Each has an acceptance criterion in its ticket.

1. **The revision loop terminates.** `route_after_review` bails when the fix-resolution rate is
   below 50% after a revision, when any `MAX_*` budget is hit, or when `max_revisions` is reached.
2. **The cover letter is generated once, after the last revision** — not per cycle. This is a
   deliberate cost decision documented in `graph.py`.
3. **ATS score gates revision too**, not just the LLM review score (`failing_documents`).
4. **Warnings are persisted, not just shown** (`build_persist_warnings`) — the result view reads them.
5. **A run never dies on a bad ATS check** — `ats_check_resume` stores `ats_error` and continues.
6. **JD shorter than `MIN_JD_TEXT_LENGTH` (300) is rejected before any LLM call.**
