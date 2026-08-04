import { currentUser } from '@/auth/access';
import { decodeCursor, encodeCursor } from '@/application/cursor';
import { databaseConfigured, query } from '@/infrastructure/database';

export async function GET(request: Request) {
  const user = await currentUser();
  if (!user) return Response.json({ error: 'forbidden' }, { status: 403 });
  if (!databaseConfigured()) return Response.json({ reviews: [], nextCursor: null });
  const url = new URL(request.url);
  let cursor;
  try { cursor = decodeCursor(url.searchParams.get('cursor')); }
  catch { return Response.json({ error: 'invalid_cursor' }, { status: 400 }); }
  const requestedLimit = Number(url.searchParams.get('limit') ?? 50);
  const limit = Math.max(1, Math.min(Number.isFinite(requestedLimit) ? requestedLimit : 50, 100));
  const reviews = await query<{ id: string; created_at: Date } & Record<string, unknown>>(
    `select le.id,le.output,le.confidence,le.review_failures,le.created_at,rm.subject,rm.from_domain,
       (le.evidence_offset is not null) has_evidence
     from llm_extractions le join raw_messages rm on rm.id=le.raw_message_id
     join gmail_accounts ga on ga.id=rm.account_id
     where ga.user_id=$1 and le.review_state='needs_review'
       and ($2::timestamptz is null or (le.created_at,le.id) < ($2,$3::uuid))
     order by le.created_at desc,le.id desc limit $4`,
    [user.id, cursor?.at ?? null, cursor?.id ?? null, limit + 1],
  );
  const page = reviews.slice(0, limit);
  const last = page.at(-1);
  return Response.json({ reviews: page, nextCursor: reviews.length > limit && last ? encodeCursor(last.created_at, last.id) : null });
}
