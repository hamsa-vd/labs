# RG-043 — Result view: scores, ATS panel, and LaTeX editor

**Epic:** E — Screens · **Depends on:** RG-034, RG-035, RG-036 · **Estimate:** XL · **Labels:** web, product

## Product requirement

**Problem.** This is the screen the whole product exists to show. v1 splits it across tabs and
buries the scores below the LaTeX.

**User story.** I see how the resume scored on both dimensions, exactly what is missing, what I
can honestly do about it, and I can edit the LaTeX and recompile without leaving the page.

**Acceptance criteria**
- Both scores are the first thing on the page, with their category and component breakdowns one
  interaction away.
- Missing ATS keywords are actionable through the evidence gate — never a one-click "add".
- The LaTeX is visible, editable, and recompilable, with the PDF beside it.
- Warnings from the run are shown, not hidden.
- I can download the `.tex` and the `.pdf` for both the resume and the cover letter.

## Technical plan

**Size warning.** This ticket is XL. If it must be split, cut along the three panels below —
each is independently shippable behind the same route.

### Files
```
apps/web/src/app/(app)/applications/[id]/page.tsx
apps/web/src/components/result/ScoreHero.tsx          the two headline numbers
apps/web/src/components/result/ReviewPanel.tsx        8 rubric categories, weights, must-fix list
apps/web/src/components/result/AtsPanel.tsx           components, matched, missing, hard reqs
apps/web/src/components/result/KeywordGate.tsx        the evidence dialog (RG-036)
apps/web/src/components/result/TexEditor.tsx          CodeMirror 6, LaTeX mode
apps/web/src/components/result/PdfPreview.tsx         pdf.js, page nav
apps/web/src/components/result/WarningsList.tsx
apps/web/src/components/result/DownloadMenu.tsx
```

### Layout
`ScoreHero` full width at the top: two large mono numerals — ATS `82 / 100` with its grade, and
review `8.4 / 10` — each with a one-line verdict and a threshold marker. No dials, no gauges, no
gradients; the number *is* the graphic. Below, a three-tab `Tabs`: **Review**, **ATS**,
**Documents**. Above 1200px, Documents renders as a two-pane split (editor left, PDF right);
below that it is a `SegmentedControl` between the two.

### `AtsPanel` and the gate
Missing keywords list as Tags in two groups, required and preferred. Clicking one opens
`KeywordGate`, a Dialog that requires:
1. a company or project, picked from the user's source of truth (searchable Select);
2. a bullet — either an existing one under that company/project, or a new one typed inline
   (minimum 40 characters, with the helper text "Describe what you actually did with it").

The primary Button stays disabled until both are satisfied. There is no bypass, no "add anyway".
On success the Tag moves from missing to matched, and a quiet line confirms it was saved to the
source of truth — that confirmation is important; it tells the user the work compounds.

"Not applicable" dismisses the keyword with an optional note.

An "Apply accepted keywords" Button appears once at least one is accepted; it calls
`POST /v1/runs/{id}/keywords/apply` and routes to the new run's live view.

### `TexEditor`
CodeMirror 6, `--font-mono`, LaTeX syntax highlighting, line numbers. Debounced local autosave;
explicit "Save and compile" for the server round-trip. Compile errors render inline at the
reported line (RG-035) and as a summary above the editor. Never block editing while compiling.

### `ReviewPanel`
The eight categories as rows: name, weight (mono), score out of 10, and the reviewer's comment.
The must-fix list above them, as the reviewer returned it. Both come straight from
`runs.resume_review`.

### Reuse from v1
`app.py render_result`, `_render_ats_tab`, `render_tex_editor` for the information architecture —
v1 already decided what to show; this ticket decides how. `runs.ats` and `runs.resume_review`
carry v1's exact key names, so the panels read them directly.

### Tests
- `ScoreHero` renders both scores with mono numerals and the correct grade band.
- The gate's primary button is disabled without evidence and enabled with it.
- Accepting a keyword moves the tag and shows the source-of-truth confirmation.
- Editing the LaTeX and compiling updates the PDF preview.
- A compile error renders at the correct line.
- Run warnings appear on the page.
- `jest-axe`: the dialog traps focus and returns it on close.

### Definition of done
Seven tests green; the split layout works at 1200px and collapses cleanly below.

### Out of scope
Version diffing between runs.
