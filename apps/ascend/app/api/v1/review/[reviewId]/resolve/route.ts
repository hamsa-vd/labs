import { z } from 'zod';
import { currentUser } from '@/auth/access';
import { applicationStatuses, isApplicationStatus } from '@/domain/application-event';
import { normalizeEntity } from '@/domain/normalization';
import { transaction } from '@/infrastructure/database';

const correctionSchema = z.object({
  company: z.string().trim().min(1).max(80),
  roleTitle: z.string().trim().max(80).nullable().optional(),
  eventType: z.enum(applicationStatuses),
  occurredAtHint: z.iso.datetime().nullable().optional(),
  scheduledAt: z.iso.datetime().nullable().optional(),
  deadlineAt: z.iso.datetime().nullable().optional(),
}).strict();
const resolutionSchema = z.object({
  action: z.enum(['confirm', 'correct', 'dismiss', 'split']),
  corrected: correctionSchema.optional(),
}).superRefine((value, context) => {
  if (value.action === 'correct' && !value.corrected) context.addIssue({ code: 'custom', message: 'corrected values are required' });
});

export async function POST(request: Request, { params }: { params: Promise<{ reviewId: string }> }) {
  const user = await currentUser();
  if (!user) return Response.json({ error: 'forbidden' }, { status: 403 });
  const parsed = resolutionSchema.safeParse(await request.json().catch(() => null));
  if (!parsed.success) return Response.json({ error: 'invalid_request' }, { status: 400 });
  const reviewId = (await params).reviewId;
  await transaction(async (client) => {
    const owned = await client.query<{ id: string; output: Record<string, unknown>; raw_message_id: string; internal_date: Date; source: string | null; model: string; prompt_version: number }>(
      `select le.id,le.output,le.raw_message_id,le.model,le.prompt_version,rm.internal_date,rm.source from llm_extractions le join raw_messages rm on rm.id=le.raw_message_id
       join gmail_accounts ga on ga.id=rm.account_id where le.id=$1 and ga.user_id=$2 for update`, [reviewId, user.id],
    );
    if (!owned.rowCount) throw new Error('review not found');
    const state = parsed.data.action === 'dismiss' ? 'dismissed' : parsed.data.action === 'correct' ? 'corrected' : 'confirmed';
    await client.query(`update llm_extractions set review_state=$2 where id=$1`, [reviewId, state]);
    if (parsed.data.action === 'correct') await client.query(
      `insert into corrections(llm_extraction_id,user_id,corrected,before_values,after_values,model,prompt_version)
       values ($1,$2,$3,$4,$5,$6,$7)`,
      [reviewId, user.id, parsed.data.corrected ?? {}, owned.rows[0]?.output ?? {},
        { ...(owned.rows[0]?.output ?? {}), ...(parsed.data.corrected ?? {}) }, owned.rows[0]?.model, owned.rows[0]?.prompt_version],
    );
    if (parsed.data.action === 'dismiss') return;

    const extraction = { ...owned.rows[0]?.output, ...(parsed.data.corrected ?? {}) };
    const company = typeof extraction.company === 'string' ? extraction.company.trim() : '';
    const role = typeof extraction.roleTitle === 'string' ? extraction.roleTitle.trim() : null;
    const eventType = typeof extraction.eventType === 'string' ? extraction.eventType : '';
    if (!company || !isApplicationStatus(eventType as never)) throw new Error('review does not contain an application event');
    const companyNorm = normalizeEntity(company);
    const roleNorm = role ? normalizeEntity(role) : null;
    let applicationId: string | undefined;
    if (parsed.data.action !== 'split') {
      const match = await client.query<{ id: string }>(
        `select id from applications where user_id=$1 and not archived and similarity(company_norm,$2)>0.6
         order by case when $3::text is null then 0 else similarity(coalesce(role_norm,''),$3) end desc,status_as_of desc limit 1`,
        [user.id, companyNorm, roleNorm],
      );
      applicationId = match.rows[0]?.id;
    }
    const occurredAt = typeof extraction.occurredAtHint === 'string' && !Number.isNaN(Date.parse(extraction.occurredAtHint))
      ? new Date(extraction.occurredAtHint) : owned.rows[0]?.internal_date ?? new Date();
    if (!applicationId) {
      const inserted = await client.query<{ id: string }>(
        `insert into applications(user_id,company_norm,company_display,role_title,role_norm,source,first_seen_at,current_status,status_as_of,origin)
         values ($1,$2,$3,$4,$5,$6,$7,$8,$7,'gmail') returning id`,
        [user.id,companyNorm,company,role,roleNorm,owned.rows[0]?.source??'direct',occurredAt,eventType],
      );
      applicationId = inserted.rows[0]?.id;
    }
    await client.query(
      `insert into application_events(application_id,raw_message_id,llm_extraction_id,event_type,occurred_at,scheduled_at,deadline_at,source,created_by)
       values ($1,$2,$3,$4,$5,$6,$7,$8,$9) on conflict (llm_extraction_id) where llm_extraction_id is not null do nothing`,
      [applicationId,owned.rows[0]?.raw_message_id,reviewId,eventType,occurredAt,
        typeof extraction.scheduledAt==='string'?extraction.scheduledAt:null,
        typeof extraction.deadlineAt==='string'?extraction.deadlineAt:null,
        parsed.data.action==='correct'?'manual':'llm',parsed.data.action==='correct'?user.id:null],
    );
    await client.query(`select refresh_application_projection($1)`,[applicationId]);
  });
  return Response.json({ resolved: true });
}
