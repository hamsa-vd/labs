# Hamsa Designs

A monorepo of independently versioned design systems published under the `@hamsa-designs` scope. Each package contains tokens, assets, components, UI kits, guidelines, and a `SKILL.md` for design agents.

## Layout

```
hamsa-designs/
  README.md                  ← this file
  ADDING-A-SYSTEM.md         ← conventions + checklist for system #2 onward
  package.json               ← npm workspaces root (no build step; packages are source-only)
  packages/
    arey/                    ← system #1
      styles.css             ← the only fixed path: the global entry, @import lines only
      tokens/                ← colors, typography, spacing, radius, elevation, motion, fonts, base
      assets/                ← logo.svg, logo-mark.svg
      components/            ← core · forms · feedback · navigation (+ internal/)
      ui_kits/               ← console · docs · mobile
      guidelines/            ← foundation specimen cards (.html)
      readme.md              ← the design guide: content fundamentals, visual foundations, iconography
      SKILL.md               ← agent-skill wrapper
      thumbnail.html
```

## Systems

| Package | Brand | Status | Surfaces |
| --- | --- | --- | --- |
| `@hamsa-designs/arey` | arey | Active | Console (web app) · Docs · Mobile (iOS) |

## Using Arey

Install the package from the workspace or configured package registry:

```sh
pnpm add @hamsa-designs/arey
```

```jsx
import '@hamsa-designs/arey/styles.css';
import { Button, Card, Input } from '@hamsa-designs/arey/react';
```

Components are plain JSX with React as a peer dependency. All styling resolves through CSS custom properties. Load `styles.css` once and set `data-theme` on `<html>` when selecting a theme.

Tokens and assets also have stable subpath exports:

```js
import '@hamsa-designs/arey/tokens/colors.css';
import logoUrl from '@hamsa-designs/arey/assets/logo.svg';
```

The complete design guidance remains in `packages/arey/readme.md`; agent tools can consume `packages/arey/SKILL.md` or the exported `@hamsa-designs/arey/skill` file.

## Rules that keep the monorepo coherent

1. **No cross-package imports.** A component in one system never imports from another. Shared ideas are copied, not linked — systems are allowed to diverge.
2. **One global entry per package.** `styles.css` contains `@import` lines only; every token and `@font-face` file is reachable from it.
3. **Semantic aliases only in components.** Components reference `--text-body`, `--surface-card`, `--accent-solid` — never a base ramp value like `--grey-600`. This is what makes theme swapping total.
4. **Every component is a trio.** `Name.jsx` + `Name.d.ts` (props contract) + `Name.prompt.md` (what & when, usage example, variants).
5. **UI kits recreate, they don't invent.** A kit's job is to show the real product. Anything undefined in the source stays deliberately blank with a disclaimer.
6. **Fonts and icons are declared, not assumed.** Substitutions are flagged in the package readme.

## Provenance

`packages/arey` was authored from stated preferences (references: Apple's Human Interface Guidelines and Vercel's design site, conceptually only — no assets or marks from either). The only supplied brand asset was the sketch wordmark now at `packages/arey/assets/logo.svg`. Full detail in `packages/arey/readme.md`.
