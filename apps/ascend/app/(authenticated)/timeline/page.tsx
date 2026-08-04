import { Badge, Button, Card } from '@labs/design/arey';
import Link from 'next/link';
import { decodeCursor, encodeCursor } from '@/application/cursor';
import { currentUser } from '@/auth/access';
import { normalizeEntity } from '@/domain/normalization';
import { databaseConfigured, query } from '@/infrastructure/database';
import { EvidenceButton } from '@/ui/evidence-button';

interface TimelineEvent {
  id: string; event_type: string; occurred_at: Date; source: string; application_id: string;
  company_display: string; role_title: string | null; subject: string | null; confidence: string | null; has_evidence: boolean;
}

export default async function TimelinePage({ searchParams }: { searchParams: Promise<{ company?: string; role?: string; cursor?: string }> }) {
  const user = await currentUser();
  if (!user) return null;
  const filters = await searchParams;
  let cursor = null;
  try { cursor = decodeCursor(filters.cursor); } catch { /* Invalid UI cursors produce an empty first page. */ }
  const rows = databaseConfigured() ? await query<TimelineEvent>(
    `select e.id,e.event_type,e.occurred_at,e.source,a.id application_id,a.company_display,a.role_title,rm.subject,
       le.confidence::text,(le.evidence_offset is not null) has_evidence
     from application_events e join applications a on a.id=e.application_id
     left join raw_messages rm on rm.id=e.raw_message_id left join llm_extractions le on le.id=e.llm_extraction_id
     where a.user_id=$1 and ($2::text is null or a.company_norm=$2) and ($3::text is null or a.role_norm=$3)
       and ($4::timestamptz is null or (e.occurred_at,e.id) < ($4,$5::uuid))
     order by e.occurred_at desc,e.id desc limit 26`,
    [user.id, filters.company ? normalizeEntity(filters.company) : null, filters.role ? normalizeEntity(filters.role) : null, cursor?.at ?? null, cursor?.id ?? null],
  ) : [];
  const events = rows.slice(0, 25);
  const last = events.at(-1);
  const nextCursor = rows.length > 25 && last ? encodeCursor(last.occurred_at, last.id) : null;
  const next = new URLSearchParams();
  if (filters.company) next.set('company', filters.company);
  if (filters.role) next.set('role', filters.role);
  if (nextCursor) next.set('cursor', nextCursor);

  return (
    <main className="ascend-page ascend-page--narrow">
      <div className="ascend-page-head"><div><div className="ascend-eyebrow">Append only</div><h1 className="ascend-title">Timeline</h1></div></div>
      <Card title="Filters">
        <form className="ascend-filter-form" method="get">
          <label className="ascend-label">Company<input name="company" defaultValue={filters.company ?? ''} /></label>
          <label className="ascend-label">Role<input name="role" defaultValue={filters.role ?? ''} /></label>
          <Button type="submit">Apply filters</Button>
          <Link className="ascend-link-button" href="/timeline">Clear</Link>
        </form>
      </Card>
      <Card>
        {events.length ? events.map((event) => <article className="ascend-event" key={event.id}><time>{event.occurred_at.toLocaleString()}</time><div><div className="ascend-actions"><Badge mono tone="outline">{event.event_type}</Badge><span className="ascend-meta">{event.confidence ? `confidence ${event.confidence}` : event.source}</span></div><h3 style={{ marginTop: 'var(--space-3)' }}><Link href={`/applications/${event.application_id}`}>{event.company_display}</Link></h3><p>{event.role_title ?? 'Role unknown'}{event.subject ? ` · ${event.subject}` : ''}</p>{event.has_evidence && <EvidenceButton eventId={event.id} />}</div></article>) : <div className="ascend-empty">No events match these filters.</div>}
      </Card>
      {nextCursor && <Link className="ascend-link-button" href={`/timeline?${next}`}>Next page</Link>}
    </main>
  );
}
