# design-systems

A monorepo of design systems. Each package is a self-contained system: tokens, assets, components, UI kits, guidelines, and a `SKILL.md` so it can be used directly as an agent skill.

## Layout

```
design-systems/
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
| `packages/arey` | arey | Active | Console (web app) · Docs · Mobile (iOS) |

## Consuming a system

Link the one global stylesheet and use the components as source:

```html
<link rel="stylesheet" href="packages/arey/styles.css">
```

```jsx
import { Button } from './packages/arey/components/core/Button.jsx';
```

Components are plain JSX with no dependencies beyond React. All styling resolves through CSS custom properties, so a system can be dropped into any stack — the only contract is that `styles.css` is loaded and `data-theme` is set on `<html>`.

## Rules that keep the monorepo coherent

1. **No cross-package imports.** A component in one system never imports from another. Shared ideas are copied, not linked — systems are allowed to diverge.
2. **One global entry per package.** `styles.css` contains `@import` lines only; every token and `@font-face` file is reachable from it.
3. **Semantic aliases only in components.** Components reference `--text-body`, `--surface-card`, `--accent-solid` — never a base ramp value like `--grey-600`. This is what makes theme swapping total.
4. **Every component is a trio.** `Name.jsx` + `Name.d.ts` (props contract) + `Name.prompt.md` (what & when, usage example, variants).
5. **UI kits recreate, they don't invent.** A kit's job is to show the real product. Anything undefined in the source stays deliberately blank with a disclaimer.
6. **Fonts and icons are declared, not assumed.** Substitutions are flagged in the package readme.

## Provenance

`packages/arey` was authored from stated preferences (references: Apple's Human Interface Guidelines and Vercel's design site, conceptually only — no assets or marks from either). The only supplied brand asset was the sketch wordmark now at `packages/arey/assets/logo.svg`. Full detail in `packages/arey/readme.md`.
