import { randomUUID } from 'node:crypto';
import { Client, Pool, type Notification } from 'pg';
import { afterAll, afterEach, beforeAll, describe, expect, it } from 'vitest';

/**
 * WP1 acceptance suite for migration 0006_resume_generator.sql.
 *
 * Follows the opt-in convention of database.integration.test.ts: it reads
 * TEST_DATABASE_URL and skips cleanly when it is absent, so the default suite
 * stays offline.
 *
 * This file stands in for RG-002's pgTAP RLS suite (ADR-100 replaced Supabase
 * RLS with Cloudflare Access plus server-side scoping), so the ownership
 * checks are exhaustive rather than representative: every new table that
 * carries a user_id is asserted individually.
 *
 * Tests write committed rows rather than rolling back, because the pg_notify
 * assertion needs a real commit. Every fixture hangs off an app_users row with
 * a per-run random email, and afterEach deletes those rows, so a crashed run
 * cannot poison the next one.
 */

const connectionString = process.env.TEST_DATABASE_URL;
const suite = describe.skipIf(!connectionString);

let pool: Pool;

/** app_users ids created by the current test; deleted in afterEach. */
const createdUserIds: string[] = [];

const CHECK_VIOLATION = '23514';
const UNIQUE_VIOLATION = '23505';

/** Postgres error codes that mean "the migration has not been applied". */
const MISSING_SCHEMA = new Set(['42P01', '42703']);

async function expectViolation(code: string, run: () => Promise<unknown>): Promise<void> {
  let error: (Error & { code?: string }) | undefined;
  try {
    await run();
  } catch (caught) {
    error = caught as Error & { code?: string };
  }
  expect(error, 'expected the database to reject this statement, but it succeeded').toBeDefined();
  expect(
    MISSING_SCHEMA.has(error?.code ?? ''),
    `statement failed because the schema is missing, not because of the constraint: ${error?.message}`,
  ).toBe(false);
  expect(error?.code, `wrong rejection reason: ${error?.message}`).toBe(code);
}

async function createUser(): Promise<string> {
  const email = `resume-schema-${randomUUID()}@example.com`;
  const result = await pool.query<{ id: string }>(
    `insert into app_users(email) values ($1) returning id::text as id`,
    [email],
  );
  const id = result.rows[0]!.id;
  createdUserIds.push(id);
  return id;
}

async function createApplication(
  userId: string,
  overrides: { currentStatus?: string; origin?: string; migratedFrom?: string | null } = {},
): Promise<string> {
  const result = await pool.query<{ id: string }>(
    `insert into applications
       (user_id, company_norm, company_display, role_title, role_norm, source,
        first_seen_at, current_status, status_as_of, origin)
     values ($1, 'acme corp', 'Acme Corp', 'Staff Engineer', 'staff engineer', 'greenhouse',
             now(), $2, now(), $3)
     returning id::text as id`,
    [userId, overrides.currentStatus ?? 'applied', overrides.origin ?? 'manual'],
  );
  return result.rows[0]!.id;
}

/** One row in every new user-scoped table, plus the run-scoped event row. */
interface ResumeGraph {
  applicationId: string;
  runId: string;
  eventId: string;
  rowIds: Record<string, string>;
}

/** The eleven new tables that carry a user_id, per acceptance criteria 5 and 7. */
const userScopedTables = [
  'sot_companies',
  'sot_projects',
  'sot_bullets',
  'sot_skills',
  'resume_templates',
  'resume_prompts',
  'resume_runs',
  'resume_documents',
  'resume_api_keys',
  'resume_keyword_decisions',
  'resume_llm_calls',
] as const;

async function insertReturningId(sql: string, params: unknown[]): Promise<string> {
  const result = await pool.query<{ id: string }>(sql, params);
  return result.rows[0]!.id;
}

async function seedResumeGraph(userId: string): Promise<ResumeGraph> {
  const unique = randomUUID();
  const applicationId = await createApplication(userId);

  const companyId = await insertReturningId(
    `insert into sot_companies(user_id, name, role_title, start_date, end_date, location, sort_order)
     values ($1, 'Acme Corp', 'Staff Engineer', 'Jul 2022', 'Present', 'London', 0)
     returning id::text as id`,
    [userId],
  );
  const projectId = await insertReturningId(
    `insert into sot_projects(user_id, company_id, name, summary, tech, sort_order)
     values ($1, $2, 'Billing rewrite', 'Rebuilt the ledger', array['go','postgres'], 0)
     returning id::text as id`,
    [userId, companyId],
  );
  const bulletId = await insertReturningId(
    `insert into sot_bullets(user_id, company_id, project_id, text, metrics, tags, sort_order)
     values ($1, $2, $3, 'Cut ledger reconciliation time by 40 percent',
             array['40 percent'], array['postgres'], 0)
     returning id::text as id`,
    [userId, companyId, projectId],
  );
  const skillId = await insertReturningId(
    `insert into sot_skills(user_id, name, category, proficiency, years, evidence_bullet_ids, sort_order)
     values ($1, $2, 'backend', 'expert', 6, array[$3::uuid], 0)
     returning id::text as id`,
    [userId, `Postgres ${unique}`, bulletId],
  );
  const templateId = await insertReturningId(
    `insert into resume_templates(user_id, key, name, kind, tex_source)
     values ($1, 'frontend', 'My frontend override', 'single_page',
             '\\documentclass{article}\\begin{document}\\end{document}')
     returning id::text as id`,
    [userId],
  );
  const promptId = await insertReturningId(
    `insert into resume_prompts(user_id, stage, body)
     values ($1, 'generation', 'My generation prompt')
     returning id::text as id`,
    [userId],
  );
  const runId = await insertReturningId(
    `insert into resume_runs(user_id, application_id) values ($1, $2) returning id::text as id`,
    [userId, applicationId],
  );
  const eventId = await insertReturningId(
    `insert into resume_run_events(run_id, seq, node, status, label)
     values ($1, 1, 'targeting', 'started', 'Building the targeting brief')
     returning id::text as id`,
    [runId],
  );
  const documentId = await insertReturningId(
    `insert into resume_documents
       (user_id, application_id, run_id, kind, storage_path, byte_size, content_hash, content_type)
     values ($1, $2, $3, 'resume_pdf', $4, 1024, $5, 'application/pdf')
     returning id::text as id`,
    [userId, applicationId, runId, `resumes/${unique}/resume.pdf`, `sha256-${unique}`],
  );
  const apiKeyId = await insertReturningId(
    `insert into resume_api_keys(user_id, provider, ciphertext, last_four)
     values ($1, 'anthropic', $2, '1234')
     returning id::text as id`,
    [userId, Buffer.from('ciphertext')],
  );
  const decisionId = await insertReturningId(
    `insert into resume_keyword_decisions(user_id, application_id, run_id, keyword, decision)
     values ($1, $2, $3, 'kubernetes', 'accepted')
     returning id::text as id`,
    [userId, applicationId, runId],
  );
  const llmCallId = await insertReturningId(
    `insert into resume_llm_calls(user_id, run_id, node, provider, model, input_tokens, output_tokens)
     values ($1, $2, 'generation', 'anthropic', 'claude-sonnet', 1200, 800)
     returning id::text as id`,
    [userId, runId],
  );

  return {
    applicationId,
    runId,
    eventId,
    rowIds: {
      sot_companies: companyId,
      sot_projects: projectId,
      sot_bullets: bulletId,
      sot_skills: skillId,
      resume_templates: templateId,
      resume_prompts: promptId,
      resume_runs: runId,
      resume_documents: documentId,
      resume_api_keys: apiKeyId,
      resume_keyword_decisions: decisionId,
      resume_llm_calls: llmCallId,
    },
  };
}

