'use client';

import { Button } from '@labs/design/arey';
import { useState } from 'react';

export function EvidenceButton({ eventId, reviewId }: { eventId?: string; reviewId?: string }) {
  const [evidence, setEvidence] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  async function load() {
    setLoading(true);
    const path = eventId ? `/api/v1/events/${eventId}/evidence` : `/api/v1/review/${reviewId}/evidence`;
    const response = await fetch(path, { cache: 'no-store' });
    const body = await response.json();
    setEvidence(response.ok ? body.evidence : 'Evidence is no longer available.');
    setLoading(false);
  }
  return <div>{evidence ? <blockquote style={{ margin: 'var(--space-3) 0 0', padding: 'var(--space-3)', background: 'var(--bg-inset)', borderRadius: 'var(--radius-control)', font: 'var(--type-code)', color: 'var(--text-secondary)' }}>{evidence}</blockquote> : <Button size="sm" variant="ghost" loading={loading} onClick={load}>Show evidence</Button>}</div>;
}
