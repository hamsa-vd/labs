import { google } from 'googleapis';
import { decryptStoredToken } from '@/security/token-crypto';

export const GMAIL_READONLY_SCOPE = 'https://www.googleapis.com/auth/gmail.readonly';

export function oauthClient() {
  const { GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_OAUTH_REDIRECT_URI } = process.env;
  if (!GOOGLE_CLIENT_ID || !GOOGLE_CLIENT_SECRET || !GOOGLE_OAUTH_REDIRECT_URI) {
    throw new Error('Google OAuth is not configured');
  }
  return new google.auth.OAuth2(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_OAUTH_REDIRECT_URI);
}

export function gmailForEncryptedToken(value: { ciphertext: Buffer; nonce: Buffer; keyVersion: number }) {
  return google.gmail({ version: 'v1', auth: oauthForEncryptedToken(value) });
}

export function oauthForEncryptedToken(value: { ciphertext: Buffer; nonce: Buffer; keyVersion: number }) {
  const auth = oauthClient();
  auth.setCredentials({ refresh_token: decryptStoredToken(value) });
  return auth;
}

export function decodeGmailBody(data?: string | null): string {
  return data ? Buffer.from(data, 'base64url').toString('utf8') : '';
}

export function messageHtml(payload: { mimeType?: string | null; body?: { data?: string | null }; parts?: unknown[] } | null | undefined): string {
  if (!payload) return '';
  if (payload.mimeType === 'text/html' && payload.body?.data) return decodeGmailBody(payload.body.data);
  if (payload.mimeType === 'text/plain' && payload.body?.data) {
    const text = decodeGmailBody(payload.body.data).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;');
    return `<pre>${text}</pre>`;
  }
  for (const part of (payload.parts ?? []) as Array<typeof payload>) {
    const found = messageHtml(part);
    if (found) return found;
  }
  return '';
}
