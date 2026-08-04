import { serviceHealth } from '@/application/health-service';

export const dynamic = 'force-dynamic';

export async function GET() {
  const health = await serviceHealth();
  return Response.json({ status: health.status, checkedAt: health.checkedAt }, {
    status: health.status === 'ok' ? 200 : 503,
    headers: { 'cache-control': 'no-store' },
  });
}
