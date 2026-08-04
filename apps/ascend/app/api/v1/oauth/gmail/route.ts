import { currentUser } from '@/auth/access';
import { query } from '@/infrastructure/database';
import { oauthForEncryptedToken } from '@/infrastructure/gmail-client';

export async function DELETE() {
  const user = await currentUser();
  if (!user) return Response.json({ error: 'forbidden' }, { status: 403 });
  const accounts = await query<{ id: string; refresh_token_ciphertext: Buffer; refresh_token_nonce: Buffer; key_version: number }>(
    `select id, refresh_token_ciphertext, refresh_token_nonce, key_version from gmail_accounts where user_id = $1`, [user.id],
  );
  for (const account of accounts) {
    await oauthForEncryptedToken({ ciphertext: account.refresh_token_ciphertext, nonce: account.refresh_token_nonce, keyVersion: account.key_version })
      .revokeCredentials().catch(() => undefined);
  }
  await query(`delete from gmail_accounts where user_id = $1 returning id`, [user.id]);
  return new Response(null, { status: 204 });
}
