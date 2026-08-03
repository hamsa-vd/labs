import { describe, expect, it } from 'vitest';
import type { ApplicationEvent, ApplicationEventType } from './application-event';
import { projectStatus } from './status-projection';

let sequence = 0;

function event(
  type: ApplicationEventType,
  occurredAt: string,
  source: 'llm' | 'manual' = 'llm',
): ApplicationEvent {
  sequence += 1;
  return {
    id: `event-${sequence}`,
    applicationId: 'application-1',
    rawMessageId: null,
    type,
    occurredAt: new Date(occurredAt),
    scheduledAt: null,
    deadlineAt: null,
    source,
    createdAt: new Date(occurredAt),
  };
}

describe('projectStatus', () => {
  it('returns null when there is no status-bearing event', () => {
    expect(projectStatus([])).toBeNull();
    expect(projectStatus([event('job_alert', '2026-07-01T09:00:00Z')])).toBeNull();
  });

  it('takes the latest event by occurrence, not by insertion order', () => {
    const status = projectStatus([
      event('interview_invite', '2026-07-10T09:00:00Z'),
      event('applied', '2026-07-01T09:00:00Z'),
    ]);
    expect(status).toBe('interview_invite');
  });

  it('does not regress when a delayed acknowledgement lands after an interview', () => {
    // The acknowledgement genuinely occurred first; it just arrived late.
    const status = projectStatus([
      event('applied', '2026-07-01T09:00:00Z'),
      event('interview_invite', '2026-07-10T09:00:00Z'),
      event('acknowledged', '2026-07-02T09:00:00Z'),
    ]);
    expect(status).toBe('interview_invite');
  });

  it('moves from offer to rejected when the offer is later withdrawn', () => {
    const status = projectStatus([
      event('offer', '2026-07-10T09:00:00Z'),
      event('rejected', '2026-07-15T09:00:00Z'),
    ]);
    expect(status).toBe('rejected');
  });

  it('does not regress out of a terminal state', () => {
    const status = projectStatus([
      event('rejected', '2026-07-10T09:00:00Z'),
      event('acknowledged', '2026-07-20T09:00:00Z'),
    ]);
    expect(status).toBe('rejected');
  });

  it('ignores event types that are not statuses', () => {
    const status = projectStatus([
      event('applied', '2026-07-01T09:00:00Z'),
      event('recruiter_outreach', '2026-07-05T09:00:00Z'),
      event('other', '2026-07-06T09:00:00Z'),
    ]);
    expect(status).toBe('applied');
  });

  it('prefers a manual correction over a model event at the same instant', () => {
    const status = projectStatus([
      event('offer', '2026-07-10T09:00:00Z', 'llm'),
      event('rejected', '2026-07-10T09:00:00Z', 'manual'),
    ]);
    expect(status).toBe('rejected');
  });
});
