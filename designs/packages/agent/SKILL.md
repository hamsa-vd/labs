---
name: hamsa-designs
description: Discover and apply the Hamsa design system installed in the current application. Use for UI design, frontend implementation, visual review, content design, prototypes, or application changes whenever package.json contains an @hamsa-designs design-system dependency.
---

# Use Hamsa Designs

Run the detector located beside this `SKILL.md` before making UI or content decisions. Resolve the command path from this skill's directory, not from the application:

```sh
node <this-skill-directory>/scripts/detect.mjs
```

The command searches upward for the application's `package.json`, finds installed `@hamsa-designs/*` design-system dependencies, and returns their manifests and absolute resource paths.

For the applicable system:

1. Read the returned `skill` and `guidelines` files completely.
2. Inspect only the relevant component prompts, tokens, assets, or UI kits returned by the manifest.
3. Follow the system skill's production or prototype workflow.
4. Reuse package components and semantic tokens. Do not recreate existing components or hard-code equivalent visual values.

If no system is detected, explain that the application must install an `@hamsa-designs/*` design-system package. If multiple systems are detected and the applicable one is not evident from the task or application code, ask which system to use.
