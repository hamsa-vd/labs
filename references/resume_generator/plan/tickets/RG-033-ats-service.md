# RG-033 — ATS checker as a service module

**Epic:** D — Pipeline · **Depends on:** RG-030 · **Estimate:** M · **Labels:** pipeline, api

## Product requirement

**Problem.** The ATS scorer is a separate local package (`ats-checker/`) that v1 imports
opportunistically and tolerates the absence of. It is one of the product's two headline numbers,
so it needs to be a first-class, always-present dependency — and reachable on its own, so an
imported resume can be scored without generating anything.

**User story.** As a user I see an ATS score with its keyword, structural, and semantic
components, what matched, what is missing, and the highest-value actions — for a generated resume
or one I imported.

**Acceptance criteria**
- The same resume and JD always produce the same score. No LLM in this path.
- Missing keywords are split into required and preferred.
- Unmet hard requirements are listed explicitly.
- A score can be requested for any resume text, outside a generation run.

## Technical plan

### Files
```
apps/api/resume_api/ats/                  vendored from ats-checker/ats_checker/
  __init__.py action_verbs.py config.py hard_requirements.py jd_cleaner.py
  keyword_extractor.py resume_parser.py scorer.py section_parser.py synonyms.py
apps/api/resume_api/services/ats_service.py
apps/api/resume_api/routers/ats.py
apps/api/tests/ats/                       ← ats-checker/tests/
```

### Routes
```
POST /v1/ats/check    { resume_text | document_id, jd_text } → AtsResult
```

### Contract — keep v1's key names exactly
```
ats_total_score, ats_grade, ats_keyword_score, ats_structural_score, ats_semantic_score,
ats_matched[], ats_missing_required[], ats_missing_preferred[], ats_top_actions[],
ats_hard_requirements[{description, met}], ats_all_hard_met, ats_error
```
These are the keys `graph.persist_outputs` writes and the result view reads. Renaming them
breaks the port for no gain.

### Steps
1. Vendor the package into `apps/api/resume_api/ats/` as a real dependency (it is the maintainer's
   own code; a git submodule would add friction for no benefit). Record the source commit in a
   header comment. Bring its tests.
2. `ats_service.check(resume_tex, jd_text)` wraps it, strips LaTeX to plain text before scoring
   (the scorer expects prose, not markup), and returns the dict above. It **never raises** — any
   failure returns `{"ats_error": "..."}`, preserving v1's behaviour where a bad ATS check does
   not kill a run.
3. `ATS_PASS_THRESHOLD = 80` ("Excellent") stays the pass bar, now per-user overridable (RG-031).
4. The standalone route is what makes the import flow (RG-044) work.

### Reuse from v1
The entire `ats-checker` package, verbatim. `resume_agent/ats_client.py` shows the wrapping
contract. `graph.ats_check_resume` shows the error-tolerance requirement.

### Tests
- Ported `ats-checker` tests pass unchanged.
- Determinism: the same input scored twice is byte-identical.
- A malformed JD returns `ats_error` and does not raise.
- LaTeX stripping: a `.tex` resume and its plain-text equivalent score within 2 points.

### Definition of done
Ported tests green plus the four above.

### Out of scope
The ATS UI and evidence gate (RG-036, RG-043).
