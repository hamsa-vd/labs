import { currentUser } from '@/auth/access';
import { applicationById } from '@/application/tracker-service';

export async function GET(_: Request, { params }: { params: Promise<{ applicationId: string }> }) {
  const user = await currentUser();
  if (!user) return Response.json({ error: 'forbidden' }, { status: 403 });
  const result = await applicationById(user.id, (await params).applicationId);
  return result.application ? Response.json({ events: result.events }) : Response.json({ error: 'not_found' }, { status: 404 });
}
