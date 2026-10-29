# RG-042 — Live run view

**Epic:** E — Screens · **Depends on:** RG-032 · **Estimate:** M · **Labels:** web, product

## Product requirement

**Problem.** A generation takes minutes and makes up to sixteen paid LLM calls. Silence during
that time reads as a hang, and v1 loses the run if the tab closes.

**User story.** I watch each stage complete with a plain-language label, I can leave and come
back, and when it finishes I land on the result.

**Acceptance criteria**
- Each stage appears as it completes, with elapsed time.
- Revision cycles are shown as cycles, not as a confusing repeat of the same stage.
- Refreshing mid-run resumes the view with no lost or duplicated stages.
- On failure I see which stage failed and one sentence about why, with a retry.
- I can cancel.

## Technical plan

### Files
```
apps/web/src/app/(app)/applications/[id]/runs/[runId]/page.tsx
apps/web/src/components/run/RunTimeline.tsx
apps/web/src/components/run/RunStage.tsx
apps/web/src/hooks/useRunStream.ts        (from RG-032)
```

### Stage labels — server-supplied (RG-032), listed here for design reference
`resolve_jd_input` "Read the job description" · `load_inputs` "Loaded your source of truth" ·
`create_targeting_brief` "Built the targeting brief" · `generate_resume` "Wrote the resume" ·
`review_documents` "Reviewed against the rubric" · `ats_check_resume` "Scored for ATS" ·
`revise_documents` "Revised the resume" · `generate_cover_letter` "Wrote the cover letter" ·
`persist_outputs` "Saved" · `compile_pdfs` "Compiled the PDF"

### Presentation
A vertical timeline. Completed stages show a filled Phosphor check and a mono elapsed time
(`4.2 s`). The active stage shows a Spinner in place of the glyph. Pending stages are
`--text-tertiary`. Repeat passes group under a "Revision 1" subheading rather than appending a
duplicate row — this is where v1's stream is confusing.

Review and ATS stages surface their score in the row as it lands, so the user sees the number
climb across revisions. That is the most reassuring thing the screen can do.

Motion is opacity + 4px rise at 220ms per stage. Nothing bounces. Reduced motion zeroes it.

### Steps
1. Subscribe via `useRunStream(runId, afterSeq)`; seed `afterSeq` from the server-rendered events
   already in the page so a refresh never replays what is already shown.
2. On `succeeded`, redirect to the result view after a 600ms beat so the last stage is visible.
3. On `failed`, render the failing stage in the error state with `errors.ts` copy and a "Start
   again" button that reuses the same inputs.
4. Cancel is a quiet Button with a confirm Dialog stating that work already spent is not refunded.

### Reuse from v1
`app.py run_generation`'s node-to-label mapping and its ordering.

### Tests
- Mocked SSE: stages render in order with elapsed times.
- Mid-run refresh shows all prior stages exactly once.
- A failure event renders the error state and the retry.
- Two revision cycles group under separate subheadings.

### Definition of done
Four tests green.

### Out of scope
The result view (RG-043).
