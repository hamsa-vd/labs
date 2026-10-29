# RG-010 — Design token pipeline from the external design-system repo

**Epic:** B — Design system · **Depends on:** RG-001 · **Estimate:** M · **Labels:** design-system, web

## Product requirement

**Problem.** The arey design system lives in a separate GitHub repo with no build step and no
package. Copying values into the app guarantees drift; importing its JSX directly is not
buildable in Next.js.

**Outcome.** Token changes made in the design-system repo reach the product in one command, and
it is impossible to commit a hard-coded colour, radius, shadow, or duration.

**Acceptance criteria**
- `pnpm ds:sync` updates tokens from a pinned upstream commit and reports what changed.
- A PR introducing `#0071e3` or `border-radius: 12px` in app code fails lint.
- Light and dark themes both switch entirely via `data-theme`, with no component-level branching.

## Technical plan

Implements ADR-002 (`plan/02-design-system-strategy.md`) — the *consume* half.

### Files
```
packages/tokens/upstream.json          { repo, ref (commit SHA), paths[] }
packages/tokens/scripts/sync.ts        fetch → write → verify
packages/tokens/css/                   generated: fonts, colors, typography, spacing, radius,
                                       elevation, motion, base  (DO NOT EDIT header on each)
packages/tokens/src/index.ts           export const tokens = {...} as const  (name → var())
packages/tokens/src/types.ts           type TokenName = '--accent-solid' | …  (generated)
packages/tokens/PARITY.md              upstream SHA + sync date log
eslint-config/no-raw-design-values.js  custom rule
```

### Steps
1. `sync.ts` fetches the eight `tokens/*.css` files plus `styles.css` at the pinned SHA, writes
   them into `packages/tokens/css/` with a generated-file banner, and parses every
   `--custom-property` declaration into the TS union and the `tokens` object.
2. **Removal guard:** after generating, scan `packages/ui/**` and `apps/web/**` for `var(--x)`
   usages. If a used token no longer exists upstream, exit non-zero and list them. Bumping the
   pin must be a deliberate, reviewed PR.
3. `apps/web/src/app/layout.tsx` imports `@repo/tokens/css/index.css` once, globally. This is the
   only global stylesheet in the app.
4. Custom ESLint rule `no-raw-design-values`: error on hex colours, `rgb()`/`hsl()` literals,
   `px` radii, `box-shadow` literals, `transition` durations, and font-family strings inside
   `.module.css` and inline `style` props. Allowed: `0`, `1px` hairlines, `100%`, `var(...)`.
5. Fonts: Instrument Sans + JetBrains Mono via `next/font`, exposed as `--font-sans`/`--font-mono`
   so the upstream `fonts.css` contract still holds without a network font request.

### Tests
- `sync.ts` against a fixture: known input CSS produces the expected union and object.
- Removal guard fires when a referenced token is deleted from the fixture.
- ESLint rule: fixture file with a hex colour errors; the same file using `var(--accent-solid)` passes.

### Definition of done
Tokens generated and committed, pin recorded, lint rule active in CI.

### Out of scope
Components (RG-011).
