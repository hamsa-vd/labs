'use client';

import { Button } from '@labs/design/arey';
import { useRouter } from 'next/navigation';
import { useState } from 'react';

export function ArchiveApplicationButton({
  applicationId,
  action,
  children,
}: Readonly<{
  applicationId: string;
  action: 'archive' | 'not_application';
  children: string;
}>) {
  const [busy, setBusy] = useState(false);
  const router = useRouter();

  async function update() {
    if (action === 'not_application' && !window.confirm('Mark this as never an application? Its events stay in the audit history.')) return;
    setBusy(true);
    const response = await fetch(`/api/v1/applications/${applicationId}`, {
      method: 'PATCH',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ action }),
    });
    setBusy(false);
    if (response.ok) router.push('/applications');
  }

  return <Button onClick={update} loading={busy}>{children}</Button>;
}
