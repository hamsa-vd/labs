import { Badge, Card, ProgressBar } from '@labs/design/arey';
import Link from 'next/link';
import { currentUser } from '@/auth/access';
import { listApplications } from '@/application/tracker-service';
import { databaseConfigured, query } from '@/infrastructure/database';

const stages = ['applied', 'acknowledged', 'assessment', 'interview', 'offer'] as const;

export default async function OverviewPage() {
  const user = await currentUser();
  if (!user) return null;
  const [allApplications, boardApplications, waitingApplications] = await Promise.all([
    listApplications(user.id, { limit: 100 }),
    listApplications(user.id, { lastDays: 90, limit: 100 }),
    listApplications(user.id, { waitingOnUser: true, limit: 100 }),
  ]);
  const account = databaseConfigured() ? (await query<{ status: string; last_synced_at: Date | null }>(
    `select status,last_synced_at from gmail_accounts where user_id=$1 limit 1`, [user.id],
  ))[0] : null;
  const queued = databaseConfigured() ? (await query<{ messages_scanned: number; candidates_found: number; events_created: number }>(
    `select messages_scanned,candidates_found,events_created from sync_jobs sj join gmail_accounts ga on ga.id=sj.account_id
     where ga.user_id=$1 and sj.status in ('queued','running') order by requested_at desc limit 1`, [user.id],
  ))[0] : null;
  const live = allApplications.filter((app) => ['acknowledged', 'assessment', 'interview_invite', 'interview_scheduled'].includes(app.status)).length;

  return (
    <main className="ascend-page ascend-overview-page">
      {account?.status === 'needs_reauth' && <div className="ascend-banner"><strong>Gmail needs reconnecting.</strong><Link className="ascend-link-button" href="/api/v1/oauth/gmail/start">Reconnect</Link></div>}
      <section className="ascend-overview-hero">
        <div className="ascend-overview-art" aria-hidden="true">
          <div className="ascend-overview-art-glass" />
          <div className="ascend-overview-art-disc" />
          <svg viewBox="0 0 340 340" fill="none" stroke="var(--text-primary)" strokeWidth="1.1" strokeLinecap="round">
            <path d="M28 236 C 78 150, 128 92, 188 62" strokeDasharray="1400" />
            <path d="M52 268 C 118 210, 176 148, 236 74" strokeDasharray="1400" />
            <path d="M196 44 C 214 52, 226 66, 232 84" strokeDasharray="1400" />
          </svg>
        </div>
        <div className="ascend-overview-copy">
          <div className="ascend-overview-kicker">
            <div className="ascend-eyebrow">{account ? `Last sync ${account.last_synced_at?.toLocaleString() ?? 'not completed'}` : 'Gmail not connected'}</div>
          </div>
          <h1 className="ascend-display">Good morning. Your applications are where you left them.</h1>
          <p className="ascend-lede">Deadlines and status changes come from an append-only history. Uncertain messages wait for review.</p>
          <div className="ascend-actions">
            {account ? <Link className="ascend-link-button" href="/applications">All applications</Link> : <Link className="ascend-link-button ascend-link-button--primary" href="/settings">Connect Gmail</Link>}
            <Link className="ascend-link-button" href="/review">Needs review</Link>
          </div>
          <div className="ascend-stats">
            <div className="ascend-stat"><strong>{allApplications.length}</strong><span>Applications tracked</span></div>
            <div className="ascend-stat"><strong>{live}</strong><span>Live conversations</span></div>
            <div className="ascend-stat"><strong>{waitingApplications.length}</strong><span>Waiting on you</span></div>
          </div>
        </div>
      </section>
      {queued && <Card title="First sync in progress" description={`${queued.messages_scanned} messages scanned · ${queued.candidates_found} candidates · ${queued.events_created} events`}><ProgressBar value={Math.min(95, Math.max(5, queued.messages_scanned / 10))} /></Card>}
      <div className="ascend-page-head"><div><div className="ascend-eyebrow">The board</div><h2 className="ascend-title">Every application, in the state it&apos;s actually in</h2></div><Badge tone="outline" mono>Last 90 days</Badge></div>
      <div className="ascend-board">
        {stages.map((stage) => {
          const items = boardApplications.filter((app) => app.stage === stage);
          return <section className="ascend-column" key={stage}><div className="ascend-column-head"><span>{stage[0].toUpperCase() + stage.slice(1)}</span><span className="ascend-meta">{items.length}</span></div><div className="ascend-card-stack">{items.map((app) => <Link className="ascend-app-card" href={`/applications/${app.id}`} key={app.id}><strong>{app.company}</strong><span>{app.role ?? 'Role unknown'}</span><span className="ascend-meta">{app.source ?? app.origin}</span></Link>)}{items.length === 0 && <div className="ascend-empty">No applications</div>}</div></section>;
        })}
      </div>
    </main>
  );
}
