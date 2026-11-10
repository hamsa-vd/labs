# arey — Design System

**arey** is a personal design system built for one taste: the structural clarity and material honesty of Apple's Human Interface Guidelines, crossed with the monochrome restraint and typographic precision of a Vercel-style developer product. It is a *from-scratch* system — not a recreation of either company's brand.

## Provenance & sources

| Source | Type | Notes |
| --- | --- | --- |
| `developer.apple.com/design/human-interface-guidelines` | Public guidance, cited by the owner as a reference | Informs depth, materials (glass/blur), motion character, control ergonomics, hit-target sizes, the "deference" instinct. Referenced conceptually only — no Apple assets, fonts, or marks are used or reproduced. |
| `vercel.com/design` | Public guidance, cited by the owner as a reference | Informs the greyscale-first palette, hairline borders, generous whitespace, mono-for-metadata habit, and copy that reads like a changelog. Referenced conceptually only — no Vercel assets or marks are used. |
| `uploads/logo-1785511170098.svg` | Supplied by the owner | The only real brand asset provided. A hand-sketched "AREY" wordmark drawn as open bezier strokes. It shipped with no stroke styling (a `.majestic-sketch` class with no matching CSS), so it rendered as filled black blobs. Copied to `assets/logo.svg` with `fill:none; stroke:currentColor; stroke-width:5; round caps` added — geometry untouched. |

No codebase, Figma file, or deck was provided. Every component, screen, and token here was authored for this system from the owner's answered preferences:

> serif-adjacent restraint · pure greyscale neutrals · a single Apple-blue accent · 12px radius language · translucent glass surfaces · full dual theme · roomy density · spring easing · Phosphor icons

**No logo was invented.** Where a mark is needed, `assets/logo.svg` is used; where the wordmark would be too small to read as a sketch, the brand name is set in plain lowercase type (`arey`) in the sans face.

---

## Products represented

Three surfaces were requested, and each has a UI kit:

1. **arey Console** (`ui_kits/console/`) — the web app. Sidebar shell, project table, detail views, settings. The workhorse surface; densest use of the component library.
2. **arey Docs** (`ui_kits/docs/`) — the documentation site. Three-column layout, code blocks, callouts, on-page nav.
3. **arey Mobile** (`ui_kits/mobile/`) — iOS-style app screens. Large-title navigation, grouped inset lists, sheets, tab bar.

---

## Content fundamentals

**Voice: a calm engineer who ships.** Declarative, present tense, specific. arey copy states what is true and what will happen, then stops. It never sells, never celebrates, never apologises at length.

**Casing.** Sentence case everywhere — buttons, headings, menu items, table headers, toasts. The only uppercase is the mono eyebrow (`--type-eyebrow`, tracked +0.08em) used for section kickers and column groups. Never Title Case A Button Like This. The brand name is lowercase in prose (`arey`) and stays lowercase mid-sentence.

**Person.** Second person for anything the user does; first-person plural only for things the system does on their behalf.

- ✅ "Your project is deploying." / "Rotate this key" / "We'll email you when the build finishes."
- ❌ "Let's get you set up!" / "Awesome — your project is live! 🎉" / "Oops, something went wrong."

**Length discipline.** Buttons: 1–3 words, verb-first ("Create project", "Rotate key", "Revoke"). Empty states: one line of what's missing + one action. Errors: what happened, then what to do — no blame, no exclamation marks.

- ✅ "Build failed at step 3. Check the install log."
- ❌ "Uh oh! We couldn't build your project. Please try again later!"

**Numbers and time are mono.** Any value a machine produced — durations, byte sizes, commit SHAs, version strings, IDs, timestamps, percentages in tables — is set in `--font-mono`. This is the system's most recognisable typographic tic. `1.2 s`, `v4.2.0`, `a3f91c8`, `128 MB`. Units are separated by a thin space and are never bold.

**Relative time in UI, absolute on hover.** "3 m ago" in a table cell; `2026-07-31 14:02 UTC` in the tooltip.

**Punctuation.** No exclamation marks. No em-dash pile-ups in UI copy (fine in prose like this readme). Serial commas. Periods on full sentences in body copy and descriptions; no periods on labels, buttons, table headers, or single-clause helper text.

**Emoji: never.** Not in UI, not in empty states, not in docs. Status is carried by a colour dot, a Phosphor glyph, or a Badge — never by 🎉 or ⚠️.

**Vocabulary.** *Project*, *deployment*, *environment*, *key*, *member*, *usage*, *log*. Prefer "Remove" to "Delete" for reversible actions and "Delete" only when it is permanent (and then require typing the name to confirm). "Sign in", not "Log in". "Settings", not "Preferences" (except on mobile, where iOS convention wins). Docs use the imperative for steps ("Install the CLI", "Run `arey dev`").

**Vibe.** Quiet confidence. A page should feel like it was set by a typographer and shipped by an SRE. If a sentence could appear in a changelog without editing, it's on voice.

---

## Visual foundations

### Colour

