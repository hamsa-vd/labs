import { currentUser } from '@/auth/access';
import { query } from '@/infrastructure/database';

export async function POST(request: Request) {
  const user = await currentUser();
  if (!user) return Response.json({ error: 'forbidden' }, { status: 403 });
  const body = await request.json().catch(() => ({})) as { mode?: unknown };
  const mode = body.mode === 'full' ? 'full' : 'incremental';
  const jobs = await query<{ id: string }>(
    `insert into sync_jobs(account_id,requested_by,mode)
     select id,$1,$2 from gmail_accounts where user_id=$1 and status='active'
       and not exists (select 1 from sync_jobs where account_id=gmail_accounts.id and status in ('queued','running'))
     returning id`, [user.id, mode],
  );
  return Response.json({ jobs: jobs.map((job) => job.id) }, { status: 202 });
}