interface ColumnRow {
  column_name: string;
  data_type: string;
  not_null: boolean;
}

async function describeTable(table: string): Promise<Map<string, ColumnRow>> {
  const result = await pool.query<ColumnRow>(
    `select a.attname as column_name,
            format_type(a.atttypid, a.atttypmod) as data_type,
            a.attnotnull as not_null
       from pg_attribute a
       join pg_class c on c.oid = a.attrelid
       join pg_namespace n on n.oid = c.relnamespace
      where n.nspname = 'public'
        and c.relkind = 'r'
        and c.relname = $1
        and a.attnum > 0
        and not a.attisdropped`,
    [table],
  );
  return new Map(result.rows.map((row) => [row.column_name, row]));
}

/**
 * Column spec: `"<type>"` means not null, `"<type>?"` means nullable.
 * Types are `format_type` spellings, so they are unambiguous about arrays.
 * A `numeric` spec matches any precision/scale the implementer picks.
 */
type TableSpec = Record<string, string>;

const newColumnsOnApplications: TableSpec = {
  company_slug: 'text?',
  role_slug: 'text?',
  jd_text: 'text?',
  jd_source_type: 'text?',
  jd_url: 'text?',
  round_count: 'integer',
  current_round: 'text?',
  next_action: 'text?',
  applied_at: 'timestamp with time zone?',
  derived_from: 'uuid?',
  migrated_from: 'text?',
  updated_at: 'timestamp with time zone',
};

const newTableSpecs: Record<string, TableSpec> = {
  sot_companies: {
    id: 'uuid',
    user_id: 'uuid',
    name: 'text',
    role_title: 'text?',
    start_date: 'text?',
    end_date: 'text?',
    location: 'text?',
    sort_order: 'integer',
    updated_at: 'timestamp with time zone',
    created_at: 'timestamp with time zone',
  },
  sot_projects: {
    id: 'uuid',
    user_id: 'uuid',
    company_id: 'uuid',
    name: 'text',
    summary: 'text?',
    tech: 'text[]',
    sort_order: 'integer',
    updated_at: 'timestamp with time zone',
    created_at: 'timestamp with time zone',
  },
  sot_bullets: {
    id: 'uuid',
    user_id: 'uuid',
    company_id: 'uuid',
    project_id: 'uuid?',
    text: 'text',
    metrics: 'text[]',
    tags: 'text[]',
    sort_order: 'integer',
    updated_at: 'timestamp with time zone',
    created_at: 'timestamp with time zone',
  },
  sot_skills: {
    id: 'uuid',
    user_id: 'uuid',
    name: 'text',
    category: 'text?',
    proficiency: 'text?',
    years: 'numeric?',
    evidence_bullet_ids: 'uuid[]',
    sort_order: 'integer',
    updated_at: 'timestamp with time zone',
    created_at: 'timestamp with time zone',
  },
  resume_templates: {
    id: 'uuid',
    user_id: 'uuid?',
    key: 'text',
    name: 'text',
    kind: 'text',
    tex_source: 'text',
    is_system: 'boolean',
    derived_from: 'uuid?',
    updated_at: 'timestamp with time zone',
    created_at: 'timestamp with time zone',
  },
  resume_prompts: {
    id: 'uuid',
    user_id: 'uuid?',
    stage: 'text',
    body: 'text',
    version: 'integer',
    is_active: 'boolean',
    updated_at: 'timestamp with time zone',
    created_at: 'timestamp with time zone',
  },
  resume_runs: {
    id: 'uuid',
    user_id: 'uuid',
    application_id: 'uuid',
    status: 'text',
    kind: 'text',
    template_id: 'uuid?',
    recommended_template_key: 'text?',
    template_reason: 'text?',
    targeting_brief: 'jsonb?',
    resume_review: 'jsonb?',
    resume_score: 'numeric?',
    cover_letter_score: 'numeric?',
    fix_resolution_matrix: 'jsonb',
    revision_count: 'integer',
    ats: 'jsonb?',
    warnings: 'text[]',
    compile_errors: 'jsonb',
    token_usage: 'jsonb',
    cost_usd: 'numeric',
    budget: 'jsonb',
    error: 'text?',
    started_at: 'timestamp with time zone?',
    finished_at: 'timestamp with time zone?',
    created_at: 'timestamp with time zone',
    updated_at: 'timestamp with time zone',
  },
  resume_run_events: {
    id: 'uuid',
    run_id: 'uuid',
    seq: 'integer',
    node: 'text',
    status: 'text',
    label: 'text',
    payload: 'jsonb',
    created_at: 'timestamp with time zone',
  },
  resume_documents: {
    id: 'uuid',
    user_id: 'uuid',
    application_id: 'uuid',
    run_id: 'uuid?',
    kind: 'text',
    storage_path: 'text',
    byte_size: 'bigint',
    content_hash: 'text',
    content_type: 'text',
    created_at: 'timestamp with time zone',
  },
  resume_api_keys: {
    id: 'uuid',
    user_id: 'uuid',
    provider: 'text',
    ciphertext: 'bytea',
    last_four: 'text',
    label: 'text',
    created_at: 'timestamp with time zone',
    last_used_at: 'timestamp with time zone?',
  },
  resume_keyword_decisions: {
    id: 'uuid',
    user_id: 'uuid',
    application_id: 'uuid',
    run_id: 'uuid?',
    keyword: 'text',
    decision: 'text',
    sot_company_id: 'uuid?',
    sot_project_id: 'uuid?',
    sot_bullet_id: 'uuid?',
    created_bullet: 'boolean',
    note: 'text?',
    created_at: 'timestamp with time zone',
  },
  resume_llm_calls: {
    id: 'uuid',
    user_id: 'uuid',
    run_id: 'uuid',
    node: 'text',
    provider: 'text',
    model: 'text',
    input_tokens: 'integer',
    output_tokens: 'integer',
    cost_usd: 'numeric',
    latency_ms: 'integer?',
    created_at: 'timestamp with time zone',
  },
};

function assertColumns(table: string, spec: TableSpec, actual: Map<string, ColumnRow>): void {
  for (const [column, declaration] of Object.entries(spec)) {
    const nullable = declaration.endsWith('?');
    const expectedType = nullable ? declaration.slice(0, -1) : declaration;
    const found = actual.get(column);
    expect(found, `${table}.${column} is missing`).toBeDefined();
    if (!found) continue;
    if (expectedType === 'numeric') {
      expect(found.data_type, `${table}.${column} type`).toMatch(/^numeric/);
    } else {
      expect(found.data_type, `${table}.${column} type`).toBe(expectedType);
    }
    expect(found.not_null, `${table}.${column} nullability`).toBe(!nullable);
  }
}