Pure neutral greyscale — no warm or cool tint anywhere. `--grey-*` runs `#ffffff → #000000` with no hue, deliberately, so that the one saturated colour in the system reads as *signal*.

**One accent: `--accent-solid`.** `#0071e3` in light, `#0a84ff` in dark. It appears on primary buttons, focus rings, links, active nav rows, and selected states — nowhere else. If two blue things are on screen competing, one is wrong. Semantic colours (green/red/amber) appear only as status, and only as a wash + text pair or a 6px dot, never as large fields.

Every colour is consumed through a semantic alias (`--text-body`, `--surface-card`, `--border-default`), never a base ramp value. That's what makes the dual theme total: swapping `data-theme` swaps everything, because no component names a grey directly.

**Dark is not inverted light.** Light theme canvas is `--grey-100` with `#fff` cards floating on it — surfaces are *lighter* than the page. Dark theme canvas is true `#000` with `#111` cards — surfaces are *lighter* than the page there too, so elevation reads the same direction in both. Dark borders become brighter (`rgba(255,255,255,.12)`), never darker.

### Type

`Instrument Sans` for everything readable; `Space Mono` for everything machine-adjacent. Two faces, no third. Both are bundled with the package under `assets/fonts`, so the stylesheet does not depend on a remote font service.

Tracking tightens as size grows: `-0.03em` at display, `-0.02em` at headings, `-0.005em` at body, `0` at 12px and below. Weights used: 400, 500, 600. **700 is reserved and rarely used; there is no light weight.** Body copy is never centred except in an empty state or a modal. Prose is capped at `--prose-max` (68ch). Optical alignment matters more than grid alignment — a 56px display heading sits flush-left with the 14px paragraph beneath it.

### Spacing & layout

4px base, roomy end of the scale. Section rhythm is 80px; card padding is 24px; control padding is 16px horizontal. Adjacent siblings are laid out with flex/grid + `gap`, never margins.

Fixed elements: the Console top bar (56px) and the Docs header are `position: sticky` with glass; the mobile tab bar is fixed to the bottom with glass; the Console sidebar (264px) scrolls independently. Content is capped at `--content-max` (1120px) and centred; docs prose at 68ch.

### Surfaces, borders & elevation

Cards are `--surface-card` at `--radius-card` (16px) with a **hairline `--border-subtle` plus a soft shadow** — both, always. A border without a shadow reads flat and cheap; a shadow without a border smudges at the edge. Shadows are large-radius and low-opacity (`--shadow-md` is 12px blur at 7% black); nothing in the system uses a hard or offset-heavy shadow.

**Glass is the signature material.** Any surface that floats over content — top bars, tab bars, popovers, dropdowns, sheets, toasts — uses `background: var(--surface-glass)` + `backdrop-filter: var(--backdrop-glass)` (`saturate(180%) blur(20px)`) + a bright hairline (`--border-glass`). Blur is used *only* for that: separating a floating layer from what's behind it. It is never decorative and never applied to a static card. Scrims behind modals are `--surface-scrim` (28% black light, 56% dark) with no blur, so the sheet's own blur stays legible.

**Protection:** where a fixed bar overlaps scrolling content, the glass layer *is* the protection — no gradient fades. The one exception is long scroll containers (sidebars, table bodies), which get an 24px `linear-gradient` mask at the bottom edge.

### Radii

12px is the default voice (`--radius-control`); cards step up to 16px; sheets to 20px; pills for Badges, Tags, and Avatars only. Nesting steps *down*: a 16px card holds a 12px control holds a 6px inner chip. Nothing in the system is square-cornered except full-bleed images and table cell dividers.

### Motion

Everything eases out; nothing eases in. `--ease-out` (`cubic-bezier(.22,1,.36,1)`) is the default. Interactive feedback gets `--ease-spring` (a light overshoot) at 140ms. Surface entries — popovers, sheets, toasts — use opacity + `translateY(4–8px)` + `scale(.98 → 1)` over 220ms. Theme swaps and text disclosure are opacity-only at 80ms. Nothing bounces twice; nothing rotates; nothing slides horizontally. `prefers-reduced-motion` zeroes every duration and the press scale.

### Interaction states

- **Hover** on filled controls: shift to the next darker solid token (`--accent-solid-hover`). On ghost/quiet controls: a `--bg-hover` wash (4% ink / 8% paper). On links and images: opacity to `.7`. Never a colour change on text links.
- **Press:** `transform: scale(.97)` (`--press-scale`) plus `--bg-active`. Physical, immediate, no shadow change. This is the most Apple-flavoured part of the system.
- **Focus:** `--ring-focus` — a 3px 22%-opacity accent ring, offset 0, *replacing* any hover state. Keyboard only (`:focus-visible`).
- **Disabled:** `opacity: .4`, `cursor: not-allowed`, no other change — the control keeps its shape so layout never shifts.
- **Selected / active nav:** `--bg-selected` fill + `--text-accent` label. No left-border accent stripes anywhere in this system.
- **Loading:** a 1px indeterminate accent bar under the top bar for page work; an in-place spinner replacing the label for control work. No skeleton shimmer — skeletons are static `--bg-inset` blocks.

