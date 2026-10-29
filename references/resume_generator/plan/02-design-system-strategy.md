# ADR-002 — consuming the arey design system

Status: accepted · Date: 2026-07-31

## Context

The design system lives in an external GitHub repo (`hamsa-vd/design-systems`, the
`arey` system). It ships CSS custom-property token files (`tokens/*.css`), a global
`styles.css`, plain-JSX components (`components/core`, `forms`, `feedback`, `navigation`),
and UI kits. It is **not** an npm package, has no build step, and its components are authored
as browser-loaded JSX for a design-preview environment — not for a Next.js RSC build.

Three options were considered.

| Option | Verdict |
| --- | --- |
| **A. Vendor everything** — copy tokens + components into `packages/ui` once | Rejected. Drift is immediate and silent; upstream fixes never arrive. |
| **B. Consume wholesale** — git submodule, import the JSX directly | Rejected. The components are not RSC-safe, have no types, no tree-shaking, and no versioning. A design-system edit could break the build with no signal. |
| **C. Split the layer** ✅ | Accepted. |

## Decision — split at the token line

**Tokens are consumed. Components are rebuilt.**

- **Tokens (consume, never edit).** A sync script pulls `tokens/*.css` + `styles.css` from a
  pinned upstream ref into `packages/tokens`, and generates a TypeScript union of every custom
  property name. Pinned by commit SHA in `packages/tokens/upstream.json`. Nothing in the app may
  write a raw hex, px radius, font stack, shadow, or duration — only `var(--*)`. A lint rule
  enforces it (RG-010).
- **Components (rebuild in `packages/ui`).** Each primitive is written once as a typed React
  component whose every visual value is a token reference, matching the upstream component's
  anatomy and states one-for-one. The upstream JSX is the **specification**; our file is the
  implementation. This gives RSC compatibility, prop types, tests, and a stable API — while
  a token change upstream still flows through automatically, which is where 90% of visual
  drift actually happens.

### Why not just rebuild the tokens too

Because tokens are the part with real churn and zero integration risk — they are plain CSS
custom properties with a stable naming contract. Components are the part with real integration
risk and near-zero churn. Consume the churn, own the risk.

### Sync protocol

`pnpm ds:sync` — fetches the pinned ref, rewrites `packages/tokens/css/`, regenerates types,
and fails if a token that any `packages/ui` component references has disappeared. Bumping the
pin is a deliberate PR with a visual-diff review, never automatic.

### Parity register

`packages/ui/PARITY.md` is a table: upstream component path → our file → last-verified upstream
SHA → deliberate deviations. A component may not be added to `packages/ui` without a row.

## Consequences

- Upstream token edits reach the app in one command.
- Upstream *component* edits require a manual port, logged in `PARITY.md`. Accepted cost.
- The app never loads the upstream `_ds_bundle.js` at runtime. Zero third-party runtime JS.
- If the design system later ships a proper npm package with RSC-safe components, RG-011 can be
  revisited — the parity register makes that migration mechanical.