const systemTemplateKeys = ['frontend', 'backend-java', 'backend-python', 'fullstack', 'senior-engineer'];
const systemTemplateKinds = ['single_page', 'multi_page'];
const systemPromptStages = ['targeting', 'generation', 'review', 'revision', 'ats', 'cover_letter'];

suite('resume generator schema (migration 0006)', () => {
  beforeAll(() => {
    pool = new Pool({ connectionString, max: 4 });
  });

  afterEach(async () => {
    const ids = createdUserIds.splice(0);
    if (ids.length > 0) {
      await pool.query(`delete from app_users where id = any($1::uuid[])`, [ids]);
    }
  });

  afterAll(async () => {
    await pool.end();
  });

  // ---------------------------------------------------------------- shape

  describe('table and column shape', () => {
    it('creates all twelve new tables', async () => {
      const result = await pool.query<{ relname: string }>(
        `select c.relname from pg_class c
           join pg_namespace n on n.oid = c.relnamespace
          where n.nspname = 'public' and c.relkind = 'r' and c.relname = any($1::text[])`,
        [Object.keys(newTableSpecs)],
      );
      const present = new Set(result.rows.map((row) => row.relname));
      for (const table of Object.keys(newTableSpecs)) {
        expect(present.has(table), `table ${table} does not exist`).toBe(true);
      }
    });

    it('adds every new applications column at the right type and nullability', async () => {
      const actual = await describeTable('applications');
      assertColumns('applications', newColumnsOnApplications, actual);
    });

    for (const [table, spec] of Object.entries(newTableSpecs)) {
      it(`gives ${table} every column at the right type and nullability`, async () => {
        const actual = await describeTable(table);
        expect(actual.size, `table ${table} does not exist`).toBeGreaterThan(0);
        assertColumns(table, spec, actual);
      });
    }

    it('defaults round_count, revision_count, cost_usd and the jsonb columns', async () => {
      const userId = await createUser();
      const applicationId = await createApplication(userId);
      const application = await pool.query<{ round_count: number }>(
        `select round_count from applications where id = $1`,
        [applicationId],
      );
      expect(application.rows[0]?.round_count).toBe(0);

      const runId = await insertReturningId(
        `insert into resume_runs(user_id, application_id) values ($1, $2) returning id::text as id`,
        [userId, applicationId],
      );
      const run = await pool.query(
        `select status, kind, revision_count, cost_usd::text as cost_usd,
                fix_resolution_matrix, compile_errors, token_usage, budget, warnings
           from resume_runs where id = $1`,
        [runId],
      );
      const row = run.rows[0] as Record<string, unknown>;
      expect(row.status).toBe('queued');
      expect(row.kind).toBe('generate');
      expect(row.revision_count).toBe(0);
      expect(Number(row.cost_usd)).toBe(0);
      expect(row.fix_resolution_matrix).toEqual([]);
      expect(row.compile_errors).toEqual({});
      expect(row.token_usage).toEqual({});
      expect(row.budget).toEqual({});
      expect(row.warnings).toEqual([]);
    });

    it('keeps resume_api_keys free of any column that could hold a plaintext secret', async () => {
      const actual = await describeTable('resume_api_keys');
      expect(actual.size, 'resume_api_keys does not exist').toBeGreaterThan(0);
      const forbidden = /(^|_)(key|token|secret|api_key|plaintext|value)($|_)/;
      for (const name of actual.keys()) {
        expect(forbidden.test(name), `resume_api_keys.${name} could hold a plaintext secret`).toBe(false);
      }
      expect(actual.get('ciphertext')?.data_type).toBe('bytea');
    });

    it('keeps resume_llm_calls free of prompt or completion text', async () => {
      const actual = await describeTable('resume_llm_calls');
      expect(actual.size, 'resume_llm_calls does not exist').toBeGreaterThan(0);
      const forbidden = ['prompt', 'completion', 'response', 'output', 'input', 'text', 'body', 'messages'];
      for (const name of actual.keys()) {
        for (const word of forbidden) {
          const offends = name.includes(word) && !name.endsWith('_tokens');
          expect(offends, `resume_llm_calls.${name} could hold prompt or completion text`).toBe(false);
        }
      }
    });
  });

  // ---------------------------------------------- applications check widening

  describe('applications check constraints', () => {
    it("accepts 'draft' as current_status", async () => {
      const userId = await createUser();
      const id = await createApplication(userId, { currentStatus: 'draft' });
      const result = await pool.query<{ current_status: string }>(
        `select current_status from applications where id = $1`,
        [id],
      );
      expect(result.rows[0]?.current_status).toBe('draft');
    });

    it('keeps the eight existing current_status values', async () => {
      const userId = await createUser();
      for (const status of [
        'applied',
        'acknowledged',
        'assessment',
        'interview_invite',
        'interview_scheduled',
        'offer',
        'rejected',
        'withdrawn',
      ]) {
        await expect(createApplication(userId, { currentStatus: status })).resolves.toBeTruthy();
      }
    });

    it('still rejects a current_status that is not in the enum', async () => {
      const userId = await createUser();
      await expectViolation(CHECK_VIOLATION, () =>
        createApplication(userId, { currentStatus: 'ghosted' }),
      );
    });

    it("accepts 'generated' and 'imported' as origin", async () => {
      const userId = await createUser();
      for (const origin of ['gmail', 'manual', 'generated', 'imported']) {
        const id = await createApplication(userId, { origin });
        const result = await pool.query<{ origin: string }>(
          `select origin from applications where id = $1`,
          [id],
        );
        expect(result.rows[0]?.origin).toBe(origin);
      }
    });

    it('still rejects an origin that is not in the enum', async () => {
      const userId = await createUser();
      await expectViolation(CHECK_VIOLATION, () => createApplication(userId, { origin: 'telepathy' }));
    });

    it("constrains jd_source_type to 'text', 'url' and 'upload'", async () => {
      const userId = await createUser();
      for (const value of ['text', 'url', 'upload']) {
        const id = await createApplication(userId);
        await expect(
          pool.query(`update applications set jd_source_type = $2 where id = $1`, [id, value]),
        ).resolves.toBeTruthy();
      }
      const bad = await createApplication(userId);
      await expectViolation(CHECK_VIOLATION, () =>
        pool.query(`update applications set jd_source_type = 'carrier_pigeon' where id = $1`, [bad]),
      );
    });

    it('points derived_from at another application and nulls it when that one is deleted', async () => {
      const userId = await createUser();
      const parentId = await createApplication(userId);
      const childId = await createApplication(userId);
      await pool.query(`update applications set derived_from = $2 where id = $1`, [childId, parentId]);
      await pool.query(`delete from applications where id = $1`, [parentId]);
      const result = await pool.query<{ derived_from: string | null }>(
        `select derived_from from applications where id = $1`,
        [childId],
      );
      expect(result.rows).toHaveLength(1);
      expect(result.rows[0]?.derived_from).toBeNull();
    });
  });

  // ------------------------------------------------------- migrated_from index

  describe('unique index on (user_id, migrated_from)', () => {
    it('rejects a second row with the same migrated_from for the same user', async () => {
      const userId = await createUser();
      const directory = `v1/applications/acme-corp-staff-engineer-${randomUUID()}`;
      const first = await createApplication(userId);
      await pool.query(`update applications set migrated_from = $2 where id = $1`, [first, directory]);
      const second = await createApplication(userId);
      await expectViolation(UNIQUE_VIOLATION, () =>
        pool.query(`update applications set migrated_from = $2 where id = $1`, [second, directory]),
      );
    });

    it('permits the same migrated_from for a different user', async () => {
      const directory = `v1/applications/shared-${randomUUID()}`;
      const userA = await createUser();
      const userB = await createUser();
      const a = await createApplication(userA);
      const b = await createApplication(userB);
      await pool.query(`update applications set migrated_from = $2 where id = $1`, [a, directory]);
      await expect(
        pool.query(`update applications set migrated_from = $2 where id = $1`, [b, directory]),
      ).resolves.toBeTruthy();
    });

    it('permits many rows with a null migrated_from for one user', async () => {
      const userId = await createUser();
      await createApplication(userId);
      await createApplication(userId);
      await createApplication(userId);
      const result = await pool.query<{ count: string }>(
        `select count(*)::text as count from applications
          where user_id = $1 and migrated_from is null`,
        [userId],
      );
      expect(Number(result.rows[0]?.count)).toBe(3);
    });
  });

  // ------------------------------------------------- source-of-truth tables

  describe('source of truth', () => {
    it('stores company dates as text, so "Jul 2022" and "Present" survive', async () => {
      const userId = await createUser();
      const companyId = await insertReturningId(
        `insert into sot_companies(user_id, name, start_date, end_date)
         values ($1, 'Acme Corp', 'Jul 2022', 'Present') returning id::text as id`,
        [userId],
      );
      const result = await pool.query<{ start_date: string; end_date: string }>(
        `select start_date, end_date from sot_companies where id = $1`,
        [companyId],
      );
      expect(result.rows[0]?.start_date).toBe('Jul 2022');
      expect(result.rows[0]?.end_date).toBe('Present');
    });

    it('lets a bullet belong to a company with no project', async () => {
      const userId = await createUser();
      const companyId = await insertReturningId(
        `insert into sot_companies(user_id, name) values ($1, 'Acme Corp') returning id::text as id`,
        [userId],
      );
      const bulletId = await insertReturningId(
        `insert into sot_bullets(user_id, company_id, text)
         values ($1, $2, 'Ran the on-call rotation') returning id::text as id`,
        [userId, companyId],
      );
      const result = await pool.query<{ project_id: string | null }>(
        `select project_id from sot_bullets where id = $1`,
        [bulletId],
      );
      expect(result.rows[0]?.project_id).toBeNull();
    });

    it('makes sot_skills unique on (user_id, lower(name))', async () => {
      const userId = await createUser();
      const name = `Postgres ${randomUUID()}`;
      await pool.query(`insert into sot_skills(user_id, name) values ($1, $2)`, [userId, name]);
      await expectViolation(UNIQUE_VIOLATION, () =>
        pool.query(`insert into sot_skills(user_id, name) values ($1, $2)`, [
          userId,
          name.toUpperCase(),
        ]),
      );
    });

    it('lets two users hold the same skill name', async () => {
      const userA = await createUser();
      const userB = await createUser();
      const name = `Postgres ${randomUUID()}`;
      await pool.query(`insert into sot_skills(user_id, name) values ($1, $2)`, [userA, name]);
      await expect(
        pool.query(`insert into sot_skills(user_id, name) values ($1, $2)`, [userB, name]),
      ).resolves.toBeTruthy();
    });
  });

  // ------------------------------------------------------------- seeded rows

  describe('seeded system rows', () => {
    it('seeds exactly ten system templates', async () => {
      const result = await pool.query<{ count: string }>(
        `select count(*)::text as count from resume_templates where user_id is null`,
      );
      expect(Number(result.rows[0]?.count)).toBe(10);
    });

    it('marks every seeded template is_system with a null user_id', async () => {
      const result = await pool.query<{ count: string }>(
        `select count(*)::text as count from resume_templates
          where user_id is null and is_system is not true`,
      );
      expect(Number(result.rows[0]?.count)).toBe(0);
    });

    it('seeds the five v1 keys in both kinds', async () => {
      const result = await pool.query<{ key: string; kind: string }>(
        `select key, kind from resume_templates where user_id is null order by kind, key`,
      );
      const actual = result.rows.map((row) => `${row.kind}__${row.key}`).sort();
      const expected = systemTemplateKinds
        .flatMap((kind) => systemTemplateKeys.map((key) => `${kind}__${key}`))
        .sort();
      expect(actual).toEqual(expected);
    });

    it('gives every seeded template a LaTeX body', async () => {
      const result = await pool.query<{ key: string; kind: string; tex_source: string }>(
        `select key, kind, tex_source from resume_templates where user_id is null`,
      );
      expect(result.rows).toHaveLength(10);
      for (const row of result.rows) {
        const label = `${row.kind}__${row.key}`;
        expect(row.tex_source, `${label} is empty`).toBeTruthy();
        expect(row.tex_source, `${label} has no \\documentclass`).toContain('\\documentclass');
        expect(row.tex_source, `${label} has no \\begin{document}`).toContain('\\begin{document}');
        expect(
          row.tex_source.trimStart().startsWith('\\documentclass'),
          `${label} does not start with \\documentclass`,
        ).toBe(true);
      }
    });

    it('seeds exactly six system prompts, one per stage', async () => {
      const result = await pool.query<{ stage: string; version: number; is_active: boolean; body: string }>(
        `select stage, version, is_active, body from resume_prompts where user_id is null`,
      );
      expect(result.rows).toHaveLength(6);
      expect(result.rows.map((row) => row.stage).sort()).toEqual([...systemPromptStages].sort());
      for (const row of result.rows) {
        expect(row.version, `${row.stage} version`).toBe(1);
        expect(row.is_active, `${row.stage} is_active`).toBe(true);
        expect(row.body.length, `${row.stage} body is empty`).toBeGreaterThan(0);
      }
    });

    it('seeds the ats prompt with the two placeholders it is specified with', async () => {
      const result = await pool.query<{ body: string }>(
        `select body from resume_prompts where user_id is null and stage = 'ats'`,
      );
      expect(result.rows).toHaveLength(1);
      expect(result.rows[0]?.body).toContain('{{JD_TEXT}}');
      expect(result.rows[0]?.body).toContain('{{ATS_FINDINGS}}');
    });
  });

  // ---------------------------------------------------- templates and prompts

  describe('template and prompt constraints', () => {
    it("constrains template kind to 'single_page' and 'multi_page'", async () => {
      const userId = await createUser();
      await expectViolation(CHECK_VIOLATION, () =>
        pool.query(
          `insert into resume_templates(user_id, key, name, kind, tex_source)
           values ($1, 'frontend', 'Bad kind', 'triptych', '\\documentclass{article}')`,
          [userId],
        ),
      );
    });

    it('lets a user override a system key and rejects their own duplicate', async () => {
      const userId = await createUser();
      const insert = () =>
        pool.query(
          `insert into resume_templates(user_id, key, name, kind, tex_source)
           values ($1, 'frontend', 'My frontend', 'single_page', '\\documentclass{article}')`,
          [userId],
        );
      await expect(insert()).resolves.toBeTruthy();
      await expectViolation(UNIQUE_VIOLATION, insert);
    });

    it('rejects a second system template for the same (key, kind)', async () => {
      await expectViolation(UNIQUE_VIOLATION, () =>
        pool.query(
          `insert into resume_templates(user_id, key, name, kind, tex_source, is_system)
           values (null, 'frontend', 'Duplicate system', 'single_page', '\\documentclass{article}', true)`,
        ),
      );
    });

    it('constrains prompt stage to the six named stages', async () => {
      const userId = await createUser();
      for (const stage of systemPromptStages) {
        await expect(
          pool.query(`insert into resume_prompts(user_id, stage, body) values ($1, $2, 'body')`, [
            userId,
            stage,
          ]),
        ).resolves.toBeTruthy();
      }
      await expectViolation(CHECK_VIOLATION, () =>
        pool.query(`insert into resume_prompts(user_id, stage, body) values ($1, 'vibes', 'body')`, [
          userId,
        ]),
      );
    });

    it('allows at most one active version per (user_id, stage)', async () => {
      const userId = await createUser();
      await pool.query(
        `insert into resume_prompts(user_id, stage, body, version, is_active)
         values ($1, 'review', 'v1', 1, true)`,
        [userId],
      );
      await expectViolation(UNIQUE_VIOLATION, () =>
        pool.query(
          `insert into resume_prompts(user_id, stage, body, version, is_active)
           values ($1, 'review', 'v2', 2, true)`,
          [userId],
        ),
      );
    });

    it('allows many inactive versions per (user_id, stage)', async () => {
      const userId = await createUser();
      await pool.query(
        `insert into resume_prompts(user_id, stage, body, version, is_active)
         values ($1, 'review', 'v1', 1, false)`,
        [userId],
      );
      await expect(
        pool.query(
          `insert into resume_prompts(user_id, stage, body, version, is_active)
           values ($1, 'review', 'v2', 2, false)`,
          [userId],
        ),
      ).resolves.toBeTruthy();
    });

    it('rejects a duplicate (user_id, stage, version)', async () => {
      const userId = await createUser();
      await pool.query(
        `insert into resume_prompts(user_id, stage, body, version, is_active)
         values ($1, 'revision', 'v1', 1, false)`,
        [userId],
      );
      await expectViolation(UNIQUE_VIOLATION, () =>
        pool.query(
          `insert into resume_prompts(user_id, stage, body, version, is_active)
           values ($1, 'revision', 'another v1', 1, false)`,
          [userId],
        ),
      );
    });
  });

  // -------------------------------------------------------------------- runs

  describe('run constraints', () => {
    it('constrains run status to the five named values', async () => {
      const userId = await createUser();
      const applicationId = await createApplication(userId);
      for (const status of ['queued', 'running', 'succeeded', 'failed', 'cancelled']) {
        await expect(
          pool.query(
            `insert into resume_runs(user_id, application_id, status) values ($1, $2, $3)`,
            [userId, applicationId, status],
          ),
        ).resolves.toBeTruthy();
      }
      await expectViolation(CHECK_VIOLATION, () =>
        pool.query(`insert into resume_runs(user_id, application_id, status) values ($1, $2, 'melted')`, [
          userId,
          applicationId,
        ]),
      );
    });

    it('constrains run kind to the three named values', async () => {
      const userId = await createUser();
      const applicationId = await createApplication(userId);
      for (const kind of ['generate', 'import', 'apply_keywords']) {
        await expect(
          pool.query(`insert into resume_runs(user_id, application_id, kind) values ($1, $2, $3)`, [
            userId,
            applicationId,
            kind,
          ]),
        ).resolves.toBeTruthy();
      }
      await expectViolation(CHECK_VIOLATION, () =>
        pool.query(`insert into resume_runs(user_id, application_id, kind) values ($1, $2, 'freestyle')`, [
          userId,
          applicationId,
        ]),
      );
    });

    it("stores the ats object under v1's unprefixed key names", async () => {
      const userId = await createUser();
      const applicationId = await createApplication(userId);
      const ats = {
        total_score: 82,
        grade: 'B',
        keyword_score: 70,
        structural_score: 90,
        semantic_score: 88,
        matched: ['kubernetes'],
        missing_required: ['terraform'],
        missing_preferred: [],
        missing_nice_to_have: [],
        top_actions: ['Add terraform to the platform bullet'],
        hard_requirements: [{ requirement: '5 years backend', met: true }],
        all_hard_met: true,
        error: null,
      };
      const runId = await insertReturningId(
        `insert into resume_runs(user_id, application_id, ats) values ($1, $2, $3::jsonb)
         returning id::text as id`,
        [userId, applicationId, JSON.stringify(ats)],
      );
      const result = await pool.query<{ ats: Record<string, unknown> }>(
        `select ats from resume_runs where id = $1`,
        [runId],
      );
      expect(result.rows[0]?.ats).toEqual(ats);
    });

    it('nulls a run template_id when the template is deleted', async () => {
      const userId = await createUser();
      const applicationId = await createApplication(userId);
      const templateId = await insertReturningId(
        `insert into resume_templates(user_id, key, name, kind, tex_source)
         values ($1, 'fullstack', 'Mine', 'multi_page', '\\documentclass{article}')
         returning id::text as id`,
        [userId],
      );
      const runId = await insertReturningId(
        `insert into resume_runs(user_id, application_id, template_id) values ($1, $2, $3)
         returning id::text as id`,
        [userId, applicationId, templateId],
      );
      await pool.query(`delete from resume_templates where id = $1`, [templateId]);
      const result = await pool.query<{ template_id: string | null }>(
        `select template_id from resume_runs where id = $1`,
        [runId],
      );
      expect(result.rows).toHaveLength(1);
      expect(result.rows[0]?.template_id).toBeNull();
    });
  });

  // ------------------------------------------------------------ run events

  describe('resume_run_events', () => {
    it('rejects a duplicate (run_id, seq)', async () => {
      const userId = await createUser();
      const applicationId = await createApplication(userId);
      const runId = await insertReturningId(
        `insert into resume_runs(user_id, application_id) values ($1, $2) returning id::text as id`,
        [userId, applicationId],
      );
      const insert = () =>
        pool.query(
          `insert into resume_run_events(run_id, seq, node, status, label)
           values ($1, 7, 'generation', 'finished', 'Drafted the resume')`,
          [runId],
        );
      await expect(insert()).resolves.toBeTruthy();
      await expectViolation(UNIQUE_VIOLATION, insert);
    });

    it('permits the same seq on a different run, so replay is per run', async () => {
      const userId = await createUser();
      const applicationId = await createApplication(userId);
      const runA = await insertReturningId(
        `insert into resume_runs(user_id, application_id) values ($1, $2) returning id::text as id`,
        [userId, applicationId],
      );
      const runB = await insertReturningId(
        `insert into resume_runs(user_id, application_id) values ($1, $2) returning id::text as id`,
        [userId, applicationId],
      );
      for (const runId of [runA, runB]) {
        await expect(
          pool.query(
            `insert into resume_run_events(run_id, seq, node, status, label)
             values ($1, 1, 'targeting', 'started', 'Building the targeting brief')`,
            [runId],
          ),
        ).resolves.toBeTruthy();
      }
    });

    it('emits a pg_notify on channel resume_run_events carrying the run id', async () => {
      const userId = await createUser();
      const applicationId = await createApplication(userId);
      const runId = await insertReturningId(
        `insert into resume_runs(user_id, application_id) values ($1, $2) returning id::text as id`,
        [userId, applicationId],
      );

      const listener = new Client({ connectionString });
      const received: Notification[] = [];
      try {
        await listener.connect();
        listener.on('notification', (notification) => {
          received.push(notification);
        });
        await listener.query('listen resume_run_events');

        await pool.query(
          `insert into resume_run_events(run_id, seq, node, status, label)
           values ($1, 1, 'targeting', 'started', 'Building the targeting brief')`,
          [runId],
        );

        const deadline = Date.now() + 5000;
        while (received.length === 0 && Date.now() < deadline) {
          // A round trip on the listening connection flushes any pending
          // notification into the client's event emitter.
          await listener.query('select 1');
          await new Promise((resolve) => setTimeout(resolve, 50));
        }

        expect(received.length, 'no notification arrived within five seconds').toBeGreaterThan(0);
        const notification = received[0]!;
        expect(notification.channel).toBe('resume_run_events');
        expect(notification.payload).toBe(runId);
      } finally {
        await listener.query('unlisten resume_run_events').catch(() => undefined);
        await listener.end().catch(() => undefined);
      }
    });
  });

  // ------------------------------------------------------------- documents

  describe('resume_documents', () => {
    it('constrains kind to the seven named values', async () => {
      const userId = await createUser();
      const applicationId = await createApplication(userId);
      const kinds = [
        'resume_tex',
        'resume_pdf',
        'cover_letter_tex',
        'cover_letter_pdf',
        'jd',
        'imported_resume',
        'template_preview',
      ];
      for (const kind of kinds) {
        await expect(
          pool.query(
            `insert into resume_documents
               (user_id, application_id, kind, storage_path, byte_size, content_hash, content_type)
             values ($1, $2, $3, $4, 10, 'sha', 'application/pdf')`,
            [userId, applicationId, kind, `docs/${randomUUID()}`],
          ),
        ).resolves.toBeTruthy();
      }
      await expectViolation(CHECK_VIOLATION, () =>
        pool.query(
          `insert into resume_documents
             (user_id, application_id, kind, storage_path, byte_size, content_hash, content_type)
           values ($1, $2, 'napkin', $3, 10, 'sha', 'application/pdf')`,
          [userId, applicationId, `docs/${randomUUID()}`],
        ),
      );
    });

    it('rejects a duplicate storage_path', async () => {
      const userA = await createUser();
      const userB = await createUser();
      const applicationA = await createApplication(userA);
      const applicationB = await createApplication(userB);
      const path = `docs/${randomUUID()}/resume.pdf`;
      const insert = (userId: string, applicationId: string) =>
        pool.query(
          `insert into resume_documents
             (user_id, application_id, kind, storage_path, byte_size, content_hash, content_type)
           values ($1, $2, 'resume_pdf', $3, 10, 'sha', 'application/pdf')`,
          [userId, applicationId, path],
        );
      await expect(insert(userA, applicationA)).resolves.toBeTruthy();
      await expectViolation(UNIQUE_VIOLATION, () => insert(userB, applicationB));
    });

    it('nulls run_id when the run is deleted but keeps the document row', async () => {
      const userId = await createUser();
      const applicationId = await createApplication(userId);
      const runId = await insertReturningId(
        `insert into resume_runs(user_id, application_id) values ($1, $2) returning id::text as id`,
        [userId, applicationId],
      );
      const documentId = await insertReturningId(
        `insert into resume_documents
           (user_id, application_id, run_id, kind, storage_path, byte_size, content_hash, content_type)
         values ($1, $2, $3, 'resume_pdf', $4, 10, 'sha', 'application/pdf')
         returning id::text as id`,
        [userId, applicationId, runId, `docs/${randomUUID()}`],
      );
      await pool.query(`delete from resume_runs where id = $1`, [runId]);
      const result = await pool.query<{ run_id: string | null }>(
        `select run_id from resume_documents where id = $1`,
        [documentId],
      );
      expect(result.rows).toHaveLength(1);
      expect(result.rows[0]?.run_id).toBeNull();
    });
  });

  // ------------------------------------------------------------------- keys

  describe('resume_api_keys', () => {
    it("constrains provider to 'anthropic', 'openai' and 'openrouter'", async () => {
      const userId = await createUser();
      for (const provider of ['anthropic', 'openai', 'openrouter']) {
        await expect(
          pool.query(
            `insert into resume_api_keys(user_id, provider, ciphertext, last_four)
             values ($1, $2, $3, '1234')`,
            [userId, provider, Buffer.from('cipher')],
          ),
        ).resolves.toBeTruthy();
      }
      await expectViolation(CHECK_VIOLATION, () =>
        pool.query(
          `insert into resume_api_keys(user_id, provider, ciphertext, last_four)
           values ($1, 'skynet', $2, '1234')`,
          [userId, Buffer.from('cipher')],
        ),
      );
    });

    it("defaults label to 'default' and rejects a duplicate (user_id, provider, label)", async () => {
      const userId = await createUser();
      const insert = () =>
        pool.query(
          `insert into resume_api_keys(user_id, provider, ciphertext, last_four)
           values ($1, 'anthropic', $2, '1234')`,
          [userId, Buffer.from('cipher')],
        );
      await insert();
      const label = await pool.query<{ label: string }>(
        `select label from resume_api_keys where user_id = $1`,
        [userId],
      );
      expect(label.rows[0]?.label).toBe('default');
      await expectViolation(UNIQUE_VIOLATION, insert);
    });
  });

  // ------------------------------------------------------ keyword decisions

  describe('resume_keyword_decisions', () => {
    it("constrains decision to 'accepted', 'dismissed' and 'deferred'", async () => {
      const userId = await createUser();
      const applicationId = await createApplication(userId);
      for (const decision of ['accepted', 'dismissed', 'deferred']) {
        await expect(
          pool.query(
            `insert into resume_keyword_decisions(user_id, application_id, keyword, decision)
             values ($1, $2, $3, $4)`,
            [userId, applicationId, `keyword-${randomUUID()}`, decision],
          ),
        ).resolves.toBeTruthy();
      }
      await expectViolation(CHECK_VIOLATION, () =>
        pool.query(
          `insert into resume_keyword_decisions(user_id, application_id, keyword, decision)
           values ($1, $2, 'kubernetes', 'maybe')`,
          [userId, applicationId],
        ),
      );
    });

    it('rejects a duplicate (application_id, lower(keyword))', async () => {
      const userId = await createUser();
      const applicationId = await createApplication(userId);
      await pool.query(
        `insert into resume_keyword_decisions(user_id, application_id, keyword, decision)
         values ($1, $2, 'Kubernetes', 'accepted')`,
        [userId, applicationId],
      );
      await expectViolation(UNIQUE_VIOLATION, () =>
        pool.query(
          `insert into resume_keyword_decisions(user_id, application_id, keyword, decision)
           values ($1, $2, 'KUBERNETES', 'dismissed')`,
          [userId, applicationId],
        ),
      );
    });

    it('nulls its evidence pointers when the referenced source-of-truth row is deleted', async () => {
      const userId = await createUser();
      const applicationId = await createApplication(userId);
      const companyId = await insertReturningId(
        `insert into sot_companies(user_id, name) values ($1, 'Acme Corp') returning id::text as id`,
        [userId],
      );
      const projectId = await insertReturningId(
        `insert into sot_projects(user_id, company_id, name) values ($1, $2, 'Billing')
         returning id::text as id`,
        [userId, companyId],
      );
      const bulletId = await insertReturningId(
        `insert into sot_bullets(user_id, company_id, project_id, text) values ($1, $2, $3, 'Shipped it')
         returning id::text as id`,
        [userId, companyId, projectId],
      );
      const decisionId = await insertReturningId(
        `insert into resume_keyword_decisions
           (user_id, application_id, keyword, decision, sot_company_id, sot_project_id, sot_bullet_id)
         values ($1, $2, 'kubernetes', 'accepted', $3, $4, $5)
         returning id::text as id`,
        [userId, applicationId, companyId, projectId, bulletId],
      );
      await pool.query(`delete from sot_companies where id = $1`, [companyId]);
      const result = await pool.query<{
        sot_company_id: string | null;
        sot_project_id: string | null;
        sot_bullet_id: string | null;
      }>(
        `select sot_company_id, sot_project_id, sot_bullet_id
           from resume_keyword_decisions where id = $1`,
        [decisionId],
      );
      expect(result.rows).toHaveLength(1);
      expect(result.rows[0]?.sot_company_id).toBeNull();
      expect(result.rows[0]?.sot_project_id).toBeNull();
      expect(result.rows[0]?.sot_bullet_id).toBeNull();
    });
  });

  // ---------------------------------------------------------------- cascade

  describe('cascade behaviour', () => {
    it('clears every one of the eleven new tables when the app_users row is deleted', async () => {
      const userId = await createUser();
      const graph = await seedResumeGraph(userId);

      for (const table of userScopedTables) {
        const before = await pool.query<{ count: string }>(
          `select count(*)::text as count from ${table} where user_id = $1`,
          [userId],
        );
        expect(Number(before.rows[0]?.count), `${table} was not seeded`).toBe(1);
      }

      await pool.query(`delete from app_users where id = $1`, [userId]);

      for (const table of userScopedTables) {
        const after = await pool.query<{ count: string }>(
          `select count(*)::text as count from ${table} where user_id = $1`,
          [userId],
        );
        expect(Number(after.rows[0]?.count), `${table} left an orphan`).toBe(0);
      }

      const events = await pool.query<{ count: string }>(
        `select count(*)::text as count from resume_run_events where run_id = $1`,
        [graph.runId],
      );
      expect(Number(events.rows[0]?.count), 'resume_run_events left an orphan').toBe(0);

      const applications = await pool.query<{ count: string }>(
        `select count(*)::text as count from applications where user_id = $1`,
        [userId],
      );
      expect(Number(applications.rows[0]?.count)).toBe(0);
    });

    it('leaves the system templates and prompts alone when a user is deleted', async () => {
      const userId = await createUser();
      await seedResumeGraph(userId);
      await pool.query(`delete from app_users where id = $1`, [userId]);

      const templates = await pool.query<{ count: string }>(
        `select count(*)::text as count from resume_templates where user_id is null`,
      );
      const prompts = await pool.query<{ count: string }>(
        `select count(*)::text as count from resume_prompts where user_id is null`,
      );
      expect(Number(templates.rows[0]?.count)).toBe(10);
      expect(Number(prompts.rows[0]?.count)).toBe(6);
    });

    it('clears a company’s projects and bullets when the company is deleted', async () => {
      const userId = await createUser();
      const companyId = await insertReturningId(
        `insert into sot_companies(user_id, name) values ($1, 'Acme Corp') returning id::text as id`,
        [userId],
      );
      const projectId = await insertReturningId(
        `insert into sot_projects(user_id, company_id, name) values ($1, $2, 'Billing rewrite')
         returning id::text as id`,
        [userId, companyId],
      );
      await pool.query(
        `insert into sot_bullets(user_id, company_id, project_id, text) values ($1, $2, $3, 'With project')`,
        [userId, companyId, projectId],
      );
      await pool.query(
        `insert into sot_bullets(user_id, company_id, text) values ($1, $2, 'Without project')`,
        [userId, companyId],
      );

      const seeded = await pool.query<{ count: string }>(
        `select count(*)::text as count from sot_bullets where company_id = $1`,
        [companyId],
      );
      expect(Number(seeded.rows[0]?.count)).toBe(2);

      await pool.query(`delete from sot_companies where id = $1`, [companyId]);

      const projects = await pool.query<{ count: string }>(
        `select count(*)::text as count from sot_projects where company_id = $1`,
        [companyId],
      );
      const bullets = await pool.query<{ count: string }>(
        `select count(*)::text as count from sot_bullets where company_id = $1`,
        [companyId],
      );
      expect(Number(projects.rows[0]?.count)).toBe(0);
      expect(Number(bullets.rows[0]?.count)).toBe(0);
    });

    it('clears a project’s bullets when the project is deleted but keeps the company', async () => {
      const userId = await createUser();
      const companyId = await insertReturningId(
        `insert into sot_companies(user_id, name) values ($1, 'Acme Corp') returning id::text as id`,
        [userId],
      );
      const projectId = await insertReturningId(
        `insert into sot_projects(user_id, company_id, name) values ($1, $2, 'Billing rewrite')
         returning id::text as id`,
        [userId, companyId],
      );
      await pool.query(
        `insert into sot_bullets(user_id, company_id, project_id, text) values ($1, $2, $3, 'Scoped')`,
        [userId, companyId, projectId],
      );
      await pool.query(`delete from sot_projects where id = $1`, [projectId]);

      const bullets = await pool.query<{ count: string }>(
        `select count(*)::text as count from sot_bullets where project_id = $1`,
        [projectId],
      );
      const company = await pool.query<{ count: string }>(
        `select count(*)::text as count from sot_companies where id = $1`,
        [companyId],
      );
      expect(Number(bullets.rows[0]?.count)).toBe(0);
      expect(Number(company.rows[0]?.count)).toBe(1);
    });

    it('clears runs, events, documents, decisions and llm calls when the application is deleted', async () => {
      const userId = await createUser();
      const graph = await seedResumeGraph(userId);
      await pool.query(`delete from applications where id = $1`, [graph.applicationId]);

      for (const table of ['resume_runs', 'resume_documents', 'resume_keyword_decisions'] as const) {
        const result = await pool.query<{ count: string }>(
          `select count(*)::text as count from ${table} where application_id = $1`,
          [graph.applicationId],
        );
        expect(Number(result.rows[0]?.count), `${table} left an orphan`).toBe(0);
      }
      const events = await pool.query<{ count: string }>(
        `select count(*)::text as count from resume_run_events where run_id = $1`,
        [graph.runId],
      );
      const calls = await pool.query<{ count: string }>(
        `select count(*)::text as count from resume_llm_calls where run_id = $1`,
        [graph.runId],
      );
      expect(Number(events.rows[0]?.count)).toBe(0);
      expect(Number(calls.rows[0]?.count)).toBe(0);
    });
  });

  // ------------------------------------------------------ ownership isolation

  describe('ownership isolation', () => {
    it('never returns the other user’s rows from a user_id filtered query, for every new table', async () => {
      const userA = await createUser();
      const userB = await createUser();
      const graphA = await seedResumeGraph(userA);
      const graphB = await seedResumeGraph(userB);

      for (const table of userScopedTables) {
        const result = await pool.query<{ id: string }>(
          `select id::text as id from ${table} where user_id = $1`,
          [userA],
        );
        const ids = result.rows.map((row) => row.id);
        expect(ids, `${table} did not return user A's row`).toEqual([graphA.rowIds[table]]);
        expect(ids, `${table} leaked user B's row`).not.toContain(graphB.rowIds[table]);
      }
    });

    it('scopes resume_run_events through its run, which is the only path it has', async () => {
      const userA = await createUser();
      const userB = await createUser();
      const graphA = await seedResumeGraph(userA);
      const graphB = await seedResumeGraph(userB);

      const result = await pool.query<{ id: string }>(
        `select e.id::text as id
           from resume_run_events e
           join resume_runs r on r.id = e.run_id
          where r.user_id = $1`,
        [userA],
      );
      const ids = result.rows.map((row) => row.id);
      expect(ids).toEqual([graphA.eventId]);
      expect(ids).not.toContain(graphB.eventId);
    });

    it('scopes applications by user_id', async () => {
      const userA = await createUser();
      const userB = await createUser();
      const graphA = await seedResumeGraph(userA);
      const graphB = await seedResumeGraph(userB);

      const result = await pool.query<{ id: string }>(
        `select id::text as id from applications where user_id = $1`,
        [userA],
      );
      const ids = result.rows.map((row) => row.id);
      expect(ids).toEqual([graphA.applicationId]);
      expect(ids).not.toContain(graphB.applicationId);
    });

    it('keeps system templates and prompts out of a user-scoped query', async () => {
      const userId = await createUser();
      const graph = await seedResumeGraph(userId);
      const templates = await pool.query<{ id: string }>(
        `select id::text as id from resume_templates where user_id = $1`,
        [userId],
      );
      const prompts = await pool.query<{ id: string }>(
        `select id::text as id from resume_prompts where user_id = $1`,
        [userId],
      );
      expect(templates.rows.map((row) => row.id)).toEqual([graph.rowIds.resume_templates]);
      expect(prompts.rows.map((row) => row.id)).toEqual([graph.rowIds.resume_prompts]);
    });
  });

  // --------------------------------------------------------- draft projection

  describe('refresh_application_projection and draft', () => {
    it('leaves a draft with no status events as draft', async () => {
      const userId = await createUser();
      const applicationId = await createApplication(userId, {
        currentStatus: 'draft',
        origin: 'generated',
      });
      await pool.query(`select refresh_application_projection($1)`, [applicationId]);
      const result = await pool.query<{ current_status: string }>(
        `select current_status from applications where id = $1`,
        [applicationId],
      );
      expect(result.rows[0]?.current_status).toBe('draft');
    });

    it('leaves a draft as draft when only non-status events exist', async () => {
      const userId = await createUser();
      const applicationId = await createApplication(userId, {
        currentStatus: 'draft',
        origin: 'generated',
      });
      await pool.query(
        `insert into application_events(application_id, event_type, occurred_at, source)
         values ($1, 'recruiter_outreach', now(), 'manual')`,
        [applicationId],
      );
      await pool.query(`select refresh_application_projection($1)`, [applicationId]);
      const result = await pool.query<{ current_status: string }>(
        `select current_status from applications where id = $1`,
        [applicationId],
      );
      expect(result.rows[0]?.current_status).toBe('draft');
    });

    it("moves a draft to 'applied' when an applied event exists", async () => {
      const userId = await createUser();
      const applicationId = await createApplication(userId, {
        currentStatus: 'draft',
        origin: 'generated',
      });
      await pool.query(
        `insert into application_events(application_id, event_type, occurred_at, source)
         values ($1, 'applied', now(), 'manual')`,
        [applicationId],
      );
      await pool.query(`select refresh_application_projection($1)`, [applicationId]);
      const result = await pool.query<{ current_status: string }>(
        `select current_status from applications where id = $1`,
        [applicationId],
      );
      expect(result.rows[0]?.current_status).toBe('applied');
    });

    it('never projects draft, because no event type spells it', async () => {
      const userId = await createUser();
      const applicationId = await createApplication(userId, { currentStatus: 'applied' });
      try {
        await pool.query(
          `insert into application_events(application_id, event_type, occurred_at, source)
           values ($1, 'draft', now(), 'manual')`,
          [applicationId],
        );
      } catch (caught) {
        // A check constraint on event_type is an even stronger guarantee than
        // the projection filter, so accept it and stop here.
        expect((caught as { code?: string }).code).toBe(CHECK_VIOLATION);
        return;
      }
      // Otherwise the load-bearing guarantee is the projection's own event_type
      // filter: a forged 'draft' event must not move the projection.
      await pool.query(`select refresh_application_projection($1)`, [applicationId]);
      const result = await pool.query<{ current_status: string }>(
        `select current_status from applications where id = $1`,
        [applicationId],
      );
      expect(result.rows[0]?.current_status).toBe('applied');
    });
  });

  // ------------------------------------------------------ set_updated_at

  describe('set_updated_at trigger', () => {
    const tablesWithUpdatedAt = [
      'applications',
      'sot_companies',
      'sot_projects',
      'sot_bullets',
      'sot_skills',
      'resume_templates',
      'resume_prompts',
      'resume_runs',
    ] as const;

    it('declares updated_at on every table the contract says has one', async () => {
      for (const table of tablesWithUpdatedAt) {
        const columns = await describeTable(table);
        expect(columns.has('updated_at'), `${table}.updated_at is missing`).toBe(true);
      }
    });

    it('overwrites a stale updated_at on update', async () => {
      const userId = await createUser();
      const applicationId = await createApplication(userId);
      const companyId = await insertReturningId(
        `insert into sot_companies(user_id, name) values ($1, 'Acme Corp') returning id::text as id`,
        [userId],
      );

      // The trigger must win over an explicit value, which is what makes the
      // column trustworthy as a change marker.
      await pool.query(
        `update applications set updated_at = timestamptz '2000-01-01', note = 'touched' where id = $1`,
        [applicationId],
      );
      await pool.query(
        `update sot_companies set updated_at = timestamptz '2000-01-01', name = 'Acme Corp Ltd' where id = $1`,
        [companyId],
      );

      const application = await pool.query<{ fresh: boolean }>(
        `select updated_at > now() - interval '1 minute' as fresh from applications where id = $1`,
        [applicationId],
      );
      const company = await pool.query<{ fresh: boolean }>(
        `select updated_at > now() - interval '1 minute' as fresh from sot_companies where id = $1`,
        [companyId],
      );
      expect(application.rows[0]?.fresh, 'applications.updated_at was not refreshed').toBe(true);
      expect(company.rows[0]?.fresh, 'sot_companies.updated_at was not refreshed').toBe(true);
    });
  });
});
