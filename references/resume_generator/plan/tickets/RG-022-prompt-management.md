# RG-022 — User-editable prompts for the six run stages

**Epic:** C — User data · **Depends on:** RG-002, RG-004 · **Estimate:** M · **Labels:** data, api

## Product requirement

**Problem.** v1's prompts are five markdown files on disk. They are the product's real
intelligence, and a user who wants a different reviewing standard cannot change them.

**User story.** As a user I read and edit the prompt used at each of the six stages — targeting,
generation, review, revision, ATS, cover letter — and I can always get back to the default.

**Acceptance criteria**
- All six prompts are visible, editable, and versioned.
- Saving creates a new version; I can view history and restore any earlier version.
- "Reset to default" restores the system prompt without losing my history.
- A prompt that drops a required variable cannot be saved.
- A run records which prompt version it used.

## Technical plan

### Files
```
apps/api/resume_api/schemas/prompts.py
apps/api/resume_api/repositories/prompts.py
apps/api/resume_api/routers/prompts.py
apps/api/resume_api/pipeline/prompts.py        render_prompt, ported from v1
supabase/seed/prompts/{targeting,generation,review,revision,ats,cover_letter}.md
supabase/migrations/0014_seed_prompts.sql
```

### Required variables per stage (validation contract)
Taken from the actual `render_prompt` call sites in v1 `graph.py`:

| Stage | Required `{{VARS}}` |
| --- | --- |
| targeting | COMPANY_NAME, JOB_TITLE, JD_TEXT, SOURCE_OF_TRUTH |
| generation | TARGETING_BRIEF, JD_TEXT, BASE_RESUME_TEX, SOURCE_OF_TRUTH |
| review | COMPANY_NAME, JOB_TITLE, REVISION_COUNT, TARGETING_BRIEF, JD_TEXT, SOURCE_OF_TRUTH, PREVIOUS_MUST_FIX, RESUME_TEX |
| revision | COMPANY_NAME, JOB_TITLE, TARGETING_BRIEF, JD_TEXT, SOURCE_OF_TRUTH, RESUME_TEX, RESUME_MUST_FIX, FIX_RESOLUTION_MATRIX, RESUME_SCORE, RESUME_TARGET_SCORE, RESUME_CATEGORY_SCORES, ATS_TOP_ACTIONS, ATS_UNMET_HARD_REQUIREMENTS |
| cover_letter | COMPANY_NAME, JOB_TITLE, TARGETING_BRIEF, JD_TEXT, RESUME_TEX, SOURCE_OF_TRUTH, FIX_RESOLUTION_SUMMARY |
| ats | (new in v2 — the ATS stage is deterministic in v1; this prompt only shapes the LLM's *explanation* of ATS findings, vars: JD_TEXT, ATS_FINDINGS) |

### Routes
```
GET    /v1/prompts                        active prompt per stage, with is_customised
GET    /v1/prompts/{stage}/versions
POST   /v1/prompts/{stage}                { body } → new version, becomes active
POST   /v1/prompts/{stage}/restore        { version }
POST   /v1/prompts/{stage}/reset          back to the system default
POST   /v1/prompts/{stage}/validate       dry-run the variable check
```

### Steps
1. Seed the five v1 prompt files verbatim as `user_id = null, version = 1` rows. Do not reword them.
2. `render_prompt` keeps v1's `{{VAR}}` substitution semantics exactly. It now takes a body string
   rather than a filename, and raises `ValidationFailed` on an unfilled variable at render time.
3. Validation on save: extract `{{...}}` tokens from the body, diff against the required set for
   that stage. Missing required → reject, naming each. Unknown extra token → reject (it would
   render empty and silently degrade the prompt).
4. Resolution order at run time: the user's active version for the stage, else the system row.
   The chosen `prompt_id`+`version` per stage is written into `runs.token_usage.prompts`.

### Reuse from v1
`resume_agent/prompts/*.md` (all five, verbatim), `prompt_loader.render_prompt` and
`distill_governance_prompt` (the governance/system prompt derived from
`base/resume-proj-instructions.txt` — keep it; it is what stops fabrication).

### Tests
- Every seeded prompt passes its own variable validation.
- Saving a prompt missing `{{JD_TEXT}}` is rejected and names it.
- Restore brings back an exact earlier body.
- Reset leaves version history intact.

### Definition of done
Six stages seeded and validating; a run records its prompt versions.

### Out of scope
The prompt editor UI (RG-045).
