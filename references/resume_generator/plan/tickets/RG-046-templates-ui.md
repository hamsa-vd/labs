# RG-046 — Templates screen

**Epic:** E — Screens · **Depends on:** RG-021, RG-035 · **Estimate:** M · **Labels:** web, product

## Product requirement

**User story.** I keep a small library of LaTeX resume templates, see what each one looks like,
and add my own by uploading, pasting, or copying an existing one.

**Acceptance criteria**
- Every template shows a rendered preview, not just a filename.
- I can add one three ways, and validation problems are explained before I save.
- I can duplicate any template, including the system ones, and edit my copy.
- I cannot delete a system template, and deleting one that is in use explains why.

## Technical plan

### Files
```
apps/web/src/app/(app)/templates/page.tsx
apps/web/src/components/templates/TemplateGrid.tsx
apps/web/src/components/templates/TemplateCard.tsx      preview thumbnail + actions
apps/web/src/components/templates/AddTemplateDialog.tsx tabs: upload | paste | duplicate
apps/web/src/components/templates/TemplatePreview.tsx   first-page render
```

### Steps
1. Grid of Cards. Each: preview thumbnail, name, kind Badge ("Single page" / "Multi page"), a
   "System" Badge where applicable, and a menu with duplicate, edit, delete.
2. Previews are generated once per template by compiling it with placeholder content (RG-035) and
   caching the first page as a PNG in Storage. Compile-on-view would be far too slow for a grid.
3. `AddTemplateDialog`: upload validates client-side for `.tex` and 200 KB, then server-side
   (RG-021); paste uses CodeMirror; duplicate is a Select over the library plus a name field.
4. Validation errors list every problem at once, in arey voice: "Line 40 uses \\write18. Remove it
   and save again."
5. Deleting a template in use surfaces the 409 as "Used by 3 applications. Duplicate it instead."

### Reuse from v1
`single_page/*.tex` and `multi_page/*.tex` are the seeded library; `config.py TEMPLATE_FILES`
gives the naming.

### Tests
- The grid shows ten seeded templates with previews.
- Uploading an invalid `.tex` lists every validation problem.
- Duplicating a system template creates an editable user copy.
- Deleting an in-use template shows the conflict message.

### Definition of done
Four tests green.

### Out of scope
A visual template designer.
