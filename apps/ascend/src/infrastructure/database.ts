import { Pool, type PoolClient, type QueryResultRow } from 'pg';

let pool: Pool | undefined;

export function databaseConfigured(): boolean {
  return Boolean(process.env.DATABASE_URL);
}

export function database(): Pool {
  if (!process.env.DATABASE_URL) throw new Error('DATABASE_URL is not configured');
  pool ??= new Pool({ connectionString: process.env.DATABASE_URL, max: 8, application_name: 'ascend-web' });
  return pool;
}

export async function query<T extends QueryResultRow>(text: string, values: unknown[] = []): Promise<T[]> {
  return (await database().query<T>(text, values)).rows;
}

export async function transaction<T>(operation: (client: PoolClient) => Promise<T>): Promise<T> {
  const client = await database().connect();
  try {
    await client.query('begin');
    const result = await operation(client);
    await client.query('commit');
    return result;
  } catch (error) {
    await client.query('rollback');
    throw error;
  } finally {
    client.release();
  }
}
