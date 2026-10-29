import 'server-only';
import type { ApplicationRecordStatus, ApplicationStatus } from '@/domain/application-event';
import type { ApplicationOrigin } from '@/domain/application';
import { applicationStage } from '@/domain/application';
import { normalizeEntity } from '@/domain/normalization';
import { databaseConfigured, query, transaction } from '@/infrastructure/database';
import { decodeCursor, encodeCursor } from './cursor';

export interface ApplicationListItem {
  id: string; company: string; role: string | null; status: ApplicationRecordStatus; stage: string | null;
  source: string | null; lastEventAt: Date; eventCount: number; origin: ApplicationOrigin;
  jobUrl: string | null; note: string | null;
}

export interface ApplicationPage { applications: ApplicationListItem[]; nextCursor: string | null }

const DEMO_APPLICATIONS: ApplicationListItem[] = [
  { id: 'demo-form3', company: 'Form3', role: 'Senior Engineer, Platform', status: 'offer', stage: 'offer', source: 'direct', lastEventAt: new Date('2026-08-03T09:14:00Z'), eventCount: 7, origin: 'gmail', jobUrl: null, note: null },
  { id: 'demo-monzo', company: 'Monzo', role: 'Senior Frontend Engineer', status: 'interview_invite', stage: 'interview', source: 'greenhouse', lastEventAt: new Date('2026-08-02T14:02:00Z'), eventCount: 4, origin: 'gmail', jobUrl: null, note: null },
  { id: 'demo-starling', company: 'Starling Bank', role: 'Engineer II, Mobile Web', status: 'assessment', stage: 'assessment', source: 'direct', lastEventAt: new Date('2026-08-02T13:52:00Z'), eventCount: 3, origin: 'gmail', jobUrl: null, note: null },
  { id: 'demo-wise', company: 'Wise', role: 'Engineer, Payments Platform', status: 'acknowledged', stage: 'acknowledged', source: 'workday', lastEventAt: new Date('2026-08-01T17:40:00Z'), eventCount: 2, origin: 'gmail', jobUrl: null, note: null },
  { id: 'demo-cleo', company: 'Cleo', role: 'Product Engineer, Web', status: 'applied', stage: 'applied', source: 'ashby', lastEventAt: new Date('2026-07-30T10:00:00Z'), eventCount: 1, origin: 'gmail', jobUrl: null, note: null },
];

export async function listApplicationsPage(userId: string, options: {
  includeClosed?: boolean; status?: string; source?: string; waitingOnUser?: boolean;
  lastDays?: number; cursor?: string | null; limit?: number;
} = {}): Promise<ApplicationPage> {
  const limit = Math.max(1, Math.min(options.limit ?? 50, 100));
  if (!databaseConfigured()) return { applications: DEMO_APPLICATIONS.slice(0, limit), nextCursor: null };
  const cursor = decodeCursor(options.cursor);
  const rows = await query<{
    id: string; company_display: string; role_title: string | null; current_status: ApplicationRecordStatus;
    source: string | null; last_event_at: Date; event_count: string; origin: ApplicationOrigin; job_url: string | null; note: string | null;
  }>(
    `with listed as (
       select a.id,a.company_display,a.role_title,a.current_status,a.source,a.origin,a.job_url,a.note,
         coalesce(max(e.occurred_at),a.status_as_of) last_event_at,count(e.id)::text event_count
       from applications a left join application_events e on e.application_id=a.id
       where a.user_id=$1 and not a.archived
         and ($2::boolean or a.current_status not in ('rejected','withdrawn'))
         and ($3::text is null or a.current_status=$3)
         and ($4::text is null or a.source=$4)
         and ($5::int is null or exists (
           select 1 from application_events recent
           where recent.application_id=a.id and recent.occurred_at >= now()-($5::int * interval '1 day')
         ))
         and (not $6::boolean or a.current_status in ('interview_invite','offer') or (
           a.current_status='assessment' and exists (
             select 1 from application_events attention
             where attention.application_id=a.id and attention.deadline_at is not null
           )
         ))
         and not exists (select 1 from application_merges m where m.source_application_id=a.id and m.undone_at is null)
       group by a.id
     )
     select * from listed
     where ($7::timestamptz is null or (last_event_at,id) < ($7,$8::uuid))
     order by last_event_at desc,id desc limit $9`,
    [userId, Boolean(options.includeClosed), options.status ?? null, options.source ?? null, options.lastDays ?? null,
      Boolean(options.waitingOnUser), cursor?.at ?? null, cursor?.id ?? null, limit + 1],
  );
  const pageRows = rows.slice(0, limit);
  const applications = pageRows.map((row) => ({
    id: row.id, company: row.company_display, role: row.role_title, status: row.current_status,
    stage: applicationStage(row.current_status), source: row.source, lastEventAt: row.last_event_at,
    eventCount: Number(row.event_count), origin: row.origin, jobUrl: row.job_url, note: row.note,
  }));
  const last = pageRows.at(-1);
  return { applications, nextCursor: rows.length > limit && last ? encodeCursor(last.last_event_at, last.id) : null };
}

