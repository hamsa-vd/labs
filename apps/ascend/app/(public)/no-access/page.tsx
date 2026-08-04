import Link from 'next/link';
import { Card } from '@labs/design/arey';
import { PublicHeader } from '@/ui/public-header';

export default function NoAccessPage() {
  return <div className="ascend-public"><PublicHeader/><main className="ascend-page ascend-page--narrow"><div className="ascend-eyebrow">Invite only</div><h1 className="ascend-title">This Google account does not have access</h1><p className="ascend-lede">Your identity was verified, but the email address is not active in Ascend’s allowlist.</p><div style={{marginTop:'var(--space-8)'}}><Card title="Need access?"><p>Request an invite using the same Google email address. Access is added manually after review.</p><Link className="ascend-link-button ascend-link-button--primary" href="/welcome">Request access</Link></Card></div></main></div>;
}
