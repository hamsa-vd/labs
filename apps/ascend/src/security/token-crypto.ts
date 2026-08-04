import { createCipheriv, createDecipheriv, randomBytes } from 'node:crypto';

export interface EncryptedToken { ciphertext: Buffer; nonce: Buffer; keyVersion: number }

interface TokenKeyring {
  activeVersion: number;
  keys: Map<number, string>;
}

function keyFromBase64(encoded: string): Buffer {
  const key = Buffer.from(encoded, 'base64');
  if (key.length !== 32) throw new Error('TOKEN_ENCRYPTION_KEY must decode to exactly 32 bytes');
  return key;
}

export function encryptToken(token: string, encodedKey: string, keyVersion = 1): EncryptedToken {
  const nonce = randomBytes(12);
  const cipher = createCipheriv('aes-256-gcm', keyFromBase64(encodedKey), nonce);
  const encrypted = Buffer.concat([cipher.update(token, 'utf8'), cipher.final()]);
  const tag = cipher.getAuthTag();
  return { ciphertext: Buffer.concat([encrypted, tag]), nonce, keyVersion };
}

export function decryptToken(value: EncryptedToken, encodedKey: string): string {
  const tag = value.ciphertext.subarray(value.ciphertext.length - 16);
  const encrypted = value.ciphertext.subarray(0, -16);
  const decipher = createDecipheriv('aes-256-gcm', keyFromBase64(encodedKey), value.nonce);
  decipher.setAuthTag(tag);
  return Buffer.concat([decipher.update(encrypted), decipher.final()]).toString('utf8');
}

type TokenEnvironment = Record<string, string | undefined>;

export function tokenKeyring(environment: TokenEnvironment = process.env): TokenKeyring {
  const keys = new Map<number, string>();
  if (environment.TOKEN_ENCRYPTION_KEYS) {
    const parsed = JSON.parse(environment.TOKEN_ENCRYPTION_KEYS) as Record<string, unknown>;
    for (const [version, key] of Object.entries(parsed)) {
      const numericVersion = Number(version);
      if (!Number.isInteger(numericVersion) || numericVersion < 1 || typeof key !== 'string') {
        throw new Error('TOKEN_ENCRYPTION_KEYS must map positive integer versions to base64 keys');
      }
      keyFromBase64(key);
      keys.set(numericVersion, key);
    }
  } else if (environment.TOKEN_ENCRYPTION_KEY) {
    keyFromBase64(environment.TOKEN_ENCRYPTION_KEY);
    keys.set(1, environment.TOKEN_ENCRYPTION_KEY);
  }

  const activeVersion = Number(environment.TOKEN_ENCRYPTION_ACTIVE_VERSION ?? 1);
  if (!Number.isInteger(activeVersion) || !keys.has(activeVersion)) {
    throw new Error(`No token encryption key configured for active version ${activeVersion}`);
  }
  return { activeVersion, keys };
}

export function encryptStoredToken(token: string, environment: TokenEnvironment = process.env): EncryptedToken {
  const keyring = tokenKeyring(environment);
  return encryptToken(token, keyring.keys.get(keyring.activeVersion)!, keyring.activeVersion);
}

export function decryptStoredToken(value: EncryptedToken, environment: TokenEnvironment = process.env): string {
  const key = tokenKeyring(environment).keys.get(value.keyVersion);
  if (!key) throw new Error(`No token encryption key configured for stored version ${value.keyVersion}`);
  return decryptToken(value, key);
}
