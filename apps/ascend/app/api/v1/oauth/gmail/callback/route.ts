import { cookies } from 'next/headers';
import { NextRequest, NextResponse } from 'next/server';
import { google } from 'googleapis';
import { currentUser, normalizeEmail } from '@/auth/access';
import { hashOAuthState, safeEqual } from '@/auth/oauth-state';
import { oauthClient } from '@/infrastructure/gmail-client';
import { query, transaction } from '@/infrastructure/database';
import { encryptStoredToken } from '@/security/token-crypto';

export const dynamic = 'force-dynamic';

function oauthRedirect(origin: string, reason: string) {
  const response = NextResponse.redirect(new URL(`/settings?oauth=${reason}`, origin));
  response.cookies.delete('ascend_oauth_state');
  response.cookies.delete('ascend_oauth_verifier');
  return response;
}

export async function GET(request: NextRequest) {
  const origin = process.env.APP_ORIGIN ?? request.nextUrl.origin;
  const user = await currentUser();
  if (!user) return NextResponse.redirect(new URL('/no-access', origin));
  const jar = await cookies();
  const state = request.nextUrl.searchParams.get('state');
  const code = request.nextUrl.searchParams.get('code');
  const expected = jar.get('ascend_oauth_state')?.value;
  const verifier = jar.get('ascend_oauth_verifier')?.value;
  if (!state || !safeEqual(expected, state) || !code || !verifier) {
    return oauthRedirect(origin, 'invalid');
  }
  const consumed = await query<{ state_sha256: string }>(
    `update oauth_states set used_at=now()
     where state_sha256=$1 and user_id=$2 and used_at is null and expires_at>now()
     returning state_sha256`, [hashOAuthState(state), user.id],
  );
  if (!consumed.length) return oauthRedirect(origin, 'replayed-state');

  const auth = oauthClient();
  const tokenResponse = await auth.getToken({ code, codeVerifier: verifier }).catch(() => null);
  if (!tokenResponse) return oauthRedirect(origin, 'invalid-code');
  const { tokens } = tokenResponse;
  if (!tokens.refresh_token) return oauthRedirect(origin, 'missing-refresh-token');
  auth.setCredentials(tokens);
  const gmail = google.gmail({ version: 'v1', auth });
  const profile = await gmail.users.getProfile({ userId: 'me' });
  const gmailAddress = normalizeEmail(profile.data.emailAddress ?? '');
  if (gmailAddress !== normalizeEmail(user.email)) {
    await auth.revokeCredentials().catch(() => undefined);
    return oauthRedirect(origin, 'email-mismatch');
  }

  const encrypted = encryptStoredToken(tokens.refresh_token);
  await transaction(async (client) => {
    const account = await client.query<{ id: string }>(
      `insert into gmail_accounts(user_id, gmail_address, refresh_token_ciphertext, refresh_token_nonce, key_version, status)
       values ($1, $2, $3, $4, $5, 'active')
       on conflict (user_id, gmail_address) do update set
         refresh_token_ciphertext = excluded.refresh_token_ciphertext,
         refresh_token_nonce = excluded.refresh_token_nonce,
         key_version = excluded.key_version,
         status = 'active'
       returning id`,
      [user.id, gmailAddress, encrypted.ciphertext, encrypted.nonce, encrypted.keyVersion],
    );
    await client.query(
      `insert into sync_jobs(account_id, requested_by, mode) values ($1, $2, 'full')`,
      [account.rows[0]?.id, user.id],
    );
  });
  await query(`delete from oauth_states where state_sha256=$1`, [hashOAuthState(state)]);

  const response = NextResponse.redirect(new URL('/overview?connected=1', origin));
  response.cookies.delete('ascend_oauth_state');
  response.cookies.delete('ascend_oauth_verifier');
  return response;
}
