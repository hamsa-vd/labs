import type { ReactNode } from 'react';
import { redirect } from 'next/navigation';
import { currentUser } from '@/auth/access';
import { databaseConfigured, query } from '@/infrastructure/database';
import { AppShell } from '@/ui/app-shell';

export const dynamic = 'force-dynamic';

interface NavigationCounts {
  applications: number;
  timeline: number;
  review: number;
}

interface SyncSummary {
  accountStatus: 'active' | 'needs_reauth' | 'revoked' | 'missing';
  lastRunStatus: 'success' | 'recovered' | 'failed' | null;
  lastRunAt: string | null;
  jobStatus: 'queued' | 'running' | null;
}

function relativeTime(value: Date | null): string | null {
  if (!value) return null;
  const minutes = Math.max(0, Math.round((Date.now() - value.getTime()) / 60_000));
  if (minutes < 1) return 'just now';
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours} hr ago`;
  return `${Math.round(hours / 24)} d ago`;
}

export default async function AuthenticatedLayout({ children }: Readonly<{ children: ReactNode }>) {
  const user = await currentUser();
  if (!user) redirect('/no-access');

  let navigationCounts: NavigationCounts = { applications: 0, timeline: 0, review: 0 };
  let syncSummary: SyncSummary = { accountStatus: 'missing', lastRunStatus: null, lastRunAt: null, jobStatus: null };
  if (databaseConfigured()) {
    try {
      const rows = await query<NavigationCounts>(
        `select
           (select count(*)::int from applications where user_id=$1 and not archived) applications,
           (select count(*)::int from application_events e join applications a on a.id=e.application_id where a.user_id=$1) timeline,
           (select count(*)::int from llm_extractions le
              join raw_messages rm on rm.id=le.raw_message_id
              join gmail_accounts ga on ga.id=rm.account_id
            where ga.user_id=$1 and le.review_state='needs_review') review`, [user.id],
      );
      navigationCounts = rows[0] ?? navigationCounts;
    } catch {
      // Navigation remains usable if an older local database lacks an optional table.
    }
    try {
      const rows = await query<{ account_status: SyncSummary['accountStatus']; last_run_status: SyncSummary['lastRunStatus']; last_run_at: Date | null; job_status: SyncSummary['jobStatus'] }>(
        `select ga.status account_status, sr.status last_run_status, sr.started_at last_run_at, sj.status job_status
           from gmail_accounts ga
           left join lateral (select status, started_at from sync_runs where account_id=ga.id order by started_at desc limit 1) sr on true
           left join lateral (select status from sync_jobs where account_id=ga.id and status in ('queued','running') order by requested_at desc limit 1) sj on true
          where ga.user_id=$1 limit 1`, [user.id],
      );
      const row = rows[0];
      if (row) syncSummary = {
        accountStatus: row.account_status,
        lastRunStatus: row.last_run_status,
        lastRunAt: relativeTime(row.last_run_at),
        jobStatus: row.job_status,
      };
    } catch {
      // Keep the shell available even when sync observability is not migrated yet.
    }
  }

  return <AppShell email={user.email} navigationCounts={navigationCounts} syncSummary={syncSummary} model={process.env.OLLAMA_MODEL ?? 'qwen3:8b'}>{children}</AppShell>;
}
