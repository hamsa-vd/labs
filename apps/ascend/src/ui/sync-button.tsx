'use client';
import { Button } from '@labs/design/arey';
import { useState } from 'react';

export function SyncButton() {
  const [state, setState] = useState<'idle'|'loading'|'queued'>('idle');
  async function sync() {
    setState('loading');
    const response = await fetch('/api/v1/sync-jobs', { method: 'POST' });
    setState(response.ok ? 'queued' : 'idle');
  }
  return <Button size="sm" variant="primary" iconLeft="arrows-clockwise" loading={state === 'loading'} onClick={sync}>{state === 'queued' ? 'Sync queued' : 'Sync now'}</Button>;
}
