import type { PoolClient } from 'pg';
import type { gmail_v1 } from 'googleapis';
import { isApplicationStatus } from '@/domain/application-event';
import { evaluateExtraction, type Extraction } from '@/domain/extraction';
import { locateEvidence, sanitizeMessageHtml } from '@/domain/message-sanitizer';
import { normalizeEntity } from '@/domain/normalization';
import { prefilterMessage } from '@/domain/prefilter';
import { database, transaction } from '@/infrastructure/database';
import { gmailForEncryptedToken, messageHtml } from '@/infrastructure/gmail-client';
import { OllamaClassifier } from '@/infrastructure/ollama-classifier';
import { isCredentialFailure, safeOperationalError } from '@/security/safe-error';

const BACKFILL_QUERY = `newer_than:2y -in:chats -in:spam (
  from:(greenhouse.io OR lever.co OR ashbyhq.com OR myworkday.com OR icims.com OR smartrecruiters.com OR workable.com OR teamtailor.com OR jobvite.com OR taleo.net OR successfactors.com OR breezy.hr OR recruitee.com OR pinpointhq.com OR bamboohr.com OR linkedin.com OR indeed.com OR otta.com)
  OR subject:("thank you for applying" OR "your application" OR "application received" OR "interview" OR "we regret" OR "moving forward" OR "next steps" OR "assessment" OR "offer")
)`;

interface AccountRow {
  id: string; user_id: string; gmail_address: string; refresh_token_ciphertext: Buffer;
  refresh_token_nonce: Buffer; key_version: number; history_id: string | null;
  last_synced_at: Date | null; timezone: string;
}

interface Counts { scanned: number; candidates: number; events: number; llmCalls: number; failed: number }

function header(message: gmail_v1.Schema$Message, name: string): string {
  return message.payload?.headers?.find((item) => item.name?.toLowerCase() === name.toLowerCase())?.value ?? '';
}

function fromAddress(value: string): string {
  return value.match(/<([^>]+)>/)?.[1] ?? value.trim();
}

function errorStatus(error: unknown): number | null {
  if (typeof error === 'object' && error && 'code' in error && typeof error.code === 'number') return error.code;
  return null;
}

function persistedOutput(extraction: Extraction): Record<string, unknown> {
  const safe: Record<string, unknown> = { ...extraction };
  delete safe.evidence;
  return safe;
}

async function resolveApplication(
  client: PoolClient,
  account: AccountRow,
  extraction: Extraction,
  source: string,
  occurredAt: Date,
): Promise<{ id: string; needsReview: boolean } | null> {
  if (!extraction.company || !isApplicationStatus(extraction.eventType)) return null;
  const companyNorm = normalizeEntity(extraction.company);
  const roleNorm = extraction.roleTitle ? normalizeEntity(extraction.roleTitle) : null;
  const matches = await client.query<{ id: string; role_norm: string | null; role_similarity: number }>(
    `select id, role_norm,case when $3::text is null then 0 else similarity(coalesce(role_norm,''), $3) end role_similarity
     from applications
     where user_id = $1 and not archived and current_status not in ('rejected','withdrawn')
       and similarity(company_norm, $2) > 0.6
     order by role_similarity desc,
              status_as_of desc limit 3`,
    [account.user_id, companyNorm, roleNorm],
  );
  const match = matches.rows[0];
  if (match && (roleNorm === null || Number(match.role_similarity) >= 0.45)) {
    return { id: match.id, needsReview: roleNorm === null };
  }
  if (roleNorm === null) return null;

  const inserted = await client.query<{ id: string }>(
    `insert into applications(user_id, company_norm, company_display, role_title, role_norm, source,
       first_seen_at, current_status, status_as_of, origin)
     values ($1,$2,$3,$4,$5,$6,$7,$8,$7,'gmail') returning id`,
    [account.user_id, companyNorm, extraction.company, extraction.roleTitle, roleNorm, source, occurredAt, extraction.eventType],
  );
  return inserted.rows[0] ? { id: inserted.rows[0].id, needsReview: roleNorm === null } : null;
}

