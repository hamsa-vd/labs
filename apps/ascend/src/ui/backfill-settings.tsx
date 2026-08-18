'use client';

import { Button } from '@labs/design/arey';
import { useRouter } from 'next/navigation';
import { useState } from 'react';

const WINDOWS = [
  { days: 30, label: 'Last 30 days' },
  { days: 90, label: 'Last 90 days' },
  { days: 365, label: 'Last 1 year' },
  { days: 730, label: 'Last 2 years' },
  { days: 1460, label: 'Last 4 years' },
] as const;

export function BackfillSettings({ initialDays }: { initialDays: number }) {
  const [days, setDays] = useState(String(initialDays));
  const [state, setState] = useState<'idle' | 'saving' | 'saved' | 'syncing'>('idle');
  const router = useRouter();

  async function save(andSync = false) {
    setState(andSync ? 'syncing' : 'saving');
    const response = await fetch('/api/v1/gmail-settings', {
      method: 'PATCH', headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ backfillDays: Number(days) }),
    });
    if (!response.ok) { setState('idle'); return; }
    if (andSync) {
      await fetch('/api/v1/sync-jobs', {
        method: 'POST', headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ mode: 'full' }),
      });
    }
    setState(andSync ? 'saved' : 'saved');
    router.refresh();
  }

  return <div className="ascend-form">
    <label className="ascend-label">Full sync window
      <select value={days} onChange={(event) => { setDays(event.target.value); setState('idle'); }}>
        {WINDOWS.map((option) => <option key={option.days} value={option.days}>{option.label}</option>)}
      </select>
    </label>
    <p className="ascend-meta">This affects full syncs only. Incremental syncs continue from Gmail&apos;s history cursor.</p>
    <div className="ascend-actions">
      <Button loading={state === 'saving'} onClick={() => save()}>Save window</Button>
      <Button variant="primary" loading={state === 'syncing'} onClick={() => save(true)}>Save and run full sync</Button>
      {state === 'saved' && <span className="ascend-meta">Saved</span>}
    </div>
  </div>;
}

