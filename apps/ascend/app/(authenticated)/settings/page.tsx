import { Badge, Card } from '@labs/design/arey';
import Link from 'next/link';
import { currentUser } from '@/auth/access';
import { databaseConfigured, query } from '@/infrastructure/database';
import { DeleteAccount, DisconnectGmailButton, PrivacyAcceptButton } from '@/ui/settings-actions';

export default async function SettingsPage() {
  const user = await currentUser();
  if (!user) return null;
  const account = databaseConfigured() ? (await query<{ gmail_address: string; status: string; last_synced_at: Date | null }>(
    `select gmail_address,status,last_synced_at from gmail_accounts where user_id=$1 limit 1`, [user.id],
  ))[0] : null;
  const currentNotice = process.env.PRIVACY_NOTICE_VERSION ?? '2026-08-03';
  const privacyCurrent = Boolean(user.privacyAcceptedAt && user.privacyNoticeVersion === currentNotice);

  return (
    <main className="ascend-page ascend-page--narrow">
      <div className="ascend-page-head"><div><div className="ascend-eyebrow">{user.email}</div><h1 className="ascend-title">Settings</h1></div></div>
      <div className="ascend-stack">
        <Card title="Privacy notice" description="Required before Gmail can be connected" action={privacyCurrent ? <Badge tone="success" dot>Accepted</Badge> : <Badge tone="warning">Required</Badge>}>
          <p>The current notice is version {currentNotice}.</p>
          <div className="ascend-actions">{!privacyCurrent && <PrivacyAcceptButton />}<Link className="ascend-link-button" href="/privacy">Read notice</Link></div>
        </Card>
        <Card title="Connected Gmail" description="Read-only access; messages are never changed" action={account ? <Badge tone={account.status === 'active' ? 'success' : 'warning'} dot>{account.status}</Badge> : <Badge>Not connected</Badge>}>
          {account ? <><div className="ascend-row"><span>Address</span><span className="ascend-meta">{account.gmail_address}</span></div><div className="ascend-row"><span>Last sync</span><span className="ascend-meta">{account.last_synced_at?.toLocaleString() ?? 'Pending'}</span></div><div className="ascend-actions"><Link className="ascend-link-button" href="/api/v1/oauth/gmail/start">Reconnect</Link><DisconnectGmailButton /></div></> : <Link className="ascend-link-button ascend-link-button--primary" href="/api/v1/oauth/gmail/start">Connect Gmail</Link>}
        </Card>
        <Card title="Classifier"><div className="ascend-row"><span>Model</span><span className="ascend-meta">{process.env.OLLAMA_MODEL ?? 'qwen3:8b'}</span></div><div className="ascend-row"><span>Prompt version</span><span className="ascend-meta">v{process.env.PROMPT_VERSION ?? '1'}</span></div><div className="ascend-row"><span>Temperature</span><span className="ascend-meta">0</span></div></Card>
        <Card title="Your data"><div className="ascend-actions"><a className="ascend-link-button" href="/api/v1/export">Export JSON</a><a className="ascend-link-button" href="/api/v1/export?format=csv&amp;dataset=applications">Applications CSV</a><a className="ascend-link-button" href="/api/v1/export?format=csv&amp;dataset=events">Events CSV</a></div></Card>
        <Card title="Delete account" description="This permanently removes tracker data and the stored Gmail credential"><DeleteAccount email={user.email} /></Card>
      </div>
    </main>
  );
}
