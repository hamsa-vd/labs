# RG-047 — Settings screen

**Epic:** E — Screens · **Depends on:** RG-023, RG-031, RG-012 · **Estimate:** M · **Labels:** web, product

## Product requirement

**User story.** In one place I manage my account, my API keys, the models each stage uses, my
budget ceilings, and my theme.

**Acceptance criteria**
- Adding a key shows only the last four characters afterwards, forever.
- I can test a key before saving it.
- Model choices and budgets are explained in terms of cost and quality, not jargon.
- Theme changes apply immediately and persist across devices.
- Deleting my account is possible, explains what is deleted, and requires typing my email.

## Technical plan

### Files
```
apps/web/src/app/(app)/settings/page.tsx              sections via SidebarNav
apps/web/src/components/settings/AccountSection.tsx
apps/web/src/components/settings/KeysSection.tsx
apps/web/src/components/settings/ModelsSection.tsx
apps/web/src/components/settings/BudgetSection.tsx
apps/web/src/components/settings/AppearanceSection.tsx
apps/web/src/components/settings/DangerZone.tsx
```

### Steps
1. Sections: Account, API keys, Models, Budget, Appearance, Danger zone.
2. **Keys.** A row per provider: label, `••••` + last four in mono, created and last-used dates.
   Add opens a Dialog with a masked Input and a "Test key" Button that must pass before Save
   enables. The secret never re-renders after submission.
3. **Models.** Three Selects — generation, review, revision — each showing the model name and its
   per-million-token price in mono. A one-line note explains v1's split: a strong model reviews,
   a cheaper one revises.
4. **Budget.** Sliders for max revisions (1–5) and the call caps, each with the default marked and
   the server ceiling shown. An estimated worst-case cost per run updates live beneath them — this
   is the control that makes BYOK feel safe.
5. **Appearance.** Light / dark / system as a `SegmentedControl`, applying instantly (RG-012).
6. **Danger zone.** Delete account requires typing the email, per the arey guide's rule that
   permanent deletion is confirmed by typing the name. It states exactly what is removed:
   applications, runs, documents, templates, prompts, keys.

### Reuse from v1
`app.py render_sidebar` for the settings that exist; `llm/catalog.py` for the model list;
`config.py` MAX_* values as the defaults shown.

### Tests
- Save is disabled until the key test passes.
- No API response in the network log contains the submitted secret.
- Changing the theme updates `data-theme` immediately and persists after reload.
- Account deletion requires the exact email and is otherwise disabled.

### Definition of done
Four tests green.

### Out of scope
Billing, notification preferences.
