import { currentUser } from '@/auth/access';
import { decodeCursor, encodeCursor } from '@/application/cursor';
import { normalizeEntity } from '@/domain/normalization';
import { databaseConfigured, query } from '@/infrastructure/database';

export async function GET(request: Request) {
  const user = await currentUser();
  if (!user) return Response.json({ error: 'forbidden' }, { status: 403 });
  if (!databaseConfigured()) return Response.json({ events: [], nextCursor: null });
  const url = new URL(request.url);
  let cursor;
  try { cursor = decodeCursor(url.searchParams.get('cursor')); }
  catch { return Response.json({ error: 'invalid_cursor' }, { status: 400 }); }
  const requestedLimit = Number(url.searchParams.get('limit') ?? 50);
  const limit = Math.max(1, Math.min(Number.isFinite(requestedLimit) ? requestedLimit : 50, 100));
  const company = url.searchParams.get('company');
  const role = url.searchParams.get('role');
  const events = await query<{ id: string; occurred_at: Date } & Record<string, unknown>>(
    `select e.id,e.event_type,e.occurred_at,e.scheduled_at,e.deadline_at,e.source,
       a.id application_id,a.company_display,a.role_title,rm.subject,le.confidence,
       (le.evidence_offset is not null) has_evidence
     from application_events e join applications a on a.id=e.application_id
     left join raw_messages rm on rm.id=e.raw_message_id left join llm_extractions le on le.id=e.llm_extraction_id
     where a.user_id=$1 and ($2::text is null or a.company_norm=$2) and ($3::text is null or a.role_norm=$3)
       and ($4::timestamptz is null or (e.occurred_at,e.id) < ($4,$5::uuid))
     order by e.occurred_at desc,e.id desc limit $6`,
    [user.id, company ? normalizeEntity(company) : null, role ? normalizeEntity(role) : null, cursor?.at ?? null, cursor?.id ?? null, limit + 1],
  );
  const page = events.slice(0, limit);
  const last = page.at(-1);
  return Response.json({ events: page, nextCursor: events.length > limit && last ? encodeCursor(last.occurred_at, last.id) : null });
}
