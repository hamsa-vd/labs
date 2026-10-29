# RG-041 — New application: input and launch

**Epic:** E — Screens · **Depends on:** RG-021, RG-032 · **Estimate:** M · **Labels:** web, product

## Product requirement

**Problem.** v1's generate tab asks for company, title, and a JD, then runs. It gives no
confidence about what is about to happen or what it will cost.

**User story.** I paste a job description, confirm the template the system suggests, and start —
knowing which models will run and roughly what it will cost before I commit.

**Acceptance criteria**
- I can supply the JD by paste or URL, and see it was fetched successfully before starting.
- A template is recommended with a stated reason, and I can override it.
- I see which three models will run and an estimated cost before pressing start.
- A JD under 300 characters blocks the start with a clear reason.
- Pressing start navigates straight to the live run view.

## Technical plan

### Files
```
apps/web/src/app/(app)/applications/new/page.tsx
apps/web/src/components/generate/JdInput.tsx           tabs: paste | URL
apps/web/src/components/generate/TemplatePicker.tsx    recommendation + override
apps/web/src/components/generate/RunPreflight.tsx      models, budget, estimated cost
```

### Steps
1. Three fields — company, job title, JD — then a preflight card. No wizard, no multi-step form;
   it is four inputs and a button.
2. JD by URL calls `POST /v1/jd/fetch` (thin wrapper on v1's `jd_loader.fetch_jd_from_url`),
   showing the fetched character count and the first lines so the user can confirm it worked.
   v1's `MIN_JD_TEXT_LENGTH` guard is surfaced inline, not as a post-submit error.
3. On JD blur, call `POST /v1/templates/recommend` and show the recommendation with its reason
   as helper text. Overriding it is a Select; the reason stays visible.
4. `RunPreflight` lists the three model roles from the profile, the revision ceiling, and an
   estimated cost from `llm/pricing.py`. Estimated, and labelled as such — never presented as exact.
5. Start posts to `POST /v1/applications` then `POST /v1/applications/{id}/runs` and routes to
   `/applications/{id}/runs/{runId}`.
6. Autosave the draft to `localStorage` per user, so a long JD paste survives an accidental reload.

### Reuse from v1
`app.py render_generation_tab` for the field set; `jd_loader.py` for URL fetch and the length
guard; `resume_selection.py` for the recommendation and its reason string.

### Tests
- A 200-char JD disables start and explains why.
- URL fetch failure shows the loader's error message inline, and start stays disabled.
- The recommendation appears after entering a JD and can be overridden.
- Start creates an application and lands on the run route.

### Definition of done
Four tests green.

### Out of scope
The live run view (RG-042).
