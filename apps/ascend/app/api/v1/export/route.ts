import { currentUser } from '@/auth/access';
import { query } from '@/infrastructure/database';

function csv(rows: Record<string, unknown>[]): string {
  if (rows.length === 0) return '';
  const columns = Object.keys(rows[0]);
  const cell = (value: unknown) => {
    const text = value instanceof Date ? value.toISOString() : value == null ? '' : String(value);
    return `"${text.replaceAll('"', '""')}"`;
  };
  return [columns.map(cell).join(','), ...rows.map((row) => columns.map((column) => cell(row[column])).join(','))].join('\n') + '\n';
}

export async function GET(request: Request) {
  const user = await currentUser();
  if (!user) return Response.json({ error: 'forbidden' }, { status: 403 });
  const applications = await query<Record<string, unknown>>(
    `select company_display,role_title,source,first_seen_at,current_status,status_as_of,origin,job_url,note
     from applications where user_id=$1 order by first_seen_at desc`, [user.id],
  );
  const events = await query<Record<string, unknown>>(
    `select a.company_display,a.role_title,e.event_type,e.occurred_at,e.scheduled_at,e.deadline_at,e.source
     from application_events e join applications a on a.id=e.application_id where a.user_id=$1 order by e.occurred_at desc`, [user.id],
  );
  const url = new URL(request.url);
  if (url.searchParams.get('format') === 'csv') {
    const dataset = url.searchParams.get('dataset') === 'events' ? events : applications;
    const name = url.searchParams.get('dataset') === 'events' ? 'events' : 'applications';
    return new Response(csv(dataset), { headers: {
      'content-type': 'text/csv; charset=utf-8',
      'content-disposition': `attachment; filename="ascend-${name}.csv"`,
      'cache-control': 'no-store',
    } });
  }
  return Response.json({ exportedAt: new Date().toISOString(), applications, events }, {
    headers: { 'content-disposition': 'attachment; filename="ascend-export.json"', 'cache-control': 'no-store' },
  });
}