export async function listApplications(userId: string, options: {
  includeClosed?: boolean; status?: string; source?: string; waitingOnUser?: boolean; lastDays?: number; limit?: number;
} = {}): Promise<ApplicationListItem[]> {
  return (await listApplicationsPage(userId, options)).applications;
}

export async function applicationById(userId: string, id: string) {
  if (!databaseConfigured()) return { application: DEMO_APPLICATIONS.find((item) => item.id === id) ?? null, events: [], merges: [] };
  const applicationRows = await query<{
    id: string; company_display: string; role_title: string | null; current_status: ApplicationRecordStatus; source: string | null;
    last_event_at: Date; event_count: string; origin: ApplicationOrigin; job_url: string | null; note: string | null;
  }>(
    `select a.id,a.company_display,a.role_title,a.current_status,a.source,a.origin,a.job_url,a.note,
       coalesce(max(e.occurred_at),a.status_as_of) last_event_at,count(e.id)::text event_count
     from applications a left join application_events e on e.application_id=a.id
     where a.user_id=$1 and a.id=$2 and not a.archived group by a.id`, [userId, id],
  );
  const row = applicationRows[0];
  const application = row ? {
    id: row.id, company: row.company_display, role: row.role_title, status: row.current_status,
    stage: applicationStage(row.current_status), source: row.source, lastEventAt: row.last_event_at,
    eventCount: Number(row.event_count), origin: row.origin, jobUrl: row.job_url, note: row.note,
  } : null;
  if (!application) return { application: null, events: [], merges: [] };
  const events = await query<{
    id: string; event_type: string; occurred_at: Date; scheduled_at: Date | null; deadline_at: Date | null;
    source: string; subject: string | null; confidence: string | null; reason: string | null; has_evidence: boolean;
  }>(
    `select e.id,e.event_type,e.occurred_at,e.scheduled_at,e.deadline_at,e.source,rm.subject,
       le.confidence::text,le.output->>'reason' reason,(le.evidence_offset is not null) has_evidence
     from application_events e join applications a on a.id=e.application_id
     left join raw_messages rm on rm.id=e.raw_message_id left join llm_extractions le on le.id=e.llm_extraction_id
     where a.user_id=$1 and e.application_id=$2 order by e.occurred_at desc`, [userId, id],
  );
  const merges = await query<{
    id: string; created_at: Date; source_application_id: string; target_application_id: string;
    source_company: string; source_role: string | null; target_company: string; target_role: string | null;
  }>(
    `select m.id,m.created_at,m.source_application_id,m.target_application_id,
       source.company_display source_company,source.role_title source_role,
       target.company_display target_company,target.role_title target_role
     from application_merges m join applications source on source.id=m.source_application_id
     join applications target on target.id=m.target_application_id
     where m.undone_at is null and source.user_id=$1 and target.user_id=$1 and ($2::uuid in (m.source_application_id,m.target_application_id))
     order by m.created_at desc`, [userId, id],
  );
  return { application, events, merges };
}

export async function createManualApplication(userId: string, input: {
  company: string; role: string; source: string; appliedAt: Date; status: ApplicationStatus; jobUrl?: string | null; note?: string | null;
}) {
  return transaction(async (client) => {
    const inserted = await client.query<{ id: string }>(
      `insert into applications(user_id,company_norm,company_display,role_title,role_norm,source,first_seen_at,
         current_status,status_as_of,origin,job_url,note)
       values ($1,$2,$3,$4,$5,$6,$7,$8,$7,'manual',$9,$10) returning id`,
      [userId, normalizeEntity(input.company), input.company.trim(), input.role.trim(), normalizeEntity(input.role),
        input.source, input.appliedAt, input.status, input.jobUrl ?? null, input.note ?? null],
    );
    const id = inserted.rows[0]?.id;
    await client.query(
      `insert into application_events(application_id,event_type,occurred_at,source,created_by) values ($1,$2,$3,'manual',$4)`,
      [id, input.status, input.appliedAt, userId],
    );
    return id;
  });
}

export async function appendManualStatus(userId: string, applicationId: string, status: ApplicationStatus, occurredAt: Date) {
  await transaction(async (client) => {
    const owned = await client.query(`select id from applications where id=$1 and user_id=$2`, [applicationId, userId]);
    if (!owned.rowCount) throw new Error('application not found');
    await client.query(`insert into application_events(application_id,event_type,occurred_at,source,created_by) values ($1,$2,$3,'manual',$4)`, [applicationId, status, occurredAt, userId]);
    await client.query(`select refresh_application_projection($1)`, [applicationId]);
  });
}

export async function mergeApplications(userId: string, sourceId: string, targetId: string) {
  return transaction(async (client) => {
    const owned = await client.query(`select id from applications where user_id=$1 and id=any($2::uuid[])`, [userId, [sourceId, targetId]]);
    if (owned.rowCount !== 2) throw new Error('applications not found');
    const result = await client.query<{ id: string }>(
      `insert into application_merges(source_application_id,target_application_id,created_by) values ($1,$2,$3) returning id`,
      [sourceId, targetId, userId],
    );
    return result.rows[0]?.id;
  });
}
