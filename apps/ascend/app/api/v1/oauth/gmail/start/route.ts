import { NextResponse } from 'next/server';
import { CodeChallengeMethod } from 'google-auth-library';
import { currentUser } from '@/auth/access';
import { createOAuthState, hashOAuthState } from '@/auth/oauth-state';
import { GMAIL_READONLY_SCOPE, oauthClient } from '@/infrastructure/gmail-client';
import { query } from '@/infrastructure/database';

export const dynamic = 'force-dynamic';

export async function GET() {
  const user = await currentUser();
  if (!user) return NextResponse.redirect(new URL('/no-access', process.env.APP_ORIGIN ?? 'http://localhost:3000'));
  const currentNotice = process.env.PRIVACY_NOTICE_VERSION ?? '2026-08-03';
  if (!user.privacyAcceptedAt || user.privacyNoticeVersion !== currentNotice) {
    return NextResponse.redirect(new URL('/settings?notice=required', process.env.APP_ORIGIN ?? 'http://localhost:3000'));
  }

  const { state, verifier, challenge } = createOAuthState();
  await query(
    `insert into oauth_states(state_sha256,user_id,expires_at) values ($1,$2,now()+interval '10 minutes')`,
    [hashOAuthState(state), user.id],
  );
  const url = oauthClient().generateAuthUrl({
    access_type: 'offline',
    prompt: 'consent',
    scope: [GMAIL_READONLY_SCOPE],
    state,
    code_challenge: challenge,
    code_challenge_method: CodeChallengeMethod.S256,
  });
  const response = NextResponse.redirect(url);
  const cookie = { httpOnly: true, secure: process.env.NODE_ENV === 'production', sameSite: 'lax' as const, maxAge: 600, path: '/api/v1/oauth/gmail/callback' };
  response.cookies.set('ascend_oauth_state', state, cookie);
  response.cookies.set('ascend_oauth_verifier', verifier, cookie);
  return response;
}
