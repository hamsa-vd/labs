# RG-002 — Supabase schema, migrations, and RLS

**Epic:** A — Foundations · **Depends on:** RG-001 · **Estimate:** L · **Labels:** foundation, data

## Product requirement

**Problem.** v1 stores everything on the local filesystem under `companies/<company>/<role>/`,
keyed by nothing but a path. Two users would overwrite each other. Application status lives in a
loose `application_status.json`.

**Outcome.** Every piece of a user's data — applications, runs, templates, prompts, source of
truth, keys — is a row that belongs to exactly one user and is unreachable by any other.

**Acceptance criteria**
- A signed-in user can only ever read or write rows where `user_id = auth.uid()`, enforced by the
  database itself, not by application code.
- The schema can represent every field v1 persisted in `review.json` and `application_status.json`.
- Migrations run forward on an empty database with no manual steps.

## Technical plan

### Files
```
supabase/config.toml
supabase/migrations/0001_extensions.sql       pgcrypto, uuid-ossp
supabase/migrations/0002_profiles.sql
supabase/migrations/0003_source_of_truth.sql
supabase/migrations/0004_templates.sql
supabase/migrations/0005_prompts.sql
supabase/migrations/0006_applications.sql
supabase/migrations/0007_runs.sql
supabase/migrations/0008_documents.sql
supabase/migrations/0009_api_keys.sql
supabase/migrations/0010_rls.sql              one policy set per table
supabase/seed/                                system-default prompts + templates (RG-021, RG-022)
apps/api/resume_api/db.py                     supabase client factory, per-request user-scoped
```

### Schema

`profiles` — `id uuid pk references auth.users`, `email citext unique`, `full_name`,
`theme text default 'system'`, `default_generation_model`, `default_review_model`,
`default_revision_model`, `max_revisions int default 1`, `resume_pass_score numeric default 8.0`,
`ats_pass_threshold int default 80`, timestamps.

`allowed_emails` — `email citext pk`, `invited_at`, `invited_by`, `redeemed_at`. No RLS; service
role only. Gates sign-in (RG-003).

`sot_companies` — user_id, name, role_title, start_date, end_date, location, sort_order.
`sot_projects` — user_id, company_id fk, name, summary, tech text[].
`sot_bullets` — user_id, company_id fk, project_id fk null, text, metrics text[], tags text[].
`sot_skills` — user_id, name citext, category, proficiency, years numeric,
`evidence_bullet_ids uuid[]`. Unique `(user_id, lower(name))`.

The split matters: the evidence gate (RG-036) needs to point a keyword at a *specific* company
or project **and** a *specific* bullet. v1's flat `source_of_truth.txt` cannot express that.

`templates` — user_id null-for-system, key, name, kind `('single_page','multi_page')`,
tex_source text, storage_path text null, is_system bool, derived_from uuid null, timestamps.

`prompts` — user_id null-for-system, stage enum
`('targeting','generation','review','revision','ats','cover_letter')`, body text, version int,
is_active bool. Unique `(user_id, stage, version)`. System rows have `user_id is null`.

`applications` — user_id, company_name, company_slug, job_title, role_slug, jd_text,
jd_source_type `('text','url','upload')`, jd_url, source `('generated','imported')`,
status `('draft','applied','screening','interviewing','offer','rejected','withdrawn')`,
round_count int, current_round, next_action, notes, applied_at, timestamps.
Index `(user_id, updated_at desc)`; unique `(user_id, company_slug, role_slug, created_at)`.

`runs` — application_id fk, user_id, status
`('queued','running','succeeded','failed','cancelled')`, template_id fk, recommended_template_key,
template_reason, targeting_brief jsonb, resume_review jsonb, resume_score numeric,
fix_resolution_matrix jsonb, revision_count int, ats jsonb, warnings text[], compile_errors jsonb,
token_usage jsonb, cost_usd numeric, error text, started_at, finished_at.
The `ats` jsonb mirrors v1's keys exactly: `total_score, grade, keyword_score, structural_score,
semantic_score, matched, missing_required, missing_preferred, top_actions, hard_requirements,
all_hard_met, error`.

`run_events` — run_id fk, seq int, node text, status, payload jsonb, created_at.
Unique `(run_id, seq)`. This is the SSE replay log (RG-032).

`documents` — user_id, application_id, run_id null, kind
`('resume_tex','resume_pdf','cover_letter_tex','cover_letter_pdf','jd','imported_resume')`,
storage_path, byte_size, content_hash, created_at.

`api_keys` — user_id, provider `('anthropic','openai','openrouter')`, ciphertext bytea,
last_four text, label, created_at, last_used_at. Unique `(user_id, provider, label)`.

### RLS
Enable on every table above except `allowed_emails`. Standard policy per table:
`using (user_id = auth.uid())` for select/update/delete, `with check (user_id = auth.uid())` for
insert. `templates` and `prompts` additionally allow `select` where `user_id is null` (system rows).

### Steps
1. `supabase init`; write migrations in the order above, each idempotent and forward-only.
2. Write every table with `created_at timestamptz default now()` and a `set_updated_at` trigger.
3. Add a `handle_new_user` trigger on `auth.users` that inserts a `profiles` row and clones the
   system prompt + template rows for the new user (RG-021/022 supply the content).
4. Generate types: `supabase gen types typescript` → `packages/contracts/src/database.types.ts`.

### Reuse from v1
`slugify()` from `resume_agent/storage.py` → `apps/api/resume_api/util/slug.py`, unchanged. It
produces `company_slug`/`role_slug`. `default_application_status()` defines the status field set.

### Tests
- `supabase/tests/rls.test.sql` (pgTAP): user A cannot select, update, or delete any of user B's
  rows in every RLS-enabled table. This test is the ticket.
- Migration replay on an empty DB in CI.

### Definition of done
Migrations apply cleanly; pgTAP RLS suite green; generated TS types committed.

### Out of scope
Seed content (RG-021, RG-022), any API route.
