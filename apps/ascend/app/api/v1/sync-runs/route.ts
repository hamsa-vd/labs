import { currentUser } from '@/auth/access';
import { decodeCursor, encodeCursor } from '@/application/cursor';
import { databaseConfigured, query } from '@/infrastructure/database';

export async function GET(request: Request) {
  const user = await currentUser();
  if (!user) return Response.json({ error: 'forbidden' }, { status: 403 });
  if (!databaseConfigured()) return Response.json({ runs: [], nextCursor: null });
  const url = new URL(request.url);
  let cursor;
  try { cursor = decodeCursor(url.searchParams.get('cursor')); }
  catch { return Response.json({ error: 'invalid_cursor' }, { status: 400 }); }
  const requestedLimit = Number(url.searchParams.get('limit') ?? 50);
  const limit = Math.max(1, Math.min(Number.isFinite(requestedLimit) ? requestedLimit : 50, 100));
  const runs = await query<{ id: string; started_at: Date } & Record<string, unknown>>(
    `select sr.* from sync_runs sr join gmail_accounts ga on ga.id=sr.account_id
     where ga.user_id=$1 and ($2::timestamptz is null or (sr.started_at,sr.id) < ($2,$3::uuid))
     order by sr.started_at desc,sr.id desc limit $4`,
    [user.id, cursor?.at ?? null, cursor?.id ?? null, limit + 1],
  );
  const page = runs.slice(0, limit);
  const last = page.at(-1);
  return Response.json({ runs: page, nextCursor: runs.length > limit && last ? encodeCursor(last.started_at, last.id) : null });
}
