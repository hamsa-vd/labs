'use client';

import { Button } from '@labs/design/arey';
import { FormEvent, useState } from 'react';
import { useRouter } from 'next/navigation';

export function ApplicationMetadataForm({ application }: { application: {
  id: string; company: string; role: string | null; source: string | null; jobUrl: string | null; note: string | null;
} }) {
  const [busy, setBusy] = useState(false);
  const router = useRouter();
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    const form = new FormData(event.currentTarget);
    const response = await fetch(`/api/v1/applications/${application.id}`, {
      method: 'PATCH',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({
        action: 'metadata',
        company: form.get('company'),
        role: form.get('role') || null,
        source: form.get('source'),
        jobUrl: form.get('jobUrl') || null,
        note: form.get('note') || null,
      }),
    });
    setBusy(false);
    if (response.ok) router.refresh();
  }
  return <form className="ascend-form" onSubmit={submit}><label className="ascend-label">Company<input name="company" required maxLength={80} defaultValue={application.company} /></label><label className="ascend-label">Role<input name="role" maxLength={80} defaultValue={application.role ?? ''} /></label><label className="ascend-label">Source<input name="source" required maxLength={40} defaultValue={application.source ?? 'manual'} /></label><label className="ascend-label">Job URL<input name="jobUrl" type="url" defaultValue={application.jobUrl ?? ''} /></label><label className="ascend-label">Note<textarea name="note" maxLength={1000} defaultValue={application.note ?? ''} /></label><Button type="submit" loading={busy}>Save identity</Button></form>;
}
