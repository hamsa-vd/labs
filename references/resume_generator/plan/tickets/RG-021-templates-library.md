# RG-021 — LaTeX template library

**Epic:** C — User data · **Depends on:** RG-002, RG-006 · **Estimate:** M · **Labels:** data, api

## Product requirement

**Problem.** v1 hard-codes five template paths in `config.py` and picks between them with a
keyword heuristic. Users cannot add their own, and the ten `.tex` files that exist are invisible
to the product.

**User story.** As a user I keep a library of resume templates — the seeded defaults plus my own,
added by upload, paste, or by copying an existing one — and I choose or accept a recommendation
for each application.

**Acceptance criteria**
- Ten system templates are available on first sign-in without me doing anything.
- I can add a template three ways: upload a `.tex` file, paste LaTeX, or duplicate an existing one.
- I can rename and delete my own templates but never the system ones.
- The system still recommends a template from the job description, and tells me why.

## Technical plan

### Files
```
apps/api/resume_api/schemas/templates.py
apps/api/resume_api/repositories/templates.py
apps/api/resume_api/routers/templates.py
apps/api/resume_api/pipeline/template_select.py     ported from v1
apps/api/resume_api/latex/validate.py               structural sanity + safety scan
supabase/seed/templates/*.tex                       the ten v1 templates
supabase/migrations/0013_seed_templates.sql
```

### Routes
```
GET    /v1/templates                      system + mine
POST   /v1/templates                      { name, kind, tex_source } | multipart upload
POST   /v1/templates/{id}/duplicate       { name }
PATCH  /v1/templates/{id}                 own rows only
DELETE /v1/templates/{id}                 own rows only; 409 if referenced by a run
POST   /v1/templates/recommend            { jd_text, job_title } → { key, reason, alternatives[] }
```

### Steps
1. Seed: import `single_page/*.tex` (5) and `multi_page/*.tex` (5) as `is_system = true`,
   `user_id = null`, with keys `frontend, backend-java, backend-python, fullstack, senior-engineer`
   under each `kind`. Store the source in the `tex_source` column — these are small text files;
   Storage is for generated output, not for the library.
2. `validate.py` runs on every write: must contain `\documentclass` and `\begin{document}`;
   reject `\write18`, `\input{/`, `\openout`, `\immediate\write`; cap at 200 KB. Return a
   `validation_failed` error listing every problem found, not just the first.
3. `template_select.py` is v1's `resume_selection.recommend_template` moved across. Change only
   what is necessary: it returns a template **key**, which the caller resolves to the user's row
   for that key (preferring their own override of a system key).
4. Deletion is blocked while any `runs` row references the template — return `409 conflict` with
   the count, per the arey voice ("Used by 3 applications. Duplicate it instead.").

### Reuse from v1
- `resume_agent/resume_selection.py` — lift, keep its tests.
- `config.py TEMPLATE_FILES` — the key naming contract.
- `single_page/*.tex`, `multi_page/*.tex` — the seed content.

### Tests
- Port `tests/test_resume_selection.py` unchanged apart from imports. It must still pass.
- Validation rejects each unsafe macro; the error lists all of them.
- Duplicating a system template creates a user-owned copy with `derived_from` set.
- Deleting a referenced template returns 409.

### Definition of done
Ten templates seeded; the ported selection test green; validation covered.

### Out of scope
The templates UI (RG-046), compilation (RG-035).
