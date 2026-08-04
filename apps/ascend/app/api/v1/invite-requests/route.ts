import { createHmac } from 'node:crypto';
import { z } from 'zod';
import { normalizeEmail } from '@/auth/access';
import { databaseConfigured, query } from '@/infrastructure/database';

export const dynamic = 'force-dynamic';

const requestSchema = z.object({ email: z.email(), note: z.string().trim().max(500).optional(), turnstileToken: z.string().optional() });

async function verifyTurnstile(token: string | undefined): Promise<boolean> {
  const secret = process.env.CLOUDFLARE_TURNSTILE_SECRET_KEY;
  // Default closed: NODE_ENV is unset for any tsx-launched script, so this must key
  // off the explicitly-set APP_ENV instead.
  if (!secret) return process.env.APP_ENV === 'development';
  if (!token) return false;
  const body = new URLSearchParams({ secret, response: token });
  const response = await fetch('https://challenges.cloudflare.com/turnstile/v0/siteverify', { method: 'POST', body, signal: AbortSignal.timeout(5_000) });
  const result = await response.json() as { success?: boolean };
  return result.success === true;
}

export async function POST(request: Request) {
  const parsed = requestSchema.safeParse(await request.json().catch(() => null));
  if (!parsed.success) return Response.json({ error: 'invalid_request' }, { status: 400 });
  if (!(await verifyTurnstile(parsed.data.turnstileToken))) return Response.json({ error: 'challenge_failed' }, { status: 400 });
  if (databaseConfigured()) {
    const email = normalizeEmail(parsed.data.email);
    const rateLimitSecret = process.env.INVITE_RATE_LIMIT_SECRET ?? process.env.CLOUDFLARE_TURNSTILE_SECRET_KEY;
    if (!rateLimitSecret) return Response.json({ error: 'invite_service_unavailable' }, { status: 503 });
    const address = request.headers.get('cf-connecting-ip') ?? request.headers.get('x-forwarded-for')?.split(',')[0]?.trim() ?? 'unknown';
    const fingerprint = createHmac('sha256', rateLimitSecret).update(address).digest('hex');
    const result = await query<{ recent: number; inserted: boolean }>(
      `with recent as (
         select count(*)::int value from invite_requests
         where request_fingerprint=$3 and requested_at > now()-interval '1 hour'
       ), inserted as (
         insert into invite_requests(email,note,request_fingerprint)
         select $1,$2,$3 from recent
         where recent.value < 5 and not exists (
           select 1 from invite_requests where lower(email)=lower($1) and requested_at > now()-interval '24 hours'
         ) returning id
       )
       select recent.value recent, exists(select 1 from inserted) inserted from recent`,
      [email, parsed.data.note ?? null, fingerprint],
    );
    if ((result[0]?.recent ?? 0) >= 5) {
      return Response.json({ error: 'rate_limited' }, { status: 429, headers: { 'retry-after': '3600' } });
    }
  }
  return Response.json({ received: true }, { status: 202 });
}
