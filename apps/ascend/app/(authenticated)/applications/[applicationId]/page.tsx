import { Badge, Card } from '@labs/design/arey';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { applicationById } from '@/application/tracker-service';
import { currentUser } from '@/auth/access';
import { ApplicationActions } from '@/ui/application-actions';
import { ArchiveApplicationButton } from '@/ui/archive-application-button';
import { ApplicationMetadataForm } from '@/ui/application-metadata-form';
import { EvidenceButton } from '@/ui/evidence-button';
import { StatusBadge } from '@/ui/status-badge';
import { UndoMergeButton } from '@/ui/undo-merge-button';

export default async function ApplicationDetailPage({
  params,
}: Readonly<{ params: Promise<{ applicationId: string }> }>) {
  const user = await currentUser();
  if (!user) return null;
  const { applicationId } = await params;
  const { application, events, merges } = await applicationById(user.id, applicationId);
  if (!application) notFound();

  return (
    <main className="ascend-page">
      <Link className="ascend-link-button" href="/applications">Applications</Link>
      <div className="ascend-page-head" style={{ marginTop: 'var(--space-6)' }}>
        <div>
          <div className="ascend-eyebrow">{application.source ?? application.origin}</div>
          <h1 className="ascend-title">{application.company}</h1>
          <p className="ascend-lede">{application.role ?? 'Role unknown'}</p>
        </div>
        <StatusBadge status={application.status} />
      </div>

      <div className="ascend-grid-2">
        <Card title="Event history">
          {events.length ? events.map((event) => (
            <article className="ascend-event" key={event.id}>
              <time>{new Date(event.occurred_at).toLocaleString()}</time>
              <div>
                <div className="ascend-actions">
                  <Badge tone="outline" mono>{event.event_type}</Badge>
                  <span className="ascend-meta">{event.source}</span>
                </div>
                {event.subject && <h3 style={{ marginTop: 'var(--space-3)' }}>{event.subject}</h3>}
                {event.reason && <p>{event.reason}</p>}
                {event.has_evidence && <EvidenceButton eventId={event.id} />}
              </div>
            </article>
          )) : <div className="ascend-empty">No events recorded.</div>}
        </Card>

        <div className="ascend-stack">
          <Card title="Current state">
            <div className="ascend-row"><span>Status</span><StatusBadge status={application.status} /></div>
            <div className="ascend-row"><span>Events</span><span className="ascend-meta">{application.eventCount}</span></div>
            <div className="ascend-row"><span>Origin</span><span className="ascend-meta">{application.origin}</span></div>
          </Card>
          <Card title="Add a correction"><ApplicationActions id={application.id} /></Card>
          <Card title="Identity metadata"><ApplicationMetadataForm application={application} /></Card>
          {merges.length > 0 && <Card title="Merged applications">{merges.map((merge) => <div className="ascend-row" key={merge.id}><span>{merge.source_company} → {merge.target_company}</span><UndoMergeButton mergeId={merge.id} /></div>)}</Card>}
          {application.jobUrl && (
            <Card title="Job link"><a href={application.jobUrl} target="_blank" rel="noreferrer">Open original listing</a></Card>
          )}
          <Card title="Application actions">
            <div className="ascend-actions">
              <ArchiveApplicationButton applicationId={application.id} action="archive">Archive</ArchiveApplicationButton>
              <ArchiveApplicationButton applicationId={application.id} action="not_application">Never an application</ArchiveApplicationButton>
            </div>
            <p className="ascend-meta">These actions hide the application without rewriting its event history.</p>
          </Card>
        </div>
      </div>
    </main>
  );
}
