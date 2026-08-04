import { Badge, Card, Table, TableCell, TableHead, TableRow } from '@labs/design/arey';
import Link from 'next/link';
import { decodeCursor, encodeCursor } from '@/application/cursor';
import { currentUser } from '@/auth/access';
import { databaseConfigured, query } from '@/infrastructure/database';

interface SyncRun {
  id: string; mode: string; status: 'success' | 'recovered' | 'failed'; started_at: Date; finished_at: Date | null;
  messages_seen: number | null; llm_calls: number | null; messages_failed: number | null; note: string | null; error: string | null;
}

export default async function SyncRunsPage({ searchParams }: { searchParams: Promise<{ cursor?: string }> }) {
  const user = await currentUser();
  if (!user) return null;
  const params = await searchParams;
  let cursor = null;
  try { cursor = decodeCursor(params.cursor); } catch { /* Invalid UI cursors produce an empty first page. */ }
  const rows = databaseConfigured() ? await query<SyncRun>(
    `select sr.* from sync_runs sr join gmail_accounts ga on ga.id=sr.account_id
     where ga.user_id=$1 and ($2::timestamptz is null or (sr.started_at,sr.id) < ($2,$3::uuid))
     order by sr.started_at desc,sr.id desc limit 51`, [user.id, cursor?.at ?? null, cursor?.id ?? null],
  ) : [];
  const runs = rows.slice(0, 50);
  const last = runs.at(-1);
  const nextCursor = rows.length > 50 && last ? encodeCursor(last.started_at, last.id) : null;

  return (
    <main className="ascend-page">
      <div className="ascend-page-head"><div><div className="ascend-eyebrow">Accounts checked every 10 minutes</div><h1 className="ascend-title">Sync runs</h1></div></div>
      <Card padded={false} variant="flat">
        {runs.length ? <Table><thead><TableRow><TableHead>Status</TableHead><TableHead>Mode</TableHead><TableHead>Started</TableHead><TableHead align="right">Seen / model / failed</TableHead><TableHead>Details</TableHead></TableRow></thead><tbody>{runs.map((run) => <TableRow key={run.id}><TableCell><Badge tone={run.status === 'success' ? 'success' : run.status === 'recovered' ? 'warning' : 'danger'} dot>{run.status}</Badge></TableCell><TableCell mono>{run.mode}</TableCell><TableCell mono>{run.started_at.toLocaleString()}</TableCell><TableCell mono align="right">{run.messages_seen ?? 0} / {run.llm_calls ?? 0} / {run.messages_failed ?? 0}</TableCell><TableCell>{run.error ?? run.note ?? '—'}</TableCell></TableRow>)}</tbody></Table> : <div className="ascend-empty">No sync runs yet.</div>}
      </Card>
      {nextCursor && <Link className="ascend-link-button" href={`/sync-runs?cursor=${encodeURIComponent(nextCursor)}`}>Next page</Link>}
    </main>
  );
}
