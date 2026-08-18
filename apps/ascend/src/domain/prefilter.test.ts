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

  it('allows plain interview subjects', () => {
    expect(prefilterMessage({ fromAddress: 'recruiter@example.com', subject: 'Interview at Northwind' }).shouldClassify).toBe(true);
  });

  it('allows rejection and application-update wording', () => {
    for (const subject of [
      'Unfortunately, we will not be moving forward',
      'Update regarding your application',
      'Application status update',
    ]) {
      expect(prefilterMessage({ fromAddress: 'careers@example.com', subject }).shouldClassify).toBe(true);
    }
  });

  it('recognizes recruiter and ATS senders such as Multiverse without a matching subject', () => {
    expect(prefilterMessage({ fromAddress: 'talent@multiverse.io', subject: 'Hello' })).toMatchObject({
      shouldClassify: true,
      source: 'multiverse',
    });
  });

  it('hard-rejects LinkedIn job alerts and newsletters', () => {
    expect(prefilterMessage({ fromAddress: 'noreply@linkedin.com', subject: 'Your job alert' }).score).toBe(0);
    expect(prefilterMessage({ fromAddress: 'hello@example.com', subject: 'Weekly news', hasListUnsubscribe: true }).score).toBe(0);
  });
});
