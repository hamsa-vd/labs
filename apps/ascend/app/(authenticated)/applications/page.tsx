import { Button, Card } from '@labs/design/arey';
import Link from 'next/link';
import { currentUser } from '@/auth/access';
import { listApplicationsPage } from '@/application/tracker-service';
import { applicationStatuses } from '@/domain/application-event';
import { ApplicationsTable } from '@/ui/applications-table';
import { ManualApplicationForm } from '@/ui/manual-application-form';

interface ApplicationSearchParams {
  includeClosed?: string;
  status?: string;
  source?: string;
  waitingOnUser?: string;
  cursor?: string;
}

export default async function ApplicationsPage({ searchParams }: { searchParams: Promise<ApplicationSearchParams> }) {
  const user = await currentUser();
  if (!user) return null;
  const params = await searchParams;
  const includeClosed = params.includeClosed === 'true';
  const status = applicationStatuses.includes(params.status as (typeof applicationStatuses)[number]) ? params.status : undefined;
  const page = await listApplicationsPage(user.id, {
    includeClosed,
    status,
    source: params.source || undefined,
    waitingOnUser: params.waitingOnUser === 'true',
    cursor: params.cursor,
    limit: 25,
  }).catch((error: unknown) => {
    if (error instanceof Error && error.message === 'invalid_cursor') return { applications: [], nextCursor: null };
    throw error;
  });
  const next = new URLSearchParams();
  if (includeClosed) next.set('includeClosed', 'true');
  if (status) next.set('status', status);
  if (params.source) next.set('source', params.source);
  if (params.waitingOnUser === 'true') next.set('waitingOnUser', 'true');
  if (page.nextCursor) next.set('cursor', page.nextCursor);

  return (
    <main className="ascend-page">
      <div className="ascend-page-head">
        <div><div className="ascend-eyebrow">{page.applications.length} on this page</div><h1 className="ascend-title">Applications</h1></div>
        <ManualApplicationForm />
      </div>
      <Card title="Filters">
        <form className="ascend-filter-form" method="get">
          <label className="ascend-label">Status
            <select name="status" defaultValue={status ?? ''}>
              <option value="">All statuses</option>
              {applicationStatuses.map((value) => <option value={value} key={value}>{value.replace('_', ' ')}</option>)}
            </select>
          </label>
          <label className="ascend-label">Source<input name="source" defaultValue={params.source ?? ''} placeholder="greenhouse" /></label>
          <label className="ascend-check"><input name="waitingOnUser" type="checkbox" value="true" defaultChecked={params.waitingOnUser === 'true'} /> Waiting on you</label>
          <label className="ascend-check"><input name="includeClosed" type="checkbox" value="true" defaultChecked={includeClosed} /> Include closed</label>
          <Button type="submit">Apply filters</Button>
          <Link className="ascend-link-button" href="/applications">Clear</Link>
        </form>
      </Card>
      <Card padded={false} variant="flat">
        {page.applications.length ? <ApplicationsTable applications={page.applications} /> : <div className="ascend-empty">No applications match these filters.</div>}
      </Card>
      {page.nextCursor && <Link className="ascend-link-button" href={`/applications?${next}`}>Next page</Link>}
    </main>
  );
}
