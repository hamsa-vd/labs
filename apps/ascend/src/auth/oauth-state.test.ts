import { describe, expect, it } from 'vitest';
import { createOAuthState, hashOAuthState, safeEqual } from './oauth-state';

describe('OAuth state and PKCE', () => {
  it('creates independent high-entropy state and verifier values', () => {
    const first = createOAuthState();
    const second = createOAuthState();
    expect(first.state).not.toBe(second.state);
    expect(first.verifier).not.toBe(first.state);
    expect(first.challenge).not.toBe(first.verifier);
  });

  it('rejects missing, changed and different-length state', () => {
    expect(safeEqual('expected', 'expected')).toBe(true);
    expect(safeEqual('expected', 'changed!')).toBe(false);
    expect(safeEqual('expected', 'short')).toBe(false);
    expect(safeEqual(undefined, 'expected')).toBe(false);
  });

  it('stores only a fixed-length state hash', () => {
    expect(hashOAuthState('browser-state')).toHaveLength(64);
    expect(hashOAuthState('browser-state')).not.toContain('browser-state');
  });
});
