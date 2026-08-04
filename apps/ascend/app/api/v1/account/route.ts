import { z } from 'zod';
import { currentUser } from '@/auth/access';
import { query, transaction } from '@/infrastructure/database';
import { oauthForEncryptedToken } from '@/infrastructure/gmail-client';

export async function DELETE(request: Request) {
  const user = await currentUser();
  if (!user) return Response.json({ error: 'forbidden' }, { status: 403 });
  const parsed = z.object({ confirmation: z.string() }).safeParse(await request.json().catch(() => null));
  if (!parsed.success || parsed.data.confirmation !== user.email) return Response.json({ error: 'confirmation_mismatch' }, { status: 400 });
  const accounts = await query<{ refresh_token_ciphertext: Buffer; refresh_token_nonce: Buffer; key_version: number }>(
    `select refresh_token_ciphertext,refresh_token_nonce,key_version from gmail_accounts where user_id=$1`, [user.id],
  );
  for (const account of accounts) await oauthForEncryptedToken({
    ciphertext: account.refresh_token_ciphertext, nonce: account.refresh_token_nonce, keyVersion: account.key_version,
  }).revokeCredentials().catch(() => undefined);
  // Deletion and de-authorisation are the same action: without revoking the
  // allowlist row, currentUser() recreates app_users on the very next request.
  await transaction(async (client) => {
    await client.query(`update access_allowlist set status='revoked', revoked_at=now() where email=$1`, [user.email]);
    await client.query(`delete from app_users where id=$1`, [user.id]);
  });
  return new Response(null, { status: 204 });
}
