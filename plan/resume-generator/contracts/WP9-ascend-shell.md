# WP9 — Ascend shell extension and design foundations

Discharges RG-010, RG-011, RG-012, RG-013 as adapted by ADR-100.

Those four tickets assumed a greenfield Next.js app that had to build a token pipeline and 27
primitives from scratch. Ascend has already done that work: it consumes the arey system through
`@labs/design/arey` (components + `ThemeToggle`) and `@labs/design/arey.css` (tokens, icon fonts,
pre-harvested component CSS), with theme switching handled DS-agnostically by `<ThemeScript>` in
`app/layout.tsx`. **Do not rebuild any of it.** This package extends what exists.

Root: `apps/ascend/`. Run with `pnpm --filter @labs/ascend check`.

Read before starting:
- `app/ascend.css` — 203 lines, the whole app's bespoke CSS. Match its density and naming.
- `src/ui/app-shell.tsx` — the shell you are extending. Note the house style: very dense JSX,
  one-line components, no decorative comments. Write in that voice, not a different one.
- `app/(authenticated)/overview/page.tsx` — how a screen is composed.
- `/Users/liv-extech/repos/labs/references/resume_generator/Resume Agent.dc.html` — the design
  canvas. It is the visual and copy specification for everything in Epic E.
- `/Users/liv-extech/repos/labs/references/ascend/index.html` — the ascend prototype, whose visual
  language takes priority where the two disagree (it is the newer of the two).

---

## 1. Navigation

The design canvas groups navigation into three labelled sections. Ascend's sidebar currently has
one unlabelled list under a "Tracker" label. Extend it to:

| Section | Items |
| --- | --- |
| Tracker | Overview, Applications, Timeline, Needs review, Sync runs |
| Resume | Pipeline, New application, Import application |
| Material | Source of truth, Prompts, Templates |
| — | Settings |

`New application` is a primary action, not a plain nav row, and must be reachable in one click
from every screen (RG-013). Under 940px the mobile nav keeps its existing five-item shape; the
resume items reach mobile through the sheet, and nothing becomes unreachable at 360px.

Routes, all under the existing `(authenticated)` group:
```
/resume                      pipeline
/resume/new                  new application
/resume/import               import application
/resume/applications/[id]    result view
/resume/runs/[runId]         live run view
/resume/source-of-truth      career record
/resume/prompts              prompt editor
/resume/templates            template library
```
`/settings` already exists and gains resume sections in WP10.

Each route ships `loading.tsx` and `error.tsx` from day one. Loading renders static
`--bg-inset` skeleton blocks — **no shimmer**, per the arey guide. Error renders the arey empty-state
pattern with a sentence mapped from the error `code` and a "Try again" button calling `reset()`.

## 2. `src/ui/active-run-badge.tsx`

The reason a user can start a generation and navigate away. A client component in the top bar
showing `company · role` and the current stage label, linking to the run. It polls
`GET /api/v1/resume/runs/active` every 5 seconds while a run is live and not at all when none is.
It renders nothing when there is no active run — an empty slot, not a placeholder.

While a run is active the shell shows a 1px indeterminate accent bar under the top bar. That is
the arey loading pattern; do not add a spinner or a skeleton shimmer.

## 3. `src/ui/score.tsx`

Three small presentational components the result view and the pipeline table both use. They are
app composites, not design-system primitives, so they live here rather than in `@labs/design`.

```tsx
export function AtsScore({ value, grade, size }: { value: number | null; grade: string | null; size?: 'sm' | 'lg' })
export function ReviewScore({ value, size }: { value: number | null; size?: 'sm' | 'lg' })
export function ScorePair({ ats, review }: { ats: number | null; review: number | null })
```

Rules from the design canvas and the arey guide, all enforceable by test:
- The number **is** the graphic. No dial, no gauge, no gradient, no progress bar in a table row.
- Every numeral renders in `--font-mono`.
- ATS shows `58 / 100` with its grade word; review shows `8.7 / 10` with `Pass` or nothing.
- Pass/fail is carried by a colour dot, never by a row background and never by a left-border stripe.
- Thresholds are ATS ≥ 80 and review ≥ 8.0, imported from a single shared constant — not retyped
  per component. Put them in `src/domain/resume-scores.ts` with the rubric weights mirrored from
  the Python `RESUME_RUBRIC`, and a test asserting the mirrored weights sum to 1.0 and match the
  Python dict key for key (RG-034). Read
  `apps/resume-pipeline/resume_pipeline/pipeline/scoring.py` for the source values.
- `null` renders as `—` in mono, never as `0`. A missing measurement is not a bad score, and
  showing zero for "not scored yet" is the single most misleading thing this component could do.

## 4. `src/domain/resume-run.ts`

The node → user-facing label map, mirrored from the server so the client never invents prose.
Exactly the labels RG-042 specifies:

```
resolve_jd_input        Read the job description
load_inputs             Loaded your source of truth
create_targeting_brief  Built the targeting brief
generate_resume         Wrote the resume
review_documents        Reviewed against the rubric
ats_check_resume        Scored for ATS
revise_documents        Revised the resume
generate_cover_letter   Wrote the cover letter
persist_outputs         Saved
compile_pdfs            Compiled the PDF
```

Also export the ordered stage list and `runStageLabel(node: string): string`, which falls back to
the node name rather than throwing — an unknown node must not break the screen.

## 5. `src/ui/errors.ts`

