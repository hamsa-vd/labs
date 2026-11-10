---
name: arey-design
description: Design and implement Arey-branded interfaces, applications, prototypes, and visual assets using the canonical Arey tokens, components, assets, content rules, and UI kits. Use whenever creating, reviewing, or modifying an Arey user interface in plain HTML, React, or another application framework.
---

# Use Arey

1. Read `readme.md` before making visual or content decisions.
2. Inspect only the relevant component contracts, prompts, UI kits, tokens, and assets for the task.
3. Reuse an existing component when one exists. Do not recreate it locally.
4. Use semantic tokens; never hard-code an equivalent colour, type style, radius, spacing value, shadow, or motion value.

## Choose the output

- For production React, install `@hamsa-designs/arey`, import `@hamsa-designs/arey/styles.css` once, and import components from `@hamsa-designs/arey/react`.
- For production in another framework, consume the CSS tokens and assets from the package and implement framework-native components that preserve the documented contracts.
- For disposable standalone HTML prototypes, load the version-pinned package stylesheet from a package CDN and build with semantic tokens. Treat prototype markup as design output, not as the production component implementation.
- For visual assets, use the supplied assets. Do not redraw or approximate the logo.

Set `data-theme="dark"` on `<html>` for dark mode. Follow accessibility, interaction-state, responsive-layout, and reduced-motion guidance in `readme.md`.

When the request is underspecified, infer routine product details from the relevant UI kit. Ask only when a missing decision would materially change the product.
