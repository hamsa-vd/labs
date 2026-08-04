import { evidenceResponse, type EvidenceRecord } from '@/application/evidence-service';
import { currentUser } from '@/auth/access';
import { query } from '@/infrastructure/database';

export const dynamic = 'force-dynamic';

export async function GET(_: Request, { params }: { params: Promise<{ eventId: string }> }) {
  const user = await currentUser();
  if (!user) return Response.json({ error: 'forbidden' }, { status: 403, headers: { 'cache-control': 'no-store' } });
  const rows = await query<EvidenceRecord>(
    `select rm.gmail_message_id,rm.content_sha256,rm.sanitizer_version,le.evidence_sha256,le.evidence_offset,le.evidence_length,
       ga.refresh_token_ciphertext,ga.refresh_token_nonce,ga.key_version
     from application_events e join applications a on a.id=e.application_id join raw_messages rm on rm.id=e.raw_message_id
     join llm_extractions le on le.id=e.llm_extraction_id join gmail_accounts ga on ga.id=rm.account_id
     where e.id=$1 and a.user_id=$2`, [(await params).eventId, user.id],
  );
  return evidenceResponse(rows[0]);
}
