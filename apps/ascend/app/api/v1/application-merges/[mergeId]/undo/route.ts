import { currentUser } from '@/auth/access';
import { query } from '@/infrastructure/database';

export async function POST(_: Request, { params }: { params: Promise<{ mergeId: string }> }) {
  const user = await currentUser();
  if (!user) return Response.json({ error: 'forbidden' }, { status: 403 });
  const rows = await query<{ id: string }>(
    `update application_merges set undone_at=now() where id=$1 and created_by=$2 and undone_at is null returning id`,
    [(await params).mergeId, user.id],
  );
  return rows[0] ? Response.json({ undone: true }) : Response.json({ error: 'not_found' }, { status: 404 });
}