async function processMessage(gmail: gmail_v1.Gmail, account: AccountRow, gmailMessageId: string, counts: Counts) {
  const metadata = await gmail.users.messages.get({
    userId: 'me', id: gmailMessageId, format: 'metadata',
    metadataHeaders: ['From', 'Subject', 'List-Unsubscribe', 'Content-Type'],
  });
  const message = metadata.data;
  const sender = fromAddress(header(message, 'From'));
  const subject = header(message, 'Subject');
  const receivedAt = new Date(Number(message.internalDate ?? Date.now()));
  const filter = prefilterMessage({
    fromAddress: sender,
    subject,
    hasListUnsubscribe: Boolean(header(message, 'List-Unsubscribe')),
    isCalendarAutoReply: /text\/calendar|\.ics\b/i.test(header(message, 'Content-Type')),
  });
  counts.scanned += 1;
  if (filter.shouldClassify) counts.candidates += 1;

  const raw = await database().query<{ id: string; processed_at: Date | null }>(
    `insert into raw_messages(account_id, gmail_message_id, gmail_thread_id, from_address, from_domain,
       subject, internal_date, prefilter_score, prefilter_reasons, source)
     values ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
     on conflict (account_id, gmail_message_id) do update set prefilter_score = excluded.prefilter_score
     returning id, processed_at`,
    [account.id, gmailMessageId, message.threadId ?? gmailMessageId, sender, filter.fromDomain,
      subject, receivedAt, filter.score, filter.reasons, filter.source],
  );
  const rawMessage = raw.rows[0];
  if (!rawMessage || rawMessage.processed_at) return;
  if (!filter.shouldClassify) {
    await database().query(`update raw_messages set processed_at = now() where id = $1`, [rawMessage.id]);
    return;
  }

  const full = await gmail.users.messages.get({ userId: 'me', id: gmailMessageId, format: 'full' });
  const cleaned = sanitizeMessageHtml(messageHtml(full.data.payload));
  const classifier = new OllamaClassifier();
  const started = Date.now();
  const extraction = await classifier.classify({ cleanedText: cleaned.text, subject, fromAddress: sender, receivedAt, timezone: account.timezone });
  counts.llmCalls += 1;
  const verdict = evaluateExtraction(extraction, {
    cleanedText: cleaned.text,
    confidenceFloor: Number(process.env.EXTRACTION_CONFIDENCE_FLOOR ?? 0.7),
    now: receivedAt,
  });
  const location = locateEvidence(cleaned.text, extraction.evidence);

  await transaction(async (client) => {
    await client.query(
      `update raw_messages set content_sha256=$2, sanitizer_version=$3, processed_at=now() where id=$1`,
      [rawMessage.id, cleaned.contentSha256, cleaned.version],
    );
    const reviewState = verdict.outcome === 'accepted' ? 'auto_applied' : verdict.outcome === 'needs_review' ? 'needs_review' : 'dismissed';
    const failures = verdict.outcome === 'accepted' ? [] : verdict.failures;
    const saved = await client.query<{ id: string }>(
      `insert into llm_extractions(raw_message_id, model, prompt_version, latency_ms, output, confidence,
         evidence_verified, review_state, review_failures, evidence_sha256, evidence_offset, evidence_length)
       values ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12) returning id`,
      [rawMessage.id, process.env.OLLAMA_MODEL ?? 'qwen3:8b', Number(process.env.PROMPT_VERSION ?? 1),
        Date.now() - started, persistedOutput(extraction), extraction.confidence, Boolean(location), reviewState,
        failures, location?.sha256 ?? null, location?.offset ?? null, location?.length ?? null],
    );
    if (verdict.outcome !== 'accepted') return;
    const occurredAt = extraction.occurredAtHint && !Number.isNaN(Date.parse(extraction.occurredAtHint))
      ? new Date(extraction.occurredAtHint) : receivedAt;
    const application = await resolveApplication(client, account, extraction, filter.source, occurredAt);
    if (!application || application.needsReview) {
      await client.query(`update llm_extractions set review_state='needs_review', review_failures=array_append(review_failures,'entity resolution requires review') where id=$1`, [saved.rows[0]?.id]);
      return;
    }
    await client.query(
      `insert into application_events(application_id, raw_message_id, llm_extraction_id, event_type,
         occurred_at, scheduled_at, deadline_at, source)
       values ($1,$2,$3,$4,$5,$6,$7,'llm') on conflict (llm_extraction_id) where llm_extraction_id is not null do nothing`,
      [application.id, rawMessage.id, saved.rows[0]?.id, extraction.eventType, occurredAt,
        extraction.scheduledAt, extraction.deadlineAt],
    );
    await client.query(`select refresh_application_projection($1)`, [application.id]);
    counts.events += 1;
  });
}

