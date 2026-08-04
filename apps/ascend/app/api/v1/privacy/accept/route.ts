import { currentUser } from '@/auth/access';
import { query } from '@/infrastructure/database';

export async function POST() {
  const user = await currentUser();
  if (!user) return Response.json({ error: 'forbidden' }, { status: 403 });
  await query(
    `update app_users set privacy_notice_version = $2, privacy_accepted_at = now() where id = $1 returning id`,
    [user.id, process.env.PRIVACY_NOTICE_VERSION ?? '2026-08-03'],
  );
  return Response.json({ accepted: true });
}