`errorSentence(code: string): string` — maps each server error code to arey-voice copy: what
happened, then what to do. Cover at minimum `jd_too_short`, `missing_api_key`, `evidence_required`,
`unreadable_pdf`, `validation_failed`, `run_budget_exceeded`, `upstream_failed`, `compile_failed`,
`compile_timeout`, `not_found`, `conflict`, `forbidden`. An unknown code falls back to
"Something failed on our side. Try again in a moment."

Sentence case. No emoji. No exclamation marks.

## 6. CSS additions to `app/ascend.css`

Add only what the resume screens need, following the existing `ascend-` naming and the file's
existing density. Every visual value is `var(--token)`.

Non-negotiables from the arey guide, each testable:
- Cards use `--surface-card`, `--radius-card`, and **both** a hairline border and a soft shadow.
- Glass (`--surface-glass` + `--backdrop-glass`) only on floating layers — top bar, popovers,
  dialogs, sheets. Never on a static card.
- Press is `transform: scale(var(--press-scale))`. Focus is `--ring-focus` on `:focus-visible`
  only, replacing hover rather than stacking with it. Disabled is `opacity: .4` and nothing else.
- Radii nest downward: card → control → inner chip.
- No left-border accent stripes anywhere. One accent colour only.
- Entry motion is opacity + 4–8px rise + `scale(.98→1)` over 220ms with `--ease-out`; interactive
  feedback is 140ms. `@media (prefers-reduced-motion: reduce)` zeroes every duration and the
  press scale.
- 940px is the shell breakpoint, matching what ascend already uses.

## 7. The lint rule

`eslint-rules/no-raw-design-values.js`, wired into `eslint.config.mjs`. Errors on a hex colour, an
`rgb()`/`hsl()` literal, a px border-radius, a box-shadow literal, a transition duration, or a
font-family string appearing in `app/ascend.css` or in an inline `style` prop under `app/` or
`src/ui/`. Allowed: `0`, `1px` hairlines, `100%`, and any `var(...)`.

This is RG-010's real deliverable in our setting: the token *pipeline* already exists via
`@labs/design`, but nothing currently stops a raw value being committed.

Run it across the existing codebase. If it flags pre-existing violations, **fix them** if they are
few and obviously mechanical; if they are many, report the count rather than weakening the rule.

## Acceptance criteria

1. All eight new routes render for a signed-in user, each with its own loading and error state.
2. Exactly one nav row is marked active per route, and the active state is `--bg-selected` fill
   plus `--text-accent` label with no left stripe.
3. "New application" is reachable in one click from every authenticated screen.
4. At 900px the sidebar is absent and the hamburger opens a focus-trapped sheet; Escape closes it
   and returns focus to the trigger. Nothing is unreachable at 360px, and no route scrolls
   horizontally at 360, 600, 940, 1200 or 1920px.
5. `ActiveRunBadge` renders nothing with no active run, and with a mocked in-flight run appears on
   an unrelated screen and links to it.
6. Score components render mono numerals, `—` for null, and the correct pass/fail dot at the
   threshold boundaries exactly (80 and 8.0 pass; 79.9 and 7.9 do not).
7. The TypeScript rubric matches the Python `RESUME_RUBRIC` key for key and sums to 1.0.
8. `runStageLabel` returns the specified label for each of the ten nodes and falls back for an
   unknown one.
9. `errorSentence` covers every listed code and falls back for an unknown one; no string contains
   an emoji or an exclamation mark — assert that across the whole map.
10. The lint rule errors on a fixture containing `#0071e3` and on `border-radius: 12px`, and passes
    the same fixture rewritten with `var(--accent-solid)` and `var(--radius-card)`.
11. `pnpm --filter @labs/ascend check` is green, and the existing 63 tests still pass.

## Test paths (test agent writes only here)

```
apps/ascend/src/ui/score.test.tsx
apps/ascend/src/domain/resume-scores.test.ts
apps/ascend/src/domain/resume-run.test.ts
apps/ascend/src/ui/errors.test.ts
apps/ascend/eslint-rules/no-raw-design-values.test.ts
apps/ascend/src/ui/resume-nav.test.tsx
```

`vitest.config.ts` currently has `environment: 'node'` and `include: ['src/**/*.test.ts']`.
Component tests need a DOM environment and a `.tsx` include. Change `vitest.config.ts` — it is
yours for this package — to add `src/**/*.test.tsx` and `eslint-rules/**/*.test.ts`, and use
`environmentMatchGlobs` (or a `// @vitest-environment jsdom` docblock) so the existing node-environment
tests are unaffected. Add `jsdom` and `@testing-library/react` as devDependencies. Confirm the
existing 63 tests still pass afterwards; if the environment change disturbs them, that is a finding
to report, not something to paper over.

## Source paths (implementing agent writes only here)

```
apps/ascend/app/(authenticated)/resume/**            (route files, loading.tsx, error.tsx)
apps/ascend/src/ui/app-shell.tsx                     (nav extension)
apps/ascend/src/ui/active-run-badge.tsx
apps/ascend/src/ui/score.tsx
apps/ascend/src/ui/errors.ts
apps/ascend/src/domain/resume-scores.ts
apps/ascend/src/domain/resume-run.ts
apps/ascend/app/ascend.css
apps/ascend/eslint-rules/no-raw-design-values.js
apps/ascend/eslint.config.mjs
```

Route pages in this package render their heading, their shell placement, and their loading and
error states only. **Screen content is WP10** — do not build tables, forms, editors, or fetch data
here. A page whose body is a heading and an empty state is the correct output of this package.
