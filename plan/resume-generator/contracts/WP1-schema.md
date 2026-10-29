# WP1 — Schema and ascend domain extension

Discharges RG-002 and RG-006 as adapted by ADR-100: ascend's Postgres and Cloudflare Access
replace Supabase Auth, RLS, and Storage.

Two roots:
- SQL: `apps/ascend/supabase/migrations/0006_resume_generator.sql`
- TypeScript: `apps/ascend/src/domain/`

A dev database is already running: `postgres://ascend:ascend@127.0.0.1:55432/ascend`, with
ascend's migrations 0001–0005 applied. `make db-migrate` from the repo root re-applies all of
them in order; `make reset` rebuilds from empty.

---

## Part A — the migration

One file, `0006_resume_generator.sql`. Forward-only, idempotent where cheaply possible, and it
must apply cleanly on top of 0005 on an empty database. Every table gets
`created_at timestamptz not null default now()`.

### A1. Extending `applications`

Ascend's `applications` table is the single application entity for both the tracker and the
resume generator. There is no second applications table — two would be exactly the scattering
this work exists to remove.

Alter it to:
- widen the `current_status` check to include `'draft'`, keeping the eight existing values;
- widen the `origin` check from `('gmail','manual')` to `('gmail','manual','generated','imported')`;
- add these columns, all nullable unless stated:

| Column | Type | Notes |
| --- | --- | --- |
| `company_slug` | text | from `slugify(company_display)`; storage paths and migration keying |
| `role_slug` | text | from `slugify(role_title)` |
| `jd_text` | text | the job description the run was built from |
| `jd_source_type` | text | check in `('text','url','upload')` |
| `jd_url` | text | |
| `round_count` | int not null default 0 | v1 `application_status.json` |
| `current_round` | text | v1 `application_status.json` |
| `next_action` | text | v1 `application_status.json` |
| `applied_at` | timestamptz | |
| `derived_from` | uuid references applications(id) on delete set null | convert-to-generated |
| `migrated_from` | text | the v1 directory this row came from (RG-053) |
| `updated_at` | timestamptz not null default now() | |

Indexes: `(user_id, updated_at desc)`; a unique index on `(user_id, migrated_from)` where
`migrated_from is not null`, which is what makes the v1 migration idempotent.

**Why `'draft'` is safe.** `refresh_application_projection` updates `current_status` only when it
projects a non-null status from `application_events`, and `'draft'` is not in
`applicationEventTypes`, so no classifier and no projection can ever emit it. A draft is the state
of an application that has a generated resume and has not been sent. Confirm this rather than
assume it: a test must show that calling `refresh_application_projection` on a draft application
with no status events leaves it `'draft'`.

### A2. Source of truth (RG-020)

The split into four tables is what lets the evidence gate point a keyword at a *specific* company
or project **and** a *specific* bullet. v1's flat text file cannot express that.

- `sot_companies` — `id uuid pk default gen_random_uuid()`, `user_id` → `app_users(id)` on delete
  cascade, `name text not null`, `role_title text`, `start_date text`, `end_date text`,
  `location text`, `sort_order int not null default 0`, `updated_at`.
  Dates are `text`, not `date`: v1's record holds values like `"Jul 2022"` and `"Present"`.
- `sot_projects` — `user_id`, `company_id` → `sot_companies(id)` on delete cascade, `name not null`,
  `summary text`, `tech text[] not null default '{}'`, `sort_order`, `updated_at`.
- `sot_bullets` — `user_id`, `company_id` → `sot_companies(id)` on delete cascade,
  `project_id` → `sot_projects(id)` on delete cascade **nullable**, `text text not null`,
  `metrics text[] not null default '{}'`, `tags text[] not null default '{}'`, `sort_order`,
  `updated_at`. A bullet belongs to a company always and to a project optionally.
- `sot_skills` — `user_id`, `name text not null`, `category text`, `proficiency text`,
  `years numeric`, `evidence_bullet_ids uuid[] not null default '{}'`, `sort_order`, `updated_at`.
  Unique on `(user_id, lower(name))`.

Indexes on every `user_id` and every foreign key.

### A3. Templates (RG-021)

`resume_templates` — `id`, `user_id` **nullable** (null means a system template),
`key text not null`, `name text not null`, `kind text not null check (kind in
('single_page','multi_page'))`, `tex_source text not null`, `is_system bool not null default
false`, `derived_from uuid references resume_templates(id) on delete set null`, `updated_at`.

Unique: `(user_id, key, kind)` for user rows, and `(key, kind)` where `user_id is null` for system
rows. A user may override a system key with their own row for the same key; resolution prefers the
user's row.

