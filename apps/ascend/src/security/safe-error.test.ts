import { describe, expect, it } from 'vitest';
import { isCredentialFailure, safeOperationalError } from './safe-error';

describe('privacy-safe operational errors', () => {
  it('classifies credential failures without preserving the source message', () => {
    const error = new Error('invalid_grant for person@example.com token secret-value');
    expect(isCredentialFailure(error)).toBe(true);
    expect(safeOperationalError(error)).toBe('oauth_refresh_failed');
  });

  it('does not echo unexpected model-derived text', () => {
    const safe = safeOperationalError(new Error('evidence: full private email quote'));
    expect(safe).toBe('Error_operation_failed');
    expect(safe).not.toContain('private email');
  });
});
