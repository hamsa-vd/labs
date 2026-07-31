# Adding a design system

Each system is one package under `packages/`. Copy this checklist.

## 1. Scaffold

```
packages/<brand>/
  styles.css
  tokens/{fonts,colors,typography,spacing,radius,elevation,motion,base}.css
  assets/
  components/<group>/
  ui_kits/<product>/
  guidelines/
  readme.md
  SKILL.md
  thumbnail.html
```

## 2. Tokens

- `styles.css` is `@import` lines only — never a rule.
- Declare **base values** (`--grey-500`, `--blue-500`) and **semantic aliases** (`--text-body`, `--surface-card`, `--accent-solid`) separately. Components use aliases only.
- Every semantic alias is re-declared under each theme scope (`:root`, `[data-theme="dark"]`). If a component names a base ramp value, theming breaks — that's the one hard rule.
- Non-visual tokens (durations, easings, scale factors) carry `/* @kind other */` so tooling doesn't try to classify them as colour or spacing.

## 3. Components

- One `Name.jsx` per component with a **named PascalCase export**; siblings may import each other by relative path.
- `Name.d.ts` beside it with the props interface, one doc comment per prop. This is the public contract.
- `Name.prompt.md` beside it: one-sentence "what & when", a small JSX example, then notable variants.
- Real CSS states (`:hover`, `:active`, `:focus-visible`, `:disabled`) via an injected stylesheet — not JS state juggling. See `packages/arey/components/internal/sheet.jsx` for the pattern.
- Group by concern (`core/`, `forms/`, `feedback/`, `navigation/`). One `@dsCard`-tagged `.html` per directory showing every variant, dense and scannable.

## 4. Guidelines

Small specimen cards, one sub-concept each (~700px wide, under 400px tall) — primary vs neutral vs semantic colours as separate cards, display vs body vs mono type as separate cards. First line of each file:

```html
<!-- @dsCard group="Colors" viewport="700x140" name="Neutral ramp" subtitle="one line" -->
```

## 5. The readme is the deliverable

`readme.md` must answer, with specific examples:

- **Provenance** — every source, with links/paths, and what was substituted or missing.
- **Content fundamentals** — voice, casing, person, punctuation, emoji policy, vocabulary, and 3+ ✅/❌ copy pairs.
- **Visual foundations** — colour, type, spacing, surfaces, borders, elevation, radii, motion, every interaction state, imagery treatment, and an explicit "not in this system" list.
- **Iconography** — which set, which weights mean what, sizes, and whether unicode or emoji are ever used.
- **Index** — a manifest of the package.

## 6. Never

- Draw, reconstruct, or approximate a real company's logo. If no mark is supplied, set the brand name in type and say so in the readme.
- Invent components the source doesn't define. Additions go under "Intentional additions" with a one-line reason.
- Round values to a 4/8px grid when the source says otherwise. If the source says 5px, write 5px.