Seed the ten v1 templates as system rows in this migration. The `.tex` bodies live at
`apps/resume-pipeline/seed/templates/{single_page,multi_page}__<key>.tex` with keys
`frontend`, `backend-java`, `backend-python`, `fullstack`, `senior-engineer`. Read them and inline
them into the migration as quoted literals — a migration must not depend on a file path at apply
time. Dollar-quote the bodies (`$tex$…$tex$`) because LaTeX is full of backslashes and quotes.

### A4. Prompts (RG-022)

`resume_prompts` — `id`, `user_id` nullable (null = system default), `stage text not null check
(stage in ('targeting','generation','review','revision','ats','cover_letter'))`, `body text not
null`, `version int not null default 1`, `is_active bool not null default true`, `updated_at`.
Unique `(user_id, stage, version)`. A partial unique index enforces at most one active version per
`(user_id, stage)`.

Seed the five v1 prompts as system rows, `user_id = null`, `version = 1`, `is_active = true`,
inlined from `apps/resume-pipeline/seed/prompts/`: `targeting_brief.md`→`targeting`,
`generator.md`→`generation`, `reviewer.md`→`review`, `reviser.md`→`revision`,
`cover_letter.md`→`cover_letter`. Do not reword them. The `ats` stage has no v1 equivalent and is
seeded with a short body using only `{{JD_TEXT}}` and `{{ATS_FINDINGS}}`.

### A5. Runs (RG-032)

`resume_runs` — `id`, `user_id`, `application_id` → `applications(id)` on delete cascade,
`status text not null check (status in ('queued','running','succeeded','failed','cancelled'))
default 'queued'`, `kind text not null check (kind in ('generate','import','apply_keywords'))
default 'generate'`, `template_id uuid references resume_templates(id) on delete set null`,
`recommended_template_key text`, `template_reason text`, `targeting_brief jsonb`,
`resume_review jsonb`, `resume_score numeric`, `cover_letter_score numeric`,
`fix_resolution_matrix jsonb not null default '[]'::jsonb`, `revision_count int not null default 0`,
`ats jsonb`, `warnings text[] not null default '{}'`, `compile_errors jsonb not null default
'{}'::jsonb`, `token_usage jsonb not null default '{}'::jsonb`, `cost_usd numeric not null
default 0`, `budget jsonb not null default '{}'::jsonb`, `error text`, `started_at`, `finished_at`,
`created_at`, `updated_at`.

The `ats` jsonb mirrors v1's key names exactly, unprefixed inside the object:
`total_score, grade, keyword_score, structural_score, semantic_score, matched, missing_required,
missing_preferred, missing_nice_to_have, top_actions, hard_requirements, all_hard_met, error`.

`resume_run_events` — `id`, `run_id` → `resume_runs(id)` on delete cascade, `seq int not null`,
`node text not null`, `status text not null`, `label text not null`, `payload jsonb not null
default '{}'::jsonb`, `created_at`. Unique `(run_id, seq)`. This is the SSE replay log, so the
uniqueness is load-bearing: it is what makes reconnect-at-seq exact.

Add a `notify` trigger on insert into `resume_run_events` that issues
`pg_notify('resume_run_events', run_id::text)`. The SSE tail listens on that channel.

### A6. Documents (RG-006)

`resume_documents` — `id`, `user_id`, `application_id` → `applications(id)` on delete cascade,
`run_id` → `resume_runs(id)` on delete set null **nullable**, `kind text not null check (kind in
('resume_tex','resume_pdf','cover_letter_tex','cover_letter_pdf','jd','imported_resume',
'template_preview'))`, `storage_path text not null`, `byte_size bigint not null`,
`content_hash text not null`, `content_type text not null`, `created_at`.
Unique `(storage_path)`. Index `(user_id, application_id, kind)`.

The row is the index; the bytes live under `RESUME_DOCUMENTS_DIR`. Nothing ever lists the
directory to find a file.

### A7. Keys (RG-023)

`resume_api_keys` — `id`, `user_id`, `provider text not null check (provider in
('anthropic','openai','openrouter'))`, `ciphertext bytea not null`, `last_four text not null`,
`label text not null default 'default'`, `created_at`, `last_used_at`.
Unique `(user_id, provider, label)`.

There is no plaintext column and no column that could hold one. `apps/ascend`'s existing
`pnpm audit:persistence` script fails the build if a plaintext token column appears; read
`apps/ascend/scripts/audit-persistence.ts` and extend its column denylist to cover this table.

### A8. Evidence decisions (RG-036)

