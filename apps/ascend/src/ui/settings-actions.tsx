'use client';

import { Button } from '@labs/design/arey';
import { useRouter } from 'next/navigation';
import { useState } from 'react';

export function PrivacyAcceptButton() {
  const [busy, setBusy] = useState(false);
  const router = useRouter();
  async function accept() {
    setBusy(true);
    const response = await fetch('/api/v1/privacy/accept', { method: 'POST' });
    setBusy(false);
    if (response.ok) router.refresh();
  }
  return <Button variant="primary" loading={busy} onClick={accept}>Accept privacy notice</Button>;
}

export function DisconnectGmailButton() {
  const [busy, setBusy] = useState(false);
  const router = useRouter();
  async function disconnect() {
    if (!window.confirm('Disconnect Gmail and remove the stored credential? Tracker history will remain.')) return;
    setBusy(true);
    const response = await fetch('/api/v1/oauth/gmail', { method: 'DELETE' });
    setBusy(false);
    if (response.ok) router.refresh();
  }
  return <Button loading={busy} onClick={disconnect}>Disconnect</Button>;
}

export function DeleteAccount({ email }: { email: string }) {
  const [value, setValue] = useState('');
  const [busy, setBusy] = useState(false);
  async function remove() {
    setBusy(true);
    const response = await fetch('/api/v1/account', { method: 'DELETE', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ confirmation: value }) });
    if (response.ok) location.href = '/no-access'; else setBusy(false);
  }
  return <div className="ascend-form"><label className="ascend-label">Type {email} to confirm<input value={value} onChange={(event) => setValue(event.target.value)} /></label><Button variant="danger" disabled={value !== email} loading={busy} onClick={remove}>Delete account</Button></div>;
}
