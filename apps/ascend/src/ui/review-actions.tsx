'use client';

import { Button } from '@labs/design/arey';
import { FormEvent, useState } from 'react';
import { useRouter } from 'next/navigation';
import { EvidenceButton } from './evidence-button';

export function ReviewActions({
  id,
  hasEvidence,
  initialCompany,
  initialRole,
  initialEventType,
}: {
  id: string;
  hasEvidence: boolean;
  initialCompany: string;
  initialRole: string;
  initialEventType: string;
}) {
  const [busy, setBusy] = useState(false);
  const [editing, setEditing] = useState(false);
  const router = useRouter();

  async function act(action: 'confirm' | 'correct' | 'dismiss' | 'split', corrected?: Record<string, unknown>) {
    setBusy(true);
    const response = await fetch(`/api/v1/review/${id}/resolve`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ action, corrected }),
    });
    setBusy(false);
    if (response.ok) router.refresh();
  }

  function correct(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    void act('correct', {
      company: form.get('company'),
      roleTitle: form.get('roleTitle'),
      eventType: form.get('eventType'),
    });
  }

  return (
    <div className="ascend-stack">
      <div className="ascend-actions">
        <Button variant="primary" loading={busy} onClick={() => act('confirm')}>Confirm</Button>
        <Button onClick={() => setEditing((value) => !value)}>Correct</Button>
        <Button onClick={() => act('split')}>New application</Button>
        <Button onClick={() => act('dismiss')}>Not job related</Button>
        {hasEvidence && <EvidenceButton reviewId={id} />}
      </div>
      {editing && (
        <form className="ascend-form" onSubmit={correct}>
          <div className="ascend-form-grid">
            <label className="ascend-label">Company<input name="company" required defaultValue={initialCompany} /></label>
            <label className="ascend-label">Role<input name="roleTitle" defaultValue={initialRole} /></label>
            <label className="ascend-label">Event
              <select name="eventType" required defaultValue={initialEventType}>
                <option value="applied">Applied</option><option value="acknowledged">Acknowledged</option>
                <option value="assessment">Assessment</option><option value="interview_invite">Interview invite</option>
                <option value="interview_scheduled">Interview scheduled</option><option value="offer">Offer</option>
                <option value="rejected">Rejected</option><option value="withdrawn">Withdrawn</option>
              </select>
            </label>
          </div>
          <Button variant="primary" type="submit" loading={busy}>Save correction</Button>
        </form>
      )}
    </div>
  );
}
