import { createHash, randomBytes } from 'node:crypto';

export function createOAuthState() {
  const state = randomBytes(24).toString('base64url');
  const verifier = randomBytes(48).toString('base64url');
  const challenge = createHash('sha256').update(verifier).digest('base64url');
  return { state, verifier, challenge };
}

export function safeEqual(left: string | undefined, right: string | null): boolean {
  if (!left || !right || left.length !== right.length) return false;
  let mismatch = 0;
  for (let index = 0; index < left.length; index += 1) mismatch |= left.charCodeAt(index) ^ right.charCodeAt(index);
  return mismatch === 0;
}

export function hashOAuthState(state: string): string {
  return createHash('sha256').update(state).digest('hex');
}
