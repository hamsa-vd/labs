import { currentUser } from '@/auth/access';
import { databaseConfigured, query } from '@/infrastructure/database';

export async function GET() {
  const user = await currentUser();
  if (!user) return Response.json({ error: 'forbidden' }, { status: 403 });
  const accounts = databaseConfigured() ? await query<{ gmail_address: string; status: string; last_synced_at: Date | null }>(
    `select gmail_address,status,last_synced_at from gmail_accounts where user_id=$1`, [user.id],
  ) : [];
  return Response.json({ user, gmailAccounts: accounts });
}
