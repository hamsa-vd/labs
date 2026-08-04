import { z } from 'zod';
import { currentUser } from '@/auth/access';
import { applicationStatuses } from '@/domain/application-event';
import { createManualApplication, listApplicationsPage } from '@/application/tracker-service';

const createSchema = z.object({
  company: z.string().trim().min(1).max(80), role: z.string().trim().min(1).max(80),
  source: z.string().trim().min(1).max(40).default('manual'), appliedAt: z.coerce.date(),
  status: z.enum(applicationStatuses).default('applied'), jobUrl: z.url().nullable().optional(), note: z.string().max(1000).nullable().optional(),
});

export async function GET(request: Request) {
  const user = await currentUser();
  if (!user) return Response.json({ error: 'forbidden' }, { status: 403 });
  const url = new URL(request.url);
  const requestedLimit = Number(url.searchParams.get('limit') ?? 50);
  try {
    const page = await listApplicationsPage(user.id, {
      includeClosed: url.searchParams.get('includeClosed') === 'true', status: url.searchParams.get('status') ?? undefined,
      source: url.searchParams.get('source') ?? undefined, waitingOnUser: url.searchParams.get('waitingOnUser') === 'true',
      cursor: url.searchParams.get('cursor'), limit: Number.isFinite(requestedLimit) ? requestedLimit : 50,
    });
    return Response.json(page);
  } catch (error) {
    if (error instanceof Error && error.message === 'invalid_cursor') return Response.json({ error: 'invalid_cursor' }, { status: 400 });
    throw error;
  }
}

export async function POST(request: Request) {
  const user = await currentUser();
  if (!user) return Response.json({ error: 'forbidden' }, { status: 403 });
  const parsed = createSchema.safeParse(await request.json().catch(() => null));
  if (!parsed.success) return Response.json({ error: 'invalid_request', issues: parsed.error.issues }, { status: 400 });
  const id = await createManualApplication(user.id, parsed.data);
  return Response.json({ id }, { status: 201 });
}
