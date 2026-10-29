# RG-040 — Pipeline screen (application tracker)

**Epic:** E — Screens · **Depends on:** RG-013, RG-032, RG-037 · **Estimate:** L · **Labels:** web, product

## Product requirement

**Problem.** v1's "Applied Jobs" tab lists folders on disk with a status dropdown. It cannot
answer the question a job search actually asks: what needs my attention today.

**User story.** I open the app and immediately see every application, where each one stands, and
what I owe it next.

**Acceptance criteria**
- Every application shows company, role, both scores, status, and last activity.
- I can filter by status and search by company or role.
- Generated and imported applications are visually distinguishable at a glance.
- I can advance status and record an interview round without leaving the list.
- With no applications, the empty state offers exactly two actions: generate, or import.

## Technical plan

### Files
```
apps/web/src/app/(app)/pipeline/page.tsx           server component, initial fetch
apps/web/src/components/pipeline/ApplicationTable.tsx
apps/web/src/components/pipeline/StatusCell.tsx    inline status change
apps/web/src/components/pipeline/ScorePair.tsx     ATS + review, mono numerals
apps/web/src/components/pipeline/PipelineFilters.tsx
apps/web/src/components/pipeline/RoundTracker.tsx  popover: round count, current round, next action
apps/api/resume_api/routers/applications.py        list, patch status
```

### Presentation
Columns: **Company / role** (two-line cell, role in `--text-secondary`) · **Source** (a Badge:
"Generated" / "Imported") · **ATS** · **Review** · **Status** · **Next action** · **Updated**.

Per the arey guide: all numbers and timestamps in `--font-mono`. Relative time in the cell
("3 d ago"), absolute in the tooltip. Status is a colour dot plus a label — never a coloured row
background, never a left-border stripe. Scores show as `82` and `8.4` with the threshold implied
by the dot colour, not by a progress bar in every row.

Below 940px the table becomes a stacked card list; the same data, no horizontal scroll.

### Steps
1. Server-render the first page; TanStack Query takes over for filtering and mutation.
2. Filters are URL state (`?status=&q=`), so a filtered view is linkable and survives a refresh.
3. Status change is an optimistic `PATCH /v1/applications/{id}`, reverting with a toast on failure.
4. `RoundTracker` edits `round_count`, `current_round`, and `next_action` in a popover — v1's
   `application_status.json` fields, now first-class.
5. Cursor pagination at 50 rows with an infinite-scroll sentinel.
6. Empty state: one line ("No applications yet.") and two buttons. No illustration.

### Reuse from v1
`app.py render_application_browser` / `_application_row` for the field set and the status
vocabulary; `storage.default_application_status()` for the exact fields to expose.

### Tests
- Playwright: filter by status narrows the list and updates the URL.
- Optimistic status change reverts and toasts when the API 500s.
- The imported marker renders for an imported application.
- Empty state renders both actions for a new user.

### Definition of done
Four tests green at 360px and 1440px.

### Out of scope
Bulk actions, CSV export.
