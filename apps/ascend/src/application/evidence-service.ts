import 'server-only';
import { createHash } from 'node:crypto';
import type { QueryResultRow } from 'pg';
import { sanitizeMessageHtmlVersion } from '@/domain/message-sanitizer';
import { gmailForEncryptedToken, messageHtml } from '@/infrastructure/gmail-client';

export interface EvidenceRecord extends QueryResultRow {
  gmail_message_id: string;
  content_sha256: string;
  sanitizer_version: number;
  evidence_sha256: string;
  evidence_offset: number;
  evidence_length: number;
  refresh_token_ciphertext: Buffer;
  refresh_token_nonce: Buffer;
  key_version: number;
}

export async function evidenceResponse(row: EvidenceRecord | undefined): Promise<Response> {
  const headers = { 'cache-control': 'no-store, max-age=0' };
  if (!row) {
    return Response.json({ error: 'evidence_unavailable' }, { status: 404, headers });
  }
  const gmail = gmailForEncryptedToken({
    ciphertext: row.refresh_token_ciphertext,
    nonce: row.refresh_token_nonce,
    keyVersion: row.key_version,
  });
  const message = await gmail.users.messages.get({ userId: 'me', id: row.gmail_message_id, format: 'full' });
  const cleaned = sanitizeMessageHtmlVersion(messageHtml(message.data.payload), row.sanitizer_version);
  if (!cleaned) return Response.json({ error: 'evidence_unavailable' }, { status: 404, headers });
  const evidence = cleaned.text.slice(row.evidence_offset, row.evidence_offset + row.evidence_length);
  const valid = cleaned.contentSha256 === row.content_sha256
    && createHash('sha256').update(evidence).digest('hex') === row.evidence_sha256;
  return valid ? Response.json({ evidence }, { headers })
    : Response.json({ error: 'evidence_changed' }, { status: 409, headers });
}
