import { describe, expect, it } from 'vitest';
import { prefilterMessage } from './prefilter';

describe('prefilterMessage', () => {
  it('classifies a known ATS without relying on the subject', () => {
    const result = prefilterMessage({ fromAddress: 'notifications@eu.greenhouse.io', subject: 'Hello' });
    expect(result).toMatchObject({ score: 3, shouldClassify: true, source: 'greenhouse' });
  });

  it('allows a strong subject from a direct sender', () => {
    expect(prefilterMessage({ fromAddress: 'jobs@example.com', subject: 'Next steps for your application' }).shouldClassify).toBe(true);
  });

  it('hard-rejects LinkedIn job alerts and newsletters', () => {
    expect(prefilterMessage({ fromAddress: 'noreply@linkedin.com', subject: 'Your job alert' }).score).toBe(0);
    expect(prefilterMessage({ fromAddress: 'hello@example.com', subject: 'Weekly news', hasListUnsubscribe: true }).score).toBe(0);
  });
});
