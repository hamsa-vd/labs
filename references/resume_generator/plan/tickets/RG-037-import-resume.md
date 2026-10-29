# RG-037 — Import an existing resume for scoring

**Epic:** D — Pipeline · **Depends on:** RG-033, RG-006 · **Estimate:** M · **Labels:** pipeline, api

## Product requirement

**Problem.** Users already have resumes they have sent out. v1 can only score what it generates,
so all that history is invisible to the tracker and gets no feedback.

**User story.** I upload or paste a resume I already sent, attach the job description, and get
the same ATS and review scores as a generated one — and it appears in my pipeline alongside
everything else.

**Acceptance criteria**
- I can import by `.tex`, `.pdf`, or pasted text.
- An imported application is scored on both dimensions and marked clearly as imported.
- Imported applications appear in the pipeline and can be tracked through interview rounds.
- I can convert an imported application into a generated one, reusing its job description.

## Technical plan

### Files
```
apps/api/resume_api/services/import_service.py
apps/api/resume_api/routers/imports.py
apps/api/resume_api/parsers/pdf_text.py       pypdf extraction
apps/api/resume_api/parsers/tex_text.py       LaTeX → plain text (shared with RG-033)
```

### Routes
```
POST /v1/applications/import      multipart: file? + { company_name, job_title, jd_text, resume_text? }
                                  → { application_id, run_id }
POST /v1/applications/{id}/convert-to-generated  → { application_id }
```

### Steps
1. Create the `applications` row with `source = 'imported'`, store the original file as a
   `documents` row of kind `imported_resume`.
2. Extract text: `.tex` → `tex_text`; `.pdf` → `pypdf`, and if the extraction yields under 200
   characters, reject with `unreadable_pdf` ("This looks like a scanned PDF. Paste the text
   instead.") rather than scoring garbage. No OCR in v2.0.
3. Create a `runs` row with `status='succeeded'` that skips generation entirely and runs only two
   stages: `ats_check` (RG-033) and `review_documents` (the reviewer prompt against the imported
   text, so the scores are comparable to a generated run).
4. Emit `run_events` for both stages so the same UI (RG-042) renders the import progress.
5. `convert-to-generated` creates a **new** application seeded with the same company, title, and
   JD, linked back via `derived_from`. The import is never mutated.

### Reuse from v1
The reviewer prompt and `scoring.attach_scores` are used unchanged, which is what makes an
imported score directly comparable to a generated one.

### Tests
- `.tex`, `.pdf`, and pasted-text imports each produce a run with both scores.
- A scanned (image-only) PDF returns `unreadable_pdf` and creates no application.
- An imported application appears in the pipeline list with the imported marker.
- Convert creates a new application and leaves the original untouched.

### Definition of done
All four tests green.

### Out of scope
The import UI (RG-044).
