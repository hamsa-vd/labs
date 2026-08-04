import 'server-only';
import { headers } from 'next/headers';
import { createRemoteJWKSet, jwtVerify } from 'jose';
import { databaseConfigured, query } from '@/infrastructure/database';

export interface AuthenticatedUser {
  id: string;
  email: string;
  timezone: string;
  privacyNoticeVersion: string | null;
  privacyAcceptedAt: Date | null;
}

interface UserRow {
  id: string;
  email: string;
  timezone: string;
  privacy_notice_version: string | null;
  privacy_accepted_at: Date | null;
}

let jwks: ReturnType<typeof createRemoteJWKSet> | undefined;

export function normalizeEmail(value: string): string {
  return value.trim().toLowerCase();
}

async function verifiedEmail(): Promise<string | null> {
  // Default closed: NODE_ENV is unset (falsy `!== 'production'`) for any tsx-launched
  // script, so this must key off the explicitly-set APP_ENV instead.
  if (process.env.APP_ENV === 'development' && process.env.ASCEND_DEV_EMAIL) {
    return normalizeEmail(process.env.ASCEND_DEV_EMAIL);
  }

  const requestHeaders = await headers();
  const token = requestHeaders.get('cf-access-jwt-assertion');
  const domain = process.env.CLOUDFLARE_ACCESS_TEAM_DOMAIN;
  const audience = process.env.CLOUDFLARE_ACCESS_AUDIENCE;
  if (!token || !domain || !audience) return null;

  const issuer = `https://${domain}`;
  jwks ??= createRemoteJWKSet(new URL(`${issuer}/cdn-cgi/access/certs`));
  try {
    const { payload } = await jwtVerify(token, jwks, { issuer, audience });
    const email = typeof payload.email === 'string' ? payload.email : null;
    return email ? normalizeEmail(email) : null;
  } catch {
    return null;
  }
}

export async function currentUser(): Promise<AuthenticatedUser | null> {
  const email = await verifiedEmail();
  if (!email) return null;

  if (!databaseConfigured()) {
    if (process.env.APP_ENV !== 'development') return null;
    return { id: 'development-user', email, timezone: process.env.DEFAULT_TIMEZONE ?? 'Europe/London', privacyNoticeVersion: 'development', privacyAcceptedAt: new Date() };
  }

  const allowed = await query<{ email: string }>(
    `select email::text from access_allowlist where email = $1 and status = 'active'`, [email],
  );
  if (allowed.length === 0) return null;

  const users = await query<UserRow>(
    `insert into app_users(email, timezone)
     values ($1, $2)
     on conflict (email) do update set last_seen_at = now()
     returning id, email, timezone, privacy_notice_version, privacy_accepted_at`,
    [email, process.env.DEFAULT_TIMEZONE ?? 'Europe/London'],
  );
  const user = users[0];
  if (!user) return null;
  return {
    id: user.id,
    email: user.email,
    timezone: user.timezone,
    privacyNoticeVersion: user.privacy_notice_version,
    privacyAcceptedAt: user.privacy_accepted_at,
  };
}
