'use client';

import { Button } from '@labs/design/arey';
import { useState } from 'react';
import { useRouter } from 'next/navigation';

export function UndoMergeButton({ mergeId }: { mergeId: string }) {
  const [busy, setBusy] = useState(false);
  const router = useRouter();
  async function undo() {
    setBusy(true);
    const response = await fetch(`/api/v1/application-merges/${mergeId}/undo`, { method: 'POST' });
    setBusy(false);
    if (response.ok) router.refresh();
  }
  return <Button size="sm" loading={busy} onClick={undo}>Undo merge</Button>;
}
