import { database } from '@/infrastructure/database';
import { runSyncJob } from '@/application/sync-service';
import { runWorkerCommand } from './worker-command';

await runWorkerCommand('sync.backfill', async () => {
  const accountId = process.argv[2];
  const rows = await database().query<{ id: string }>(
    `insert into sync_jobs(account_id, mode)
     select id, 'full' from gmail_accounts where ($1::uuid is null or id=$1)
     returning id`, [accountId ?? null],
  );
  for (const row of rows.rows) await runSyncJob(row.id);
});