### Imagery

There is no illustration library and none should be invented. Imagery, when present, is **cool-neutral, high-key, and low-saturation** — product screenshots on grey, or full-bleed photography desaturated toward the greyscale palette. No grain, no duotone, no gradient meshes. Full-bleed images sit square-cornered and edge-to-edge; inset images take `--radius-card` and a hairline border. Empty slots use a `--bg-inset` block with a centred Phosphor glyph at `--text-tertiary`.

### Explicitly not in this system

Bluish-purple gradients. Aggressive background gradients. Emoji. Cards with a coloured left border. Multiple accent colours. Drop shadows on text. Icon-in-a-tinted-rounded-square feature grids. Rounded "pill" body text containers. Any second display face.

---

## Iconography

**Phosphor Icons** — chosen for its rounded terminals (which agree with the 12px radius language) and its six weights. All six weights ship vendored inside the package; import `@hamsa-designs/arey/styles.css` once and every weight is available with no CDN dependency and no separate `<link>` tags:

```js
import '@hamsa-designs/arey/styles.css';
```

```html
<!-- disposable HTML prototypes: point at the built, self-contained stylesheet -->
<link rel="stylesheet" href="https://unpkg.com/@hamsa-designs/arey/dist/styles.css">
```

**Substitution flag:** no icon assets were supplied with the brand, so Phosphor is the owner's chosen set rather than a copy of an in-house library. Nothing was hand-drawn.

Rules:

- Use the **`<Icon>`** component (`components/core/Icon.jsx`), never a raw `<i>` tag, so size and weight stay tokenised.
- **Regular** weight is the default, everywhere. **Fill** marks a *selected* state only — an active tab bar item, a starred row. **Bold** is used only at 12–14px where Regular loses hairlines.
- Sizes: 14px inline with 13px labels, 16px in controls and nav rows, 20px on mobile tab bars, 24px for empty-state and feature glyphs. Never larger than 24 in UI; a 48px+ glyph only appears in an empty state.
- Icons inherit `currentColor`. An icon is never the accent colour unless its text label is too.
- Icon-only controls are always ≥36px on web / ≥44px on mobile, and always carry an `aria-label`.
- **No unicode characters used as icons** (no `×`, `→`, `✓`, `•` standing in for glyphs) except `⌘`/`⌥`/`⇧`/`↵` inside the `Kbd` component, where the unicode *is* the correct typography.
- **No emoji, ever.** Status is a Phosphor glyph or a colour dot.

---

## Consuming the package

```sh
npm install @hamsa-designs/arey
```

```jsx
import '@hamsa-designs/arey/styles.css'; // once, anywhere near the app root — tokens + icon fonts
import { Button, Card } from '@hamsa-designs/arey/react';
```

`@hamsa-designs/arey/react` resolves to a compiled `dist/` build (plain JS, `react` external, bundled
type declarations) — no consumer build configuration (no `transpilePackages`, no JSX loader for
`node_modules`) is required. Set `data-theme="dark"` on `<html>` for dark mode; every token and
every component follows that switch automatically.

## Index

**Root**
- `styles.css` — the source global entry (`@import` lines only); the published, self-contained
  build is `dist/styles.css` (see above).
- `readme.md` — this document.
- `SKILL.md` — Agent Skills wrapper, so this folder works as a Claude Code skill.
- `thumbnail.html` — homepage tile.

**`tokens/`** — `fonts.css` · `colors.css` · `typography.css` · `spacing.css` · `radius.css` · `elevation.css` · `motion.css` · `base.css`

**`assets/`** — `logo.svg` (full sketch wordmark) · `logo-mark.svg` (the "A" alone)

**`guidelines/`** — foundation specimen cards (Type, Colors, Spacing, Effects, Brand) plus prose deep-dives.

**`components/`**
- `core/` — Button, IconButton, Icon, Card, Badge, Tag, Kbd, Avatar
- `forms/` — Input, Textarea, Select, Checkbox, Radio, Switch, Field
- `feedback/` — Dialog, Toast, Tooltip, Spinner, ProgressBar, EmptyState
- `navigation/` — Tabs, SegmentedControl, Breadcrumbs, SidebarNav, ListRow
- `data/` — Table, TableHead, TableCell, TableRow
- `internal/` — `sheet.jsx`: shared `injectSheet`/`cx` runtime and the text-control base styles. Not part of the public export surface.

**`ui_kits/`**
- `console/` — arey Console web app (dashboard, table, detail, settings)
- `docs/` — arey Docs site
- `mobile/` — arey Mobile, iOS-style screens

### Intentional additions

- **`Icon`** — a thin wrapper over the Phosphor web font. Added so weight/size stay tokenised and consumers never hand-write `<i class="ph …">`.
- **`Field`** — label + helper + error wrapper shared by all form controls. Added to keep the error/description pattern identical across Input, Select, and Textarea rather than duplicating it five times.
- **`Kbd`** — shortcut key rendering. Added because the mono-accent voice makes shortcut display a recurring need in Console and Docs.
