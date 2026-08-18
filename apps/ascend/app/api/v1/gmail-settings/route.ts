import { currentUser } from '@/auth/access';
import { query } from '@/infrastructure/database';

const ALLOWED_DAYS = new Set([30, 90, 365, 730, 1460]);

export async function PATCH(request: Request) {
  const user = await currentUser();
  if (!user) return Response.json({ error: 'forbidden' }, { status: 403 });
  const body = await request.json().catch(() => ({})) as { backfillDays?: unknown };
  const backfillDays = Number(body.backfillDays);
  if (!ALLOWED_DAYS.has(backfillDays)) return Response.json({ error: 'invalid_backfill_window' }, { status: 400 });
  const updated = await query<{ id: string }>(
    `update gmail_accounts set backfill_days=$2 where user_id=$1 and status='active' returning id`,
    [user.id, backfillDays],
  );
  if (!updated.length) return Response.json({ error: 'gmail_not_connected' }, { status: 409 });
  return Response.json({ backfillDays });
}

