import { z } from 'zod';
import { currentUser } from '@/auth/access';
import { mergeApplications } from '@/application/tracker-service';

export async function POST(request: Request) {
  const user = await currentUser();
  if (!user) return Response.json({ error: 'forbidden' }, { status: 403 });
  const parsed = z.object({ sourceId: z.uuid(), targetId: z.uuid() }).safeParse(await request.json().catch(() => null));
  if (!parsed.success || parsed.data.sourceId === parsed.data.targetId) return Response.json({ error: 'invalid_request' }, { status: 400 });
  const id = await mergeApplications(user.id, parsed.data.sourceId, parsed.data.targetId);
  return Response.json({ id }, { status: 201 });
}
