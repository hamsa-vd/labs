# RG-011 — Rebuild arey primitives as typed React components

**Epic:** B — Design system · **Depends on:** RG-010 · **Estimate:** L · **Labels:** design-system, web

## Product requirement

**Problem.** The upstream components are preview-environment JSX: untyped, not RSC-safe, no
tree-shaking, no tests. The product needs the same visual language as real, typed components.

**Outcome.** Every screen in Epic E is assembled from `@repo/ui` and adds no bespoke styling.

**Acceptance criteria**
- Each component matches its upstream counterpart's anatomy and every interaction state
  (hover, press, focus-visible, disabled, selected).
- Every visual value in `packages/ui` is a `var(--*)` reference. Zero literals.
- Keyboard operation and `prefers-reduced-motion` work on every interactive component.

## Technical plan

Implements ADR-002 — the *rebuild* half. Upstream JSX is the **spec**; do not copy it verbatim.

### Files
```
packages/ui/src/core/{Button,IconButton,Icon,Card,Badge,Tag,Kbd,Avatar}.tsx
packages/ui/src/forms/{Input,Textarea,Select,Checkbox,Radio,Switch,Field}.tsx
packages/ui/src/feedback/{Dialog,Toast,Tooltip,Spinner,ProgressBar,EmptyState}.tsx
packages/ui/src/navigation/{Tabs,SegmentedControl,Breadcrumbs,SidebarNav,ListRow}.tsx
packages/ui/src/**/<Name>.module.css
packages/ui/PARITY.md                upstream path → our file → verified SHA → deviations
packages/ui/src/index.ts
```

### Rules (from the arey guide — non-negotiable)
- Sentence case on every label. No emoji, ever. No unicode glyphs standing in for icons.
- Machine-produced values (durations, scores, SHAs, timestamps, percentages in tables) use
  `--font-mono`.
- Cards: `--surface-card`, `--radius-card`, **hairline border and soft shadow, both**.
- Glass (`--surface-glass` + `--backdrop-glass`) only on floating layers: top bar, popovers,
  dialogs, toasts. Never on a static card.
- Press = `transform: scale(var(--press-scale))`. Focus = `--ring-focus`, `:focus-visible` only,
  replacing hover. Disabled = `opacity: .4` and nothing else.
- Radii nest downward: 16px card → 12px control → 6px inner chip.
- No left-border accent stripes. One accent colour only.
- `Icon` wraps the Phosphor web font; never a raw `<i>`. Regular by default, Fill only for
  selected state, Bold only at 12–14px.

### Steps
1. For each component: read the upstream file, list its props and states in `PARITY.md`, then
   implement with CSS Modules + tokens. Server-component-safe by default; `'use client'` only on
   components with state or refs (Dialog, Toast, Tooltip, Tabs, Switch, Select).
2. Dialog and Tooltip build on Radix primitives for focus trap and positioning, styled entirely
   by our CSS Modules. Do not re-implement focus management.
3. Motion: entries are opacity + `translateY(4–8px)` + `scale(.98→1)` over 220ms with
   `--ease-out`. Interactive feedback 140ms with `--ease-spring`.
   `@media (prefers-reduced-motion: reduce)` zeroes every duration and the press scale.
4. Ship a Storybook (or a `/kitchen-sink` route, if Storybook is too much weight) with every
   component in every state, light and dark.

### Tests
- `vitest` + Testing Library per component: renders, prop variants, disabled blocks the handler.
- `jest-axe` on every component; zero violations.
- A repo-wide test asserting no literal hex or px-radius appears in `packages/ui/**/*.module.css`.
- Playwright visual snapshots of the kitchen sink in both themes.

### Definition of done
All 27 components shipped with a `PARITY.md` row each; a11y and token tests green.

### Out of scope
App-specific composites — ScoreDial, ATSKeywordList, RunTimeline — which belong to their
feature tickets in Epic E.
