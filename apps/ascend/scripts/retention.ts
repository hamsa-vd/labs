import { database } from '@/infrastructure/database';
import { runWorkerCommand } from './worker-command';

await runWorkerCommand('retention', async () => {
  const raw = await database().query(`delete from raw_messages where internal_date < now()-interval '2 years' returning id`);
  const jobs = await database().query(`delete from sync_jobs where finished_at < now()-interval '90 days' returning id`);
  const runs = await database().query(`delete from sync_runs where finished_at < now()-interval '1 year' returning id`);
  const invites = await database().query(`delete from invite_requests where requested_at < now()-interval '1 year' returning id`);
  const oauthStates = await database().query(`delete from oauth_states where expires_at < now()-interval '1 day' returning state_sha256`);
  console.log(JSON.stringify({ event: 'retention.completed', rawMessages: raw.rowCount, syncJobs: jobs.rowCount, syncRuns: runs.rowCount, inviteRequests: invites.rowCount, oauthStates: oauthStates.rowCount }));
});
