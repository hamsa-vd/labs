import { randomUUID } from 'node:crypto';
import { Pool } from 'pg';
import { afterAll, beforeAll, describe, expect, it } from 'vitest';

const connectionString = process.env.TEST_DATABASE_URL;
const suite = describe.skipIf(!connectionString);
let pool: Pool;

suite('Postgres production invariants', () => {
  beforeAll(() => { pool = new Pool({ connectionString, max: 2 }); });
  afterAll(async () => { await pool.end(); });

  it('grants the same normalized email once under concurrent calls', async () => {
    const email = `integration-${randomUUID()}@example.com`;
    try {
      await Promise.all([
        pool.query(`select (grant_access($1,1000,'integration')).id`, [email.toUpperCase()]),
        pool.query(`select (grant_access($1,1000,'integration')).id`, [email]),
      ]);
      const count = await pool.query<{ count: string }>(`select count(*)::text from access_allowlist where email=$1`, [email]);
      expect(Number(count.rows[0]?.count)).toBe(1);
    } finally {
      await pool.query(`delete from access_allowlist where email=$1`, [email]);
    }
  });

  it('keeps Gmail message ingestion idempotent', async () => {
    const client = await pool.connect();
    try {
      await client.query('begin');
      const email = `integration-${randomUUID()}@example.com`;
      const user = await client.query<{ id: string }>(`insert into app_users(email) values ($1) returning id`, [email]);
      const account = await client.query<{ id: string }>(
        `insert into gmail_accounts(user_id,gmail_address,refresh_token_ciphertext,refresh_token_nonce)
         values ($1,$2,$3,$4) returning id`, [user.rows[0]?.id, email, Buffer.from('cipher'), Buffer.alloc(12)],
      );
      const messageId = randomUUID();
      const insert = () => client.query(
        `insert into raw_messages(account_id,gmail_message_id,gmail_thread_id,from_address,from_domain,internal_date,prefilter_score)
         values ($1,$2,$2,'sender@example.com','example.com',now(),0)
         on conflict (account_id,gmail_message_id) do nothing`, [account.rows[0]?.id, messageId],
      );
      await insert(); await insert();
      const count = await client.query<{ count: string }>(`select count(*)::text from raw_messages where account_id=$1`, [account.rows[0]?.id]);
      expect(Number(count.rows[0]?.count)).toBe(1);
    } finally {
      await client.query('rollback');
      client.release();
    }
  });

  it('cascades account data when the app user is deleted', async () => {
    const client = await pool.connect();
    try {
      await client.query('begin');
      const email = `integration-${randomUUID()}@example.com`;
      const user = await client.query<{ id: string }>(`insert into app_users(email) values ($1) returning id`, [email]);
      await client.query(
        `insert into gmail_accounts(user_id,gmail_address,refresh_token_ciphertext,refresh_token_nonce)
         values ($1,$2,$3,$4)`, [user.rows[0]?.id, email, Buffer.from('cipher'), Buffer.alloc(12)],
      );
      await client.query(`delete from app_users where id=$1`, [user.rows[0]?.id]);
      const count = await client.query<{ count: string }>(`select count(*)::text from gmail_accounts where user_id=$1`, [user.rows[0]?.id]);
      expect(Number(count.rows[0]?.count)).toBe(0);
    } finally {
      await client.query('rollback');
      client.release();
    }
  });
});
