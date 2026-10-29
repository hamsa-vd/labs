# RG-036 — Evidence-gated ATS keyword fixes

**Epic:** D — Pipeline · **Depends on:** RG-020, RG-033 · **Estimate:** L · **Labels:** pipeline, api, product

## Product requirement

**Problem.** The fastest way to raise an ATS score is to paste in missing keywords. That is also
how a resume becomes a lie and a candidate gets caught in an interview. The product's position is
that a keyword may only be added if the user can point at where they actually did it.

**User story.** The ATS panel says I am missing "Kubernetes". To add it, I must attach a company
or project from my source of truth and a specific experience bullet that evidences it. Once I do,
the keyword is added to the resume **and** saved back to my source of truth, so every future
resume knows it.

**Acceptance criteria**
- A missing keyword cannot be accepted without both an owning company/project and a bullet.
- Accepting writes the evidence into the source of truth, not just into this one resume.
- I can write a new bullet inline while accepting, and it is saved to the source of truth too.
- I can dismiss a keyword as not applicable, and it stays dismissed for this application.
- The resume is regenerated or patched with the keyword only after the evidence exists.

## Technical plan

This is the product's most opinionated feature. It has no v1 equivalent — build it carefully.

### Files
```
apps/api/resume_api/schemas/evidence.py
apps/api/resume_api/services/evidence_service.py
apps/api/resume_api/routers/evidence.py
supabase/migrations/0015_keyword_decisions.sql
```

### Schema
`keyword_decisions` — user_id, application_id, run_id, keyword citext,
decision `('accepted','dismissed','deferred')`, sot_company_id null, sot_project_id null,
sot_bullet_id null, created_bullet bool, note, created_at.
Unique `(application_id, lower(keyword))`.

### Routes
```
GET  /v1/runs/{id}/keywords                  missing + matched + prior decisions, merged
POST /v1/runs/{id}/keywords/{kw}/accept      { company_id | project_id, bullet_id | new_bullet }
POST /v1/runs/{id}/keywords/{kw}/dismiss     { note? }
POST /v1/runs/{id}/keywords/apply            regenerate the resume with the accepted set
```

### The gate — server-enforced, not a UI convention
`accept` rejects with `evidence_required` unless:
1. exactly one of `company_id` / `project_id` is present and owned by the caller; **and**
2. either `bullet_id` (owned, and belonging to that company or project) or `new_bullet` with at
   least 40 characters of text is present.

On success, in one transaction:
- if `new_bullet`: insert an `sot_bullets` row under that company/project;
- upsert an `sot_skills` row for the keyword, appending the bullet id to `evidence_bullet_ids`;
- insert the `keyword_decisions` row.

The source-of-truth write is the point of the feature. A keyword accepted here is permanently
part of the user's record and will be available to every future application. This is what makes
the gate a compounding asset rather than a nag.

### `apply`
Runs the revision node once with the accepted keywords and their evidence bullets appended to the
prompt context, then re-runs the ATS check, and writes a new `runs` row linked to the same
application. It never edits the previous run — score history stays intact.

### Tests
- Accept with no bullet → `evidence_required`; nothing is written (assert the transaction rolled back).
- Accept with a bullet belonging to a different company → rejected.
- Accept with `new_bullet` → the bullet exists in the source of truth afterwards and the skill row
  references it.
- Dismiss persists across a page reload and across a re-run of the ATS check.
- `apply` produces a new run whose ATS score is ≥ the previous one for a seeded fixture.

### Definition of done
All five tests green; the gate is impossible to bypass through the API.

### Out of scope
The panel UI (RG-043).