async function listBackfillIds(gmail: gmail_v1.Gmail, after?: Date | null): Promise<string[]> {
  const ids: string[] = [];
  let pageToken: string | undefined;
  const query = after ? `${BACKFILL_QUERY} after:${Math.floor(after.getTime() / 1000)}` : BACKFILL_QUERY;
  do {
    const page = await gmail.users.messages.list({ userId: 'me', q: query, pageToken, maxResults: 500 });
    ids.push(...(page.data.messages ?? []).flatMap((message) => message.id ? [message.id] : []));
    pageToken = page.data.nextPageToken ?? undefined;
  } while (pageToken);
  return ids;
}

async function historyIds(gmail: gmail_v1.Gmail, startHistoryId: string): Promise<{ ids: string[]; historyId: string | null }> {
  const ids = new Set<string>();
  let pageToken: string | undefined;
  let latest: string | null = null;
  do {
    const page = await gmail.users.history.list({ userId: 'me', startHistoryId, historyTypes: ['messageAdded'], pageToken, maxResults: 500 });
    for (const history of page.data.history ?? []) for (const added of history.messagesAdded ?? []) if (added.message?.id) ids.add(added.message.id);
    latest = page.data.historyId ?? latest;
    pageToken = page.data.nextPageToken ?? undefined;
  } while (pageToken);
  return { ids: [...ids], historyId: latest };
}

// The historyId cursor must be captured before listing messages, not after — otherwise
// anything delivered while the run is in progress falls between the cursor and the last
// processed message and is silently never seen. Shared by the normal full-backfill path
// and the incremental-cursor-stale recovery path, both of which list messages this way.
async function fullBackfill(gmail: gmail_v1.Gmail, after?: Date | null): Promise<{ ids: string[]; historyId: string | null }> {
  const profile = await gmail.users.getProfile({ userId: 'me' });
  const ids = await listBackfillIds(gmail, after);
  return { ids, historyId: profile.data.historyId ?? null };
}

