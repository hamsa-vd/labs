# arey Docs — UI kit

The documentation surface: sticky glass header, 240px sidebar, 68ch prose column, 216px "On this page" rail.

## Parts (`DocsParts.jsx`)
- `DocsHeader` — glass header with product switcher links, search + `⌘K`, theme toggle.
- `CodeBlock` — filename/lang strip, copy button that confirms in place, mono body. Prompt `$` is unselectable.
- `Callout` — note / warning / danger. Wash + 1px border + filled Phosphor glyph.
- `PropsTable` — reference table; types render in accent mono.
- `OnThisPage` — right rail; the active heading gets an ink left-border marker.

## Page (`DocsApp.jsx`)
One full Quickstart article showing every prose element: h1–h3, paragraphs, lists, inline code, a package-manager SegmentedControl driving the install snippet, two callouts, a reference table, and prev/next cards.

## Interactions to try
- Switch npm / pnpm / brew — the install snippet updates.
- Copy button on any code block turns into a check for 1.2 s.
- Theme toggle in the header.
- Sidebar and "On this page" both track selection.
