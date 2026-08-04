import { Badge, Card } from '@labs/design/arey';
import Link from 'next/link';
import { decodeCursor, encodeCursor } from '@/application/cursor';
import { currentUser } from '@/auth/access';
import { databaseConfigured, query } from '@/infrastructure/database';
import { ReviewActions } from '@/ui/review-actions';

interface ReviewItem {
  id: string; output: Record<string, unknown>; confidence: string | null; review_failures: string[];
  created_at: Date; subject: string | null; from_domain: string; has_evidence: boolean;
}

export default async function ReviewPage({ searchParams }: { searchParams: Promise<{ cursor?: string }> }) {
  const user = await currentUser();
  if (!user) return null;
  const params = await searchParams;
  let cursor = null;
  try { cursor = decodeCursor(params.cursor); } catch { /* Invalid UI cursors produce an empty first page. */ }
  const rows = databaseConfigured() ? await query<ReviewItem>(
    `select le.id,le.output,le.confidence::text,le.review_failures,le.created_at,rm.subject,rm.from_domain,
       (le.evidence_offset is not null) has_evidence
     from llm_extractions le join raw_messages rm on rm.id=le.raw_message_id join gmail_accounts ga on ga.id=rm.account_id
     where ga.user_id=$1 and le.review_state='needs_review'
       and ($2::timestamptz is null or (le.created_at,le.id) < ($2,$3::uuid))
     order by le.created_at desc,le.id desc limit 26`, [user.id, cursor?.at ?? null, cursor?.id ?? null],
  ) : [];
  const reviews = rows.slice(0, 25);
  const last = reviews.at(-1);
  const nextCursor = rows.length > 25 && last ? encodeCursor(last.created_at, last.id) : null;

  return (
    <main className="ascend-page ascend-page--narrow">
      <div className="ascend-page-head"><div><div className="ascend-eyebrow">{reviews.length} on this page</div><h1 className="ascend-title">Needs review</h1><p className="ascend-lede">These messages were not trusted enough to change the tracker automatically.</p></div></div>
      <div className="ascend-stack">
        {reviews.length ? reviews.map((review) => <Card key={review.id} title={review.subject ?? 'Untitled message'} description={`${review.from_domain} · ${review.created_at.toLocaleString()}`} action={<Badge tone="warning" mono>{review.confidence ?? '—'}</Badge>}><div className="ascend-row"><span>Event</span><span className="ascend-meta">{String(review.output.eventType ?? 'unknown')}</span></div><div className="ascend-row"><span>Company</span><span>{String(review.output.company ?? 'Unknown')}</span></div><p style={{ color: 'var(--text-secondary)' }}>{review.review_failures.join('. ')}</p><ReviewActions id={review.id} hasEvidence={review.has_evidence} initialCompany={String(review.output.company ?? '')} initialRole={String(review.output.roleTitle ?? '')} initialEventType={String(review.output.eventType ?? 'applied')} /></Card>) : <div className="ascend-empty">Nothing needs review.</div>}
      </div>
      {nextCursor && <Link className="ascend-link-button" href={`/review?cursor=${encodeURIComponent(nextCursor)}`}>Next page</Link>}
    </main>
  );
}
