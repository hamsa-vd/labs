import 'server-only';
import { databaseConfigured, query } from '@/infrastructure/database';

export interface ServiceHealth {
  status: 'ok' | 'degraded';
  database: 'ok' | 'unavailable' | 'not_configured';
  worker: 'ok' | 'stale' | 'not_started' | 'not_configured';
  checkedAt: string;
}

export async function serviceHealth(): Promise<ServiceHealth> {
  const checkedAt = new Date().toISOString();
  if (!databaseConfigured()) return { status: 'ok', database: 'not_configured', worker: 'not_configured', checkedAt };
  try {
    const rows = await query<{ age_seconds: string }>(
      `select extract(epoch from (now()-heartbeat_at))::text age_seconds
       from worker_heartbeats where worker_name='gmail-sync'`,
    );
    const age = rows[0] ? Number(rows[0].age_seconds) : null;
    const worker = age === null ? 'not_started' : age <= 180 ? 'ok' : 'stale';
    return { status: worker === 'ok' ? 'ok' : 'degraded', database: 'ok', worker, checkedAt };
  } catch {
    return { status: 'degraded', database: 'unavailable', worker: 'not_started', checkedAt };
  }
}
