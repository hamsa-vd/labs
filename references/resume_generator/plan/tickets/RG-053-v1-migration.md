# RG-053 — Migrate v1 data into v2

**Epic:** F — Operations · **Depends on:** RG-020, RG-021, RG-037 · **Estimate:** M · **Labels:** ops, data

## Product requirement

**Problem.** v1 has a real history on disk: applications under `companies/<company>/<role>/` with
`JD.txt`, `hamsa_resume.tex`, `cover_letter.tex`, `review.json`, `application_status.json`, and
PDFs — plus a curated `source_of_truth.txt` and ten templates. None of it should be retyped.

**User story.** As the v1 user I run one command and my entire history appears in v2 with its
scores and statuses intact.

**Acceptance criteria**
- Every v1 application directory becomes an application with a run carrying its original scores.
- The source of truth is imported as structured rows, and the rendered output matches the
  original file.
- Migration is idempotent — running it twice does not duplicate anything.
- A dry-run reports exactly what would be created, and changes nothing.

## Technical plan

### Files
```
apps/api/scripts/migrate_v1.py         --source <path> --user-email <e> [--dry-run]
apps/api/scripts/parsers/v1_sot.py     source_of_truth.txt → structured rows
apps/api/tests/test_migrate_v1.py
```

### Steps
1. **Source of truth.** Parse `base/source_of_truth.txt` into companies, projects, bullets, and
   skills. Then verify by rendering it back with `sot_render` (RG-020) and diffing against the
   original. Report the diff and abort if it is not empty — a lossy career-record import is worse
   than no import.
2. **Templates.** Import `single_page/*.tex` and `multi_page/*.tex` as user-owned rows if they
   differ from the seeded system versions; skip if identical by hash.
3. **Applications.** Walk `companies/**`, using `storage.list_saved_applications()`'s own
   discovery rules — including its fallback globs for oddly-named `.tex` files, which encode real
   history. For each: create the application from the directory slugs and `JD.txt`; create a run
   with `status='succeeded'`; map `review.json` field-for-field onto the `runs` columns (the keys
   already match, per RG-002); upload the `.tex` and PDF files as `documents`; apply
   `application_status.json` to the application's status fields.
4. **Idempotency.** Key on `(user_id, company_slug, role_slug, original_dir)`; skip existing. Store
   `original_dir` in a `migrated_from` column added by this ticket's migration.
5. `--dry-run` prints a table of what would be created and touches nothing.
6. Where `review.json` is missing, create the application with no run rather than skipping it —
   the JD and the `.tex` are still worth having.

### Reuse from v1
`storage.list_saved_applications`, `read_application_status`, and `default_application_status` —
port them into the script as the discovery layer. They already handle the messy real-world cases.

### Tests
- Against a fixture tree of five applications: five applications, five runs, correct scores.
- A second run of the migration creates nothing new.
- `--dry-run` writes nothing and reports the right counts.
- The source-of-truth round-trip diff is empty for the real `source_of_truth.txt`.
- A directory missing `review.json` still produces an application.

### Definition of done
Five tests green; the real v1 tree migrates cleanly end to end.

### Out of scope
Migrating LinkedIn notes or the `ats-checker` cache.
