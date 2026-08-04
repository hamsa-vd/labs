import { randomBytes } from 'node:crypto';
import { describe, expect, it } from 'vitest';
import { decryptStoredToken, decryptToken, encryptStoredToken, encryptToken, tokenKeyring } from './token-crypto';

describe('token encryption', () => {
  it('round-trips with AES-256-GCM and rejects the wrong key', () => {
    const key = randomBytes(32).toString('base64');
    const encrypted = encryptToken('refresh-token', key);
    expect(encrypted.ciphertext.toString()).not.toContain('refresh-token');
    expect(decryptToken(encrypted, key)).toBe('refresh-token');
    expect(() => decryptToken(encrypted, randomBytes(32).toString('base64'))).toThrow();
  });

  it('decrypts older ciphertext after the active key rotates', () => {
    const first = randomBytes(32).toString('base64');
    const second = randomBytes(32).toString('base64');
    const keys = JSON.stringify({ 1: first, 2: second });
    const oldValue = encryptStoredToken('old-refresh-token', {
      TOKEN_ENCRYPTION_KEYS: keys,
      TOKEN_ENCRYPTION_ACTIVE_VERSION: '1',
    });
    const rotatedEnvironment = {
      TOKEN_ENCRYPTION_KEYS: keys,
      TOKEN_ENCRYPTION_ACTIVE_VERSION: '2',
    };

    expect(tokenKeyring(rotatedEnvironment).activeVersion).toBe(2);
    expect(decryptStoredToken(oldValue, rotatedEnvironment)).toBe('old-refresh-token');
    expect(encryptStoredToken('new-refresh-token', rotatedEnvironment).keyVersion).toBe(2);
  });
});
