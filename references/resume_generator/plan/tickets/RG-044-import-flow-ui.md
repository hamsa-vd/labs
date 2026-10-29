# RG-044 — Import flow UI

**Epic:** E — Screens · **Depends on:** RG-037, RG-040 · **Estimate:** M · **Labels:** web, product

## Product requirement

**User story.** I have already applied to twelve jobs with a resume I wrote myself. I want those
in the tracker, scored, so I know which ones were weak and what to fix next time.

**Acceptance criteria**
- Import by drag-and-drop file, file picker, or paste.
- I supply the company, role, and job description alongside the resume.
- I see the same two scores as a generated application.
- A scanned PDF tells me plainly to paste the text instead.
- Importing is reachable from the pipeline empty state and from the sidebar.

## Technical plan

### Files
```
apps/web/src/app/(app)/applications/import/page.tsx
apps/web/src/components/import/ResumeDropzone.tsx     .tex, .pdf, ≤5 MB
apps/web/src/components/import/ImportForm.tsx
```

### Steps
1. Dropzone accepts `.tex` and `.pdf`; a third tab accepts pasted text. On file selection show
   the filename, size (mono), and the extracted character count as a confidence signal.
2. Same company / role / JD fields as RG-041, sharing the components — not a second copy.
3. Submit posts multipart to `POST /v1/applications/import` and routes to the run view, which
   shows only the two scoring stages (RG-042 handles this without change).
4. `unreadable_pdf` renders inline on the dropzone with the paste tab pre-selected — recover the
   user in place rather than sending them back to the start.
5. On the result view, an imported application shows an "Imported" Badge next to the title and a
   "Generate a tailored version" Button calling `convert-to-generated`.

### Tests
- Drag-and-drop a `.tex` → import succeeds and lands on the run view.
- An oversized file is rejected client-side with a clear message.
- `unreadable_pdf` switches to the paste tab with the error shown.
- The imported badge and the convert action render on the result view.

### Definition of done
Four tests green.

### Out of scope
Bulk import.
