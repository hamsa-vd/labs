# RG-020 — Source of truth: structured model and API

**Epic:** C — User data · **Depends on:** RG-002, RG-004 · **Estimate:** L · **Labels:** data, api

## Product requirement

**Problem.** v1 reads a single flat file, `base/source_of_truth.txt`, and injects it wholesale
into every prompt. It works for one person, but nothing can *reference* a fact inside it — which
is exactly what the ATS evidence gate (RG-036) needs, and it cannot be edited safely by a user.

**User story.** As a user I keep one structured record of my career — companies, projects,
bullets, skills — and every generated resume is built only from facts in it.

**Acceptance criteria**
- I can add, edit, reorder, and delete companies, projects, bullets, and skills.
- A skill can be linked to the specific bullets that prove it.
- The whole record renders back to the plain-text block the prompts expect, byte-stably.
- Nothing is ever deleted silently: deleting a company warns about the bullets it owns.

## Technical plan

### Files
```
apps/api/resume_api/schemas/sot.py
apps/api/resume_api/repositories/sot.py
apps/api/resume_api/routers/sot.py
apps/api/resume_api/pipeline/sot_render.py     structured rows → prompt text block
apps/api/tests/test_sot_render.py
```

### Routes
```
GET    /v1/source-of-truth                 full tree (companies → projects → bullets) + skills
POST   /v1/source-of-truth/companies       PATCH/DELETE /{id}
POST   /v1/source-of-truth/projects        PATCH/DELETE /{id}
POST   /v1/source-of-truth/bullets         PATCH/DELETE /{id}
POST   /v1/source-of-truth/skills          PATCH/DELETE /{id}
POST   /v1/source-of-truth/reorder         { entity, ids[] }  → bulk sort_order write
GET    /v1/source-of-truth/rendered        the exact text the pipeline injects
POST   /v1/source-of-truth/import          paste a v1-style text block → parsed draft (no write)
```

### `sot_render.py` — the important part
The pipeline prompts (`generator.md`, `targeting_brief.md`, `reviewer.md`, `reviser.md`,
`cover_letter.md`) all take a `SOURCE_OF_TRUTH` string. This function is the single producer of
that string. Deterministic ordering (company sort_order, then project sort_order, then bullet
sort_order) so identical data always yields an identical prompt — otherwise prompt caching and
run comparison both break.

Format: keep v1's shape so the existing prompts need no edits — company header line, role and
dates, then indented bullets, then a skills block grouped by category.

### Reuse from v1
- `base/source_of_truth.txt` is the reference content and the format spec. Read it, match the
  rendered output to it, and use it as the golden fixture for the render test.
- The v1 prompts consume this string unchanged. Do not change the format to "improve" it.

### Tests
- Golden test: the seeded structured record renders **byte-identical** to a fixture derived from
  `base/source_of_truth.txt`. This is the ticket's core test.
- Ordering is stable across two calls with rows inserted out of order.
- `/import` parses the v1 text block into the correct company/project/bullet counts.
- Deleting a company cascades to its projects and bullets, and returns the count it removed.

### Definition of done
Golden render test green; all CRUD routes covered; RLS verified for a second user.

### Out of scope
The editor UI (RG-045).
