/**
 * The only unauthenticated write in Ascend. Cloudflare Access bypasses this
 * path so the public landing form can reach it, which makes Turnstile and a
 * rate limit mandatory rather than optional. Seat cap is enforced here, not by
 * the number rendered on the landing page. See architecture §2.5 and §11.4.
 */
export const dynamic = 'force-dynamic';

export function POST() {
  return Response.json({ error: 'not_implemented' }, { status: 501 });
}