export async function runSyncJob(jobId: string): Promise<void> {
  const jobs = await database().query<{ id: string; account_id: string; mode: 'full' | 'incremental'; started_at: Date }>(
    `update sync_jobs set status='running', started_at=now() where id=$1 and status='queued' returning id, account_id, mode, started_at`, [jobId],
  );
  const job = jobs.rows[0];
  if (!job) return;
  const client = await database().connect();
  const lock = await client.query<{ locked: boolean }>(`select pg_try_advisory_lock(hashtext($1)) as locked`, [job.account_id]);
  if (!lock.rows[0]?.locked) {
    await client.release();
    await database().query(`update sync_jobs set status='queued', started_at=null where id=$1`, [job.id]);
    return;
  }
  const counts: Counts = { scanned: 0, candidates: 0, events: 0, llmCalls: 0, failed: 0 };
  try {
    const accounts = await database().query<AccountRow>(
      `select ga.*, u.timezone from gmail_accounts ga join app_users u on u.id=ga.user_id where ga.id=$1`, [job.account_id],
    );
    const account = accounts.rows[0];
    if (!account) throw new Error('Gmail account not found');
    const gmail = gmailForEncryptedToken({ ciphertext: account.refresh_token_ciphertext, nonce: account.refresh_token_nonce, keyVersion: account.key_version });
    let mode = job.mode;
    let ids: string[];
    let nextHistoryId: string | null = account.history_id;
    try {
      if (mode === 'incremental' && account.history_id) {
        const history = await historyIds(gmail, account.history_id);
        ids = history.ids; nextHistoryId = history.historyId ?? account.history_id;
      } else {
        mode = 'full';
        const backfill = await fullBackfill(gmail, account.last_synced_at);
        ids = backfill.ids; nextHistoryId = backfill.historyId ?? nextHistoryId;
      }
    } catch (error) {
      if (mode === 'incremental' && errorStatus(error) === 404) {
        mode = 'full';
        const backfill = await fullBackfill(gmail, account.last_synced_at);
        ids = backfill.ids; nextHistoryId = backfill.historyId ?? nextHistoryId;
      } else throw error;
    }
    for (const id of ids) {
      try {
        await processMessage(gmail, account, id, counts);
      } catch (error) {
        // One malformed message must not wedge the whole account's sync forever. Mark it
        // processed so it isn't retried every run, but keep the failure reason so it stays
        // findable and re-drivable — this may be the first write for this message if it
        // failed before processMessage's own raw_messages upsert ran.
        counts.failed += 1;
        await database().query(
          `insert into raw_messages(account_id, gmail_message_id, gmail_thread_id, from_address, from_domain,
             internal_date, prefilter_score, prefilter_reasons, source, processing_error, processing_failed_at, processed_at)
           values ($1,$2,$2,'unknown','unknown',now(),0,'{}','unknown',$3,now(),now())
           on conflict (account_id, gmail_message_id) do update
             set processing_error=excluded.processing_error, processing_failed_at=excluded.processing_failed_at,
                 processed_at=coalesce(raw_messages.processed_at, excluded.processed_at)`,
          [account.id, id, safeOperationalError(error)],
        );
      }
      await database().query(
        `update sync_jobs set messages_scanned=$2, candidates_found=$3, events_created=$4 where id=$1`,
        [job.id, counts.scanned, counts.candidates, counts.events],
      );
    }
    await transaction(async (tx) => {
      await tx.query(
        `update gmail_accounts set history_id=$2,last_synced_at=now(),last_full_sync_at=case when $3='full' then now() else last_full_sync_at end,status='active' where id=$1`,
        [account.id, nextHistoryId, mode],
      );
      await tx.query(`update sync_jobs set status='completed',finished_at=now() where id=$1`, [job.id]);
      await tx.query(
        `insert into sync_runs(account_id,mode,status,started_at,finished_at,messages_seen,llm_calls,messages_failed,note)
         values ($1,$2,$3,$4,now(),$5,$6,$7,$8)`,
        [account.id, mode, mode !== job.mode ? 'recovered' : 'success', job.started_at, counts.scanned, counts.llmCalls, counts.failed,
          mode !== job.mode ? 'stale historyId recovered with bounded backfill' : 'historyId advanced'],
      );
    });
  } catch (error) {
    const message = safeOperationalError(error);
    await database().query(`update sync_jobs set status='failed',finished_at=now(),error=$2 where id=$1`, [job.id, message]);
    await database().query(
      `insert into sync_runs(account_id,mode,status,started_at,finished_at,messages_seen,llm_calls,messages_failed,error)
       values ($1,$2,'failed',$3,now(),$4,$5,$6,$7)`,
      [job.account_id, job.mode, job.started_at, counts.scanned, counts.llmCalls, counts.failed, message],
    );
    if (isCredentialFailure(error)) await database().query(`update gmail_accounts set status='needs_reauth' where id=$1`, [job.account_id]);
    throw error;
  } finally {
    await client.query(`select pg_advisory_unlock(hashtext($1))`, [job.account_id]).catch(() => undefined);
    client.release();
  }
}

export async function runWorkerCycle(): Promise<number> {
  await database().query(
    `insert into worker_heartbeats(worker_name,heartbeat_at) values ('gmail-sync',now())
     on conflict (worker_name) do update set heartbeat_at=excluded.heartbeat_at`,
  );
  await database().query(
    `insert into sync_jobs(account_id,mode)
     select id,'incremental' from gmail_accounts ga
     where status='active' and (last_synced_at is null or last_synced_at < now()-interval '10 minutes')
       and not exists (select 1 from sync_jobs sj where sj.account_id=ga.id and sj.status in ('queued','running'))`,
  );
  const queued = await database().query<{ id: string }>(
    `select id from sync_jobs where status='queued' order by requested_at for update skip locked limit 10`,
  );
  // Each failure is already recorded in sync_jobs/sync_runs by runSyncJob; swallow it here
  // so one account's failure doesn't skip every other account or the heartbeat below.
  for (const job of queued.rows) await runSyncJob(job.id).catch(() => undefined);
  await database().query(
    `update worker_heartbeats set heartbeat_at=now(),jobs_processed=jobs_processed+$1 where worker_name='gmail-sync'`,
    [queued.rowCount ?? 0],
  );
  return queued.rowCount ?? 0;
}
