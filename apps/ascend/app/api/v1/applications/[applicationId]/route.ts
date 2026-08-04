import { z } from 'zod';
import { currentUser } from '@/auth/access';
import { applicationStatuses } from '@/domain/application-event';
import { appendManualStatus, applicationById } from '@/application/tracker-service';
import { query, transaction } from '@/infrastructure/database';
import { normalizeEntity } from '@/domain/normalization';

const updateSchema = z.discriminatedUnion('action', [
  z.object({
    action: z.literal('status'),
    status: z.enum(applicationStatuses),
    occurredAt: z.coerce.date().default(() => new Date()),
  }),
  z.object({ action: z.enum(['archive', 'restore', 'not_application']) }),
  z.object({
    action: z.literal('metadata'),
    company: z.string().trim().min(1).max(80),
    role: z.string().trim().max(80).nullable(),
    source: z.string().trim().min(1).max(40),
    jobUrl: z.url().nullable(),
    note: z.string().max(1000).nullable(),
  }),
]);

export async function GET(_: Request, { params }: { params: Promise<{ applicationId: string }> }) {
  const user = await currentUser();
  if (!user) return Response.json({ error: 'forbidden' }, { status: 403 });
  const { applicationId } = await params;
  const value = await applicationById(user.id, applicationId);
  if (!value.application) return Response.json({ error: 'not_found' }, { status: 404 });
  return Response.json(value);
}

export async function PATCH(request: Request, { params }: { params: Promise<{ applicationId: string }> }) {
  const user = await currentUser();
  if (!user) return Response.json({ error: 'forbidden' }, { status: 403 });
  const parsed = updateSchema.safeParse(await request.json().catch(() => null));
  if (!parsed.success) return Response.json({ error: 'invalid_request' }, { status: 400 });
  const { applicationId } = await params;
  if (parsed.data.action === 'status') {
    await appendManualStatus(user.id, applicationId, parsed.data.status, parsed.data.occurredAt);
  } else if (parsed.data.action === 'metadata') {
    const rows = await query(
      `update applications set company_norm=$1,company_display=$2,role_norm=$3,role_title=$4,source=$5,job_url=$6,note=$7
       where id=$8 and user_id=$9 returning id`,
      [normalizeEntity(parsed.data.company), parsed.data.company, parsed.data.role ? normalizeEntity(parsed.data.role) : null,
        parsed.data.role, parsed.data.source, parsed.data.jobUrl, parsed.data.note, applicationId, user.id],
    );
    if (!rows.length) return Response.json({ error: 'not_found' }, { status: 404 });
  } else {
    await transaction(async (client) => {
      const updated = await client.query(
        `update applications
         set archived=$1
         where id=$2 and user_id=$3
         returning id`,
        [parsed.data.action !== 'restore', applicationId, user.id],
      );
      if (!updated.rowCount) throw new Error('application not found');

      if (parsed.data.action === 'not_application') {
        await client.query(
          `update llm_extractions le
           set review_state='dismissed'
           from application_events ae
           where ae.application_id=$1 and ae.llm_extraction_id=le.id`,
          [applicationId],
        );
      }
    });
  }
  return Response.json({ updated: true });
}
