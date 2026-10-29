# RG-045 — Source of truth and prompts screen

**Epic:** E — Screens · **Depends on:** RG-020, RG-022 · **Estimate:** L · **Labels:** web, product

## Product requirement

**Problem.** These are the two things that determine output quality, and in v1 both are files on
disk that a user cannot reach.

**User story.** I curate my career record and, separately, tune the instructions the system uses
at each stage — and I can always get back to the defaults.

**Acceptance criteria**
- I can manage companies, projects, bullets, and skills with inline editing and drag reorder.
- I can see exactly the text that gets injected into prompts.
- I can edit all six prompts, see version history, restore a version, and reset to default.
- A prompt missing a required variable cannot be saved, and the error names the variable.
- Nothing is lost on an accidental navigation.

## Technical plan

### Files
```
apps/web/src/app/(app)/source-of-truth/page.tsx        Tabs: Career record | Prompts
apps/web/src/components/sot/CompanyList.tsx            accordion, dnd-kit reorder
apps/web/src/components/sot/BulletEditor.tsx           inline textarea, autosave
apps/web/src/components/sot/SkillGrid.tsx              category groups, evidence links
apps/web/src/components/sot/RenderedPreview.tsx        read-only, mono, the injected text
apps/web/src/components/prompts/PromptEditor.tsx       CodeMirror, variable chips
apps/web/src/components/prompts/VersionHistory.tsx
```

### Steps
1. **Career record tab.** Companies as an accordion; each holds projects, each holds bullets.
   `dnd-kit` for reorder, committing to `POST /source-of-truth/reorder` on drop. Bullet edits
   autosave on blur with a quiet "Saved" — no save button, no dialog.
2. A skill row shows the bullets that evidence it as small links. A skill with no evidence shows
   a quiet warning glyph — this is the same standard the ATS gate enforces, applied to the record
   itself, so the two features feel like one idea.
3. `RenderedPreview` is a collapsed panel showing `GET /source-of-truth/rendered` verbatim in
   `--font-mono`. Making the prompt input visible is what lets a user debug bad output themselves.
4. **Prompts tab.** Six stages down the left as a `SidebarNav`; the editor on the right. Above the
   editor, the required variables render as `Kbd`-style chips — clicking one inserts it at the
   cursor. A chip is muted when that variable is absent from the body, so a missing one is visible
   before saving, not only on the validation error.
5. A customised prompt shows a "Modified" Badge in the stage list and a "Reset to default" action.
   `VersionHistory` is a popover listing versions with timestamps (mono) and a restore action.
6. `beforeunload` guard on unsaved prompt edits. The career record does not need one — it autosaves.

### Reuse from v1
`base/source_of_truth.txt` for the record's shape and the rendered format;
`resume_agent/prompts/*.md` as the default bodies shown when a user resets.

### Tests
- Reordering bullets persists across a reload.
- The rendered preview matches `GET /rendered` exactly.
- Saving a prompt without `{{JD_TEXT}}` shows the named error and does not save.
- Restoring a version replaces the editor body.
- Reset restores the system default and clears the "Modified" badge.

### Definition of done
Five tests green.

### Out of scope
Importing a career record from LinkedIn or a PDF.