`resume_keyword_decisions` — `id`, `user_id`, `application_id` → `applications(id)` on delete
cascade, `run_id` → `resume_runs(id)` on delete set null, `keyword text not null`,
`decision text not null check (decision in ('accepted','dismissed','deferred'))`,
`sot_company_id uuid references sot_companies(id) on delete set null`,
`sot_project_id uuid references sot_projects(id) on delete set null`,
`sot_bullet_id uuid references sot_bullets(id) on delete set null`,
`created_bullet bool not null default false`, `note text`, `created_at`.
Unique `(application_id, lower(keyword))`.

### A9. Cost accounting (RG-050)

`resume_llm_calls` — `id`, `user_id`, `run_id` → `resume_runs(id)` on delete cascade,
`node text not null`, `provider text not null`, `model text not null`, `input_tokens int not null
default 0`, `output_tokens int not null default 0`, `cost_usd numeric not null default 0`,
`latency_ms int`, `created_at`. Index `(user_id, created_at desc)`.

No column here may hold prompt or completion text. Only counts.

### A10. `set_updated_at`

Every table with an `updated_at` column gets a `before update` trigger setting it to `now()`.
Write one shared trigger function and attach it; do not repeat the body per table. Check whether
ascend's earlier migrations already define such a function before creating another.

---

## Part B — ascend domain types

`applications.current_status` can now hold `'draft'`, which the TypeScript types do not admit.
Close that gap without weakening the projection's closed enum.

In `apps/ascend/src/domain/application-event.ts`:
- leave `applicationEventTypes`, `applicationStatuses`, `terminalStatuses`, `isApplicationStatus`,
  `isTerminalStatus` and `projectStatus`'s contract **exactly as they are**. A classifier must
  still be unable to emit `'draft'`; that is the point of the closed enum.
- add `applicationRecordStatuses = ['draft', ...applicationStatuses]` and the derived type
  `ApplicationRecordStatus`. This is the type of the *column*, which is a superset of the type of
  a *projection*.

In `apps/ascend/src/domain/application.ts`:
- `Application.currentStatus` becomes `ApplicationRecordStatus`.
- `applicationOrigins` gains `'generated'` and `'imported'`.
- `applicationStages` gains `'draft'` as its first element, and `applicationStage('draft')`
  returns `'draft'`. A draft is a real column on the board — it is where a generated resume waits
  before it is sent.

Anything that fails to typecheck as a result is in scope to fix, but fix it by widening the type,
never by casting. `pnpm --filter @labs/ascend typecheck` must be green.

---

## Acceptance criteria

1. `make reset` applies 0001–0006 to an empty database with no manual step and no error.
2. Applying 0006 twice in a row does not error (guard with `if not exists` / `on conflict`).
3. Ten system templates and six system prompts exist after migration, with correct keys and stages.
4. Every seeded template body starts with `\documentclass` and contains `\begin{document}`.
5. Deleting an `app_users` row removes every resume row belonging to that user, across all eleven
   new tables, with no orphan and no foreign-key error.
6. Deleting a `sot_companies` row removes its projects and its bullets.
7. Two users' rows are independent: a query filtered by `user_id` never returns the other's rows,
   for every new table. This suite stands in for RG-002's pgTAP RLS suite.
8. `refresh_application_projection` on a draft application with no status events leaves it
   `'draft'`; with an `'applied'` event it becomes `'applied'`.
9. Inserting a `resume_run_events` row emits a `pg_notify` on channel `resume_run_events`.
10. `resume_run_events` rejects a duplicate `(run_id, seq)`.
11. `resume_api_keys` has no column capable of holding a plaintext secret, and
    `pnpm --filter @labs/ascend audit:persistence` passes.
12. `pnpm --filter @labs/ascend typecheck` and `pnpm --filter @labs/ascend test` are green.

## Test paths (test agent writes only here)

```
apps/ascend/src/infrastructure/resume-schema.integration.test.ts
apps/ascend/src/domain/application-record-status.test.ts
```

The integration test follows the existing convention in
`apps/ascend/src/infrastructure/database.integration.test.ts`: it reads `TEST_DATABASE_URL` and
skips cleanly when it is absent, so the default suite stays offline. Read that file for the
pattern before writing. It will be run with
`TEST_DATABASE_URL=postgres://ascend:ascend@127.0.0.1:55432/ascend`.

## Source paths (implementing agent writes only here)

```
apps/ascend/supabase/migrations/0006_resume_generator.sql
apps/ascend/src/domain/application-event.ts     (additive only)
apps/ascend/src/domain/application.ts
apps/ascend/scripts/audit-persistence.ts        (denylist extension only)
```
Plus the minimum edits elsewhere in `apps/ascend/src` and `apps/ascend/app` needed to keep
`typecheck` green after the type widening.
