import { Badge, Card } from '@labs/design/arey';
import { serviceHealth } from '@/application/health-service';
import { PublicHeader } from '@/ui/public-header';

export const dynamic = 'force-dynamic';

export default async function StatusPage() {
  const health = await serviceHealth();
  const operational = health.status === 'ok';
  return (
    <div className="ascend-public">
      <PublicHeader />
      <main className="ascend-page ascend-page--narrow">
        <div className="ascend-eyebrow">Service status</div>
        <h1 className="ascend-title">{operational ? 'Ascend is operating normally' : 'Ascend is experiencing a service issue'}</h1>
        <div style={{ marginTop: 'var(--space-8)' }}>
          <Card title="Current status" action={<Badge tone={operational ? 'success' : 'warning'} dot>{operational ? 'Operational' : 'Degraded'}</Badge>}>
            <p>The web application, database, and Gmail worker are checked without exposing account-specific details.</p>
            <div className="ascend-row"><span>Database</span><span className="ascend-meta">{health.database}</span></div>
            <div className="ascend-row"><span>Sync worker</span><span className="ascend-meta">{health.worker}</span></div>
            <p className="ascend-meta">Checked {new Date(health.checkedAt).toLocaleString()}</p>
          </Card>
        </div>
      </main>
    </div>
  );
}
