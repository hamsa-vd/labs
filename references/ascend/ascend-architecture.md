# Ascend: Architecture Review and Build Plan

**Context:** invite-only job application tracker. Gmail ingestion, local LLM classification, Supabase Postgres, self-hosted on a Mac Mini behind a Cloudflare Tunnel. Roughly 5 to 15 users, all personally invited and allowlisted.

**Date:** August 2026

---

## 1. Verdict on the stack as proposed

| Choice | Verdict | Note |
|---|---|---|
| Gmail API for ingestion | Keep | But the OAuth publishing status decision is critical. See §2. |
| Local LLM via Ollama | Keep, and it is a compliance asset, not just a cost saving. See §7. |
| Supabase Postgres | Keep | Free tier is ample. Encrypt refresh tokens before they land in it. |
| Mac Mini host | Keep, with caveats | Sleep, power cuts and >7 day downtime each have a specific failure mode. See §8. |
| Cloudflare Tunnel | Keep, and add Cloudflare Access | Access gives you the invite allowlist for free and deletes a whole auth subsystem. |
| Supabase Auth "Login with Google" | **Drop it** | See §2.4. It is the wrong tool for holding long-lived Gmail refresh tokens. |
| "a very small script" | **Wrong framing** | Single-user is a script. Multi-user Gmail access is a compliance and key-management project. Budget accordingly. |

---

## 2. The decision that determines everything: Google OAuth

### 2.1 The problem

`https://www.googleapis.com/auth/gmail.readonly` is a Google **restricted** scope. Because Ascend stores restricted-scope data on a server you operate, publishing a *verified* app would require an annual security assessment by a Google-empanelled assessor (CASA), typically Tier 2 self-scan-plus-lab-verification, in some cases Tier 3 with a full penetration test. ([Google: Restricted scope verification](https://developers.google.com/identity/protocols/oauth2/production-readiness/restricted-scope-verification))

You do not need to do that. But you do need to pick the right publishing status, and the naive choice breaks the product.

### 2.2 Testing status is a trap

An OAuth app left in **Testing** status:

- caps you at 100 test users (fine for you), and
- **expires every authorization 7 days after consent**, including the refresh token, which then returns `invalid_grant`. ([Google Cloud: Manage App Audience](https://support.google.com/cloud/answer/15549945?hl=en))

That means every friend reconnects their Gmail weekly, forever. The product dies on contact.

### 2.3 The right answer: publish to "In production", stay unverified

Setting publishing status to **In production** without completing verification:

- removes the 7-day refresh token expiry, so tokens become long-lived, and
- keeps you capped at 100 users, which you do not care about, and
- shows every user a "Google hasn't verified this app" interstitial. They click *Advanced* then *Go to Ascend (unsafe)*.

([Google: OAuth app state overview](https://developers.google.com/identity/protocols/oauth2/production-readiness/overview), [Unipile: Google OAuth refresh token expiration](https://www.unipile.com/google-oauth-refresh-token/))

For personally invited friends, a one-time scary screen you warn them about in advance is acceptable. Write the warning into your invite email with a screenshot so nobody bounces.

**Confidence note:** the "In production unverified" path is documented and widely used, but Google has tightened restricted-scope enforcement repeatedly. Verify the behaviour yourself with a throwaway second Google account before you onboard anyone: connect, wait 8 days, confirm the refresh token still works. Do not take this on faith, mine or anyone else's.

**Fallback if Google closes this path:** per-user forwarding aliases. Cloudflare Email Routing on a domain you own, forwarding to a Worker that POSTs to your tunnel. Each user sets one Gmail filter to forward job mail to `hamsa@ascend.yourdomain`. Zero Google scopes, zero verification, zero token management. It is a worse UX and misses mail the filter does not catch, but it is bulletproof and free. Keep it in your back pocket.

### 2.4 Do not use Supabase Auth's Google provider for Gmail access

Supabase Auth returns `provider_refresh_token` only on the first consent, and Supabase does not refresh Google provider tokens for you or re-issue them on subsequent logins. You end up writing the refresh logic anyway, on top of an abstraction that hides the token. Own the OAuth flow directly with `googleapis` / `google-auth-library` and store the refresh token yourself.

### 2.5 Collapse the login problem entirely

You do not need application login at all. Put **Cloudflare Access** (Zero Trust, free for up to 50 seats) in front of the tunnel, with Google as the identity provider and a hardcoded email allowlist. Unauthenticated requests never reach your Mac Mini. Your app reads the verified identity from the `Cf-Access-Jwt-Assertion` header.

Validate that JWT server-side against Cloudflare's JWKS (`https://<team>.cloudflareaccess.com/cdn-cgi/access/certs`). Do not trust the raw header without verification, and make sure `cloudflared` only exposes `localhost:PORT` so the origin is not independently reachable.

This removes: signup, sessions, password reset, RLS policy design, and the invite system. You add an email to a Cloudflare policy and that is the invite.

### 2.6 Scope minimisation

Request `gmail.readonly` only. Not `gmail.modify`, not `mail.google.com/`. Two additional disciplines that cost you nothing now and save you enormously if you ever pursue verification:

1. **Never persist message bodies.** Fetch, classify, extract structured fields, discard. Store the subject, sender, `internalDate`, message ID and derived facts. If Supabase is ever breached, there is no correspondence to leak.
2. **Never send email content to a third-party API.** Google's [Limited Use requirements](https://developers.google.com/terms/api-services-user-data-policy) prohibit transferring restricted-scope data except in narrow cases. Local Ollama is not a cost optimisation here, it is the compliant architecture. Sending user email bodies to OpenAI or Anthropic would put you in breach.

---

## 3. Recommended topology

```
Friend's browser
      |
      v
Cloudflare Access (email allowlist, Google IdP, free <=50 seats)
      |
      v
Cloudflare Tunnel  ---- cloudflared (launchd service) ----+
                                                          |
                              Mac Mini                    v
                    +-------------------------------------------------+
                    |  ascend-web    (Hono/Fastify + React, :8080)    |
                    |  ascend-sync   (launchd, every 10 min)          |
                    |  ollama serve  (:11434, OLLAMA_KEEP_ALIVE=24h)  |
                    +-------------------------------------------------+
                                 |                    |
                                 v                    v
                        Gmail API (HTTPS)      Supabase Postgres
```

One process for web plus one scheduled worker. Do not introduce a queue, Docker, or Kubernetes at this scale. Postgres is your queue if you ever need one (`SELECT ... FOR UPDATE SKIP LOCKED`).

**Language:** Node/TypeScript is the path of least resistance given `googleapis` is first-party and you are full stack. Python/FastAPI is equally fine. Pick the one you will still enjoy debugging at 11pm.

---

## 4. Gmail sync design

### 4.1 Two paths, both mandatory

**Initial backfill (per account, once):** `users.messages.list` with a targeted query to avoid pulling the whole mailbox:

```
newer_than:2y -in:chats -in:spam (
  from:(greenhouse.io OR lever.co OR ashbyhq.com OR myworkday.com OR icims.com
        OR smartrecruiters.com OR workable.com OR teamtailor.com OR jobvite.com
        OR taleo.net OR successfactors.com OR breezy.hr OR recruitee.com
        OR pinpointhq.com OR bamboohr.com OR linkedin.com OR indeed.com OR otta.com)
  OR subject:("thank you for applying" OR "your application" OR "application received"
        OR "interview" OR "we regret" OR "moving forward" OR "next steps"
        OR "assessment" OR "offer")
)
```

This is a recall/cost tradeoff, and you should measure the recall loss on your own mailbox before shipping it. Run a full unfiltered `newer_than:1y` list once on your own account, classify everything, and see what the filtered query would have missed.

**Incremental (every run):** `users.history.list` with the stored `startHistoryId` and `historyTypes=messageAdded`.

### 4.2 The failure mode you must code for on day one

A `historyId` is valid for **at least a week, occasionally only hours**, and history records are purged after roughly 30 days. A stale `startHistoryId` returns **HTTP 404**, and the only recovery is a full re-sync. ([Google: users.history.list](https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.history/list))

This matters more for you than for most, because a home Mac Mini goes offline: power cuts, OS updates, you unplug it to move house. Any outage over about a week guarantees a 404. So:

- catch 404 explicitly, log it, and fall back to the filtered backfill query bounded by `after:<last_synced_at>`,
- make ingestion idempotent (see §5) so a full re-sync is safe and boring, not scary.

### 4.3 Skip Pub/Sub push for now

`users.watch` gives you near-realtime push, but the watch expires in 7 days and must be renewed daily, and it needs a Google Cloud Pub/Sub topic plus a publicly reachable push endpoint. For a job tracker, 10-minute polling latency is invisible to the user. Add push in M6 if you ever want it.

### 4.4 Quotas

Gmail API per-project daily quota and per-user rate limits are generous relative to 15 users doing a few hundred messages a day. `messages.get` is the expensive call. Batch with `format=metadata` first where you only need headers, and only fetch `format=full` for messages that clear the prefilter (§6.1). Check current numbers at [Gmail API usage limits](https://developers.google.com/workspace/gmail/api/reference/quota) rather than trusting a figure quoted here.

---

## 5. Data model

Event-sourced, because emails arrive out of order and your LLM will be wrong sometimes. You want to re-derive state from scratch after a prompt change, not migrate it.

```sql
create extension if not exists pg_trgm;

-- one row per invited person
create table app_users (
  id            uuid primary key default gen_random_uuid(),
  email         text unique not null,
  created_at    timestamptz not null default now()
);

create table gmail_accounts (
  id                      uuid primary key default gen_random_uuid(),
  user_id                 uuid not null references app_users(id) on delete cascade,
  gmail_address           text not null,
  refresh_token_ciphertext bytea not null,   -- AES-256-GCM, key NOT in Supabase
  refresh_token_nonce      bytea not null,
  key_version             int  not null default 1,
  history_id              text,
  last_full_sync_at       timestamptz,
  last_synced_at          timestamptz,
  status                  text not null default 'active',  -- active | needs_reauth | revoked
  unique (user_id, gmail_address)
);

-- headers + derived only. NO bodies.
create table raw_messages (
  id                uuid primary key default gen_random_uuid(),
  account_id        uuid not null references gmail_accounts(id) on delete cascade,
  gmail_message_id  text not null,
  gmail_thread_id   text not null,
  from_address      text not null,
  from_domain       text not null,
  subject           text,
  internal_date     timestamptz not null,
  prefilter_score   int  not null,
  prefilter_reasons text[],
  processed_at      timestamptz,
  unique (account_id, gmail_message_id)      -- idempotency key
);

create table llm_extractions (
  id              uuid primary key default gen_random_uuid(),
  raw_message_id  uuid not null references raw_messages(id) on delete cascade,
  model           text not null,             -- 'qwen3:8b'
  prompt_version  int  not null,
  latency_ms      int,
  output          jsonb not null,
  confidence      numeric(3,2),
  created_at      timestamptz not null default now()
);

create table applications (
  id              uuid primary key default gen_random_uuid(),
  user_id         uuid not null references app_users(id) on delete cascade,
  company_norm    text not null,             -- 'monzo'
  company_display text not null,             -- 'Monzo Bank Ltd'
  role_title      text,
  source          text,                      -- 'linkedin' | 'direct' | 'referral'
  first_seen_at   timestamptz not null,
  current_status  text not null,             -- projection, recomputable
  status_as_of    timestamptz not null,
  archived        boolean not null default false
);
create index on applications using gin (company_norm gin_trgm_ops);

-- append only. never update, never delete.
create table application_events (
  id              uuid primary key default gen_random_uuid(),
  application_id  uuid not null references applications(id) on delete cascade,
  raw_message_id  uuid references raw_messages(id),
  event_type      text not null,
  occurred_at     timestamptz not null,
  source          text not null default 'llm',  -- llm | manual
  created_at      timestamptz not null default now()
);

create table sync_runs (
  id            uuid primary key default gen_random_uuid(),
  account_id    uuid references gmail_accounts(id) on delete cascade,
  mode          text not null,             -- incremental | full
  started_at    timestamptz not null,
  finished_at   timestamptz,
  messages_seen int, llm_calls int, error text
);
```

**`current_status` is a projection**, computed from `application_events` by a precedence function (`offer > rejected > interview_scheduled > interview_invite > assessment > acknowledged > applied`), tie-broken by `occurred_at`. Keep the function in SQL so you can rebuild every application's status with one `UPDATE ... FROM (subquery)` after a prompt change.

**Entity resolution.** A rejection often arrives in a new thread, so `gmail_thread_id` alone will not group correctly. Normalise the company name (lowercase, strip `Ltd|Limited|Inc|LLC|GmbH|plc|Group`, strip legal punctuation), then match within the same `user_id` using `similarity(company_norm, $1) > 0.6` from `pg_trgm`, further constrained by role title similarity when present. Expect this to be the single buggiest part of the system. Build a manual "merge these two applications" button in the UI early; it is cheaper than perfect matching.

---

## 6. Classification pipeline

### 6.1 Stage 0: deterministic prefilter, no LLM

Score every message before it touches Ollama. Do not run an LLM on your Deliveroo receipts.

**Strong signals (sender domain):** `greenhouse.io`, `my.greenhouse.io`, `lever.co`, `hire.lever.co`, `ashbyhq.com`, `myworkday.com`, `myworkdayjobs.com`, `icims.com`, `taleo.net`, `successfactors.com`, `smartrecruiters.com`, `workable.com`, `workablemail.com`, `teamtailor.com`, `jobvite.com`, `breezy.hr`, `recruitee.com`, `personio.de`, `pinpointhq.com`, `bamboohr.com`, `eu.dayforcehcm.com`, `avature.net`, `pinpoint.hr`

**Aggregator signals:** `linkedin.com` (especially `jobs-noreply@linkedin.com`), `indeed.com`, `otta.com`, `welcometothejungle.com`, `glassdoor.com`, `hired.com`, `cord.co`, `wellfound.com`, `builtin.com`

**Subject regex:** `thank you for (applying|your (application|interest))`, `application (received|status|update)`, `we (regret|are unable)`, `moving forward`, `next steps`, `(technical|coding|online) assessment`, `schedule.{0,20}(call|interview)`, `offer of employment`

**Hard negatives (score to zero regardless):** `noreply@linkedin.com` job *alerts*, newsletters with `List-Unsubscribe` plus zero strong signals, calendar invite `.ics` auto-replies.

Expected effect: roughly 90 to 97 percent of mail skips the LLM entirely. *This is a hypothesis based on typical inbox composition, not a measured figure. Instrument it and check.*

### 6.2 Stage 1: structured extraction

Ollama supports JSON Schema constrained decoding via the `format` parameter. Use it. Do not parse freeform text.

```json
{
  "type": "object",
  "required": ["is_job_related", "event_type", "confidence"],
  "properties": {
    "is_job_related": { "type": "boolean" },
    "company":    { "type": ["string", "null"] },
    "role_title": { "type": ["string", "null"] },
    "event_type": { "type": "string", "enum": [
      "applied", "acknowledged", "assessment", "interview_invite",
      "interview_scheduled", "offer", "rejected", "withdrawn",
      "recruiter_outreach", "job_alert", "other"
    ]},
    "occurred_at_hint": { "type": ["string", "null"] },
    "confidence": { "type": "number", "minimum": 0, "maximum": 1 },
    "evidence": { "type": "string", "description": "verbatim quote from the email supporting event_type" }
  }
}
```

The `evidence` field is not decoration. It is your debugging handle and your hallucination detector: if the quoted span does not appear in the source text, discard the extraction.

**Input preparation matters more than model choice.** Strip HTML to text, drop quoted reply chains (`On ... wrote:`, `>` prefixed lines), drop footers after `Unsubscribe`, collapse whitespace, truncate to about 2000 characters. A clean 2000 characters beats a noisy 8000.

**Settings:** `temperature: 0`, fixed `seed`, `OLLAMA_KEEP_ALIVE=24h` so the model stays resident between the 10-minute polls (cold load of an 8B model costs several seconds every run otherwise).

### 6.3 Model recommendation

You did not say which Mac Mini, so:

| RAM | Recommendation | Reasoning |
|---|---|---|
| 16 GB (M4 base) | `qwen3:8b` | Best instruction-following and JSON adherence per GB in that class. `gemma3:12b-it-qat` is the alternative if you want stronger English nuance and can spare the memory. |
| 24 to 36 GB (M4 Pro) | `qwen3:14b` | Noticeably better at ambiguous rejections and multi-role emails. |
| 48 GB+ | `gpt-oss:20b` or `qwen3:30b-a3b` | The MoE variant is fast for its size. Only worth it if your eval shows the smaller models failing. |

Start at `qwen3:8b`. Do not upgrade the model until your eval set tells you the model is the bottleneck. In my experience with this class of task the bottleneck is almost always input cleaning and prompt specificity, not parameter count.

Rough throughput on M4-class silicon for an 8B model is tens of tokens per second, so a ~200 token structured output lands in the low seconds per email. A 300-email backfill is a coffee break, not an overnight job.

### 6.4 The highest-leverage thing you will do

**Build a golden set of 100 hand-labelled emails from your own mailbox before you tune anything.** Store it as a JSONL file in the repo: cleaned input text plus expected `event_type`, `company`, `role_title`. Write a `pnpm eval` script that prints precision and recall per `event_type`.

Without this you are changing prompts based on vibes and you will not know when you have made things worse. With it, prompt iteration becomes a 30-second loop. Include the awkward cases deliberately: rejections that thank you warmly, recruiter cold outreach that reads like an application acknowledgement, one email covering two roles, non-English mail if relevant.

Then: every manual correction a user makes in the UI gets appended to a `corrections` table, and you periodically promote those into the golden set. That is your flywheel.

---

## 7. Security

**Refresh tokens.** Encrypt with AES-256-GCM in your application before insert. The key lives on the Mac Mini, never in Supabase, never in the repo. Options in increasing order of effort: a `0600` file read at boot, an environment variable in the launchd plist, or macOS Keychain via `security find-generic-password -w`. Include `key_version` in the schema (already there) so rotation is possible without a heroic migration. The property you want: a full Supabase compromise yields no usable Gmail access.

**Supabase service_role key** stays server-side only. If it ever touches browser JavaScript, every row of every table is public.

**Row Level Security** on all tables even though Cloudflare Access is your real perimeter and your backend uses `service_role` (which bypasses RLS). It costs an hour and it is the thing that saves you the day you add a direct-from-browser query.

**Google Limited Use.** Restricted-scope data must not be transferred to third parties, used for advertising, or read by humans except for security or with explicit consent. This binds you whether or not you are verified. It is the reason local Ollama is the right call, and the reason you should not "just try GPT-5 for the hard cases".

**UK GDPR.** *This is not legal advice and I am not a lawyer.* Once you process other people's email data on infrastructure you control, you are plausibly a data controller under UK GDPR, and the Article 2(2)(c) "purely personal or household activity" exemption is arguable but not something I would rely on. Practical, proportionate steps for a friends-only tool: a one-page written notice each user acknowledges before connecting (what you collect, where it is stored, that a local model reads it, that nothing leaves your machine except to Supabase), a working delete-my-account button that actually purges rows and revokes the Google token, and a retention limit (for example, purge `raw_messages` older than 2 years). If Ascend ever goes public, get proper advice. The [ICO's guidance for small organisations](https://ico.org.uk/for-organisations/) is the starting point.

---

## 8. Running this on a Mac Mini

- **Use `launchd`, not `cron`.** `cron` handles sleep and missed runs badly. A `launchd` plist with `StartInterval` plus `KeepAlive` is the correct primitive. Install `cloudflared` the same way with `cloudflared service install`.
- **Stop it sleeping:** `sudo pmset -a sleep 0 disablesleep 1 autorestart 1 powernap 0`. `autorestart 1` reboots the machine automatically after a power failure, which is the outage you will actually hit.
- **Survive a long outage.** Any downtime beyond about a week means a `historyId` 404 and a full re-sync (§4.2). This is fine if ingestion is idempotent. Test it deliberately: delete the stored `history_id` and confirm a clean re-sync produces zero duplicate events.
- **Supabase free tier pauses projects after 7 days of inactivity.** Your sync keeps it warm in normal operation, but a Mac Mini outage plus an auto-paused database is a compounding failure. Set an external heartbeat.
- **Backups.** Nightly `pg_dump` to the Mini, then `rclone` to Google Drive or R2. Supabase free tier backup guarantees are thin. Test a restore once.
- **Observability.** The `sync_runs` table plus a `/healthz` endpoint plus a free [healthchecks.io](https://healthchecks.io) ping at the end of each successful run. If the ping does not arrive, you get an email. That is the whole monitoring stack and it is enough.
- **Reauth loop.** When a refresh token dies, set `gmail_accounts.status = 'needs_reauth'` and show a banner in the UI. Do not silently stop syncing; that is how a tracker quietly goes stale for three weeks without anyone noticing.

---

## 9. Build order

| Milestone | Scope | Done when |
|---|---|---|
| **M0** | CLI script, your Gmail only, no DB, no UI. Prefilter plus Ollama plus JSON output printed to stdout. Build the 100-email golden set and the eval script. | Precision and recall on your golden set are good enough that you would trust the output. |
| **M1** | Supabase schema, idempotent ingest, event sourcing, status projection, entity resolution. Still your account only, still CLI. | Running the backfill twice produces identical state. |
| **M2** | Read-only web UI. `cloudflared` plus Cloudflare Access with just your email. | You can see your tracker from your phone. |
| **M3** | Multi-user: your own Google OAuth connect flow, encrypted token storage, `In production` publishing status, Cloudflare Access allowlist. Onboard exactly one friend. | Their tokens still work on day 8. Verify this explicitly. |
| **M4** | `users.history.list` incremental sync, 404 full-resync fallback, `launchd` scheduling, healthchecks ping, `needs_reauth` handling. | Unplug the Mac Mini for a day; it recovers unattended. |
| **M5** | Manual correction UI (edit status, merge applications, mark not-job-related), corrections feeding the golden set, delete-my-account. | A friend fixes a mistake without messaging you. |
| **M6 (optional)** | Pub/Sub push, weekly digest email, stale-application nudges, analytics. | |

The ordering point: **M0 before anything else.** If local classification does not reach acceptable accuracy on your own mail, none of the infrastructure matters, and you will have found out in two evenings instead of two months.

---

## 10. Where I would push back hardest

1. **"Small script" is a misread.** Single-user is genuinely a weekend. Adding other people's Gmail is a different category of project: OAuth publishing status, key management, reauth flows, a data protection posture, and a support burden when it breaks. Decide whether the multi-user part is a goal or a distraction from a tracker that works for you.
2. **Verify the token-lifetime claim yourself.** §2.3 is the load-bearing assumption of the whole multi-user design, and Google changes restricted-scope enforcement often. An 8-day test with a throwaway account costs you nothing and de-risks everything.
3. **The golden set is not optional overhead.** It is the difference between an LLM feature you can improve and one you can only pray at.
4. **Do not store email bodies.** It is tempting for debugging. Store the cleaned text hash and the `evidence` quote instead. Future-you, explaining a breach to a friend, will be grateful.

---

## Sources

- [Google: Restricted scope verification](https://developers.google.com/identity/protocols/oauth2/production-readiness/restricted-scope-verification)
- [Google: OAuth app state overview](https://developers.google.com/identity/protocols/oauth2/production-readiness/overview)
- [Google Cloud Console Help: Manage App Audience](https://support.google.com/cloud/answer/15549945?hl=en)
- [Google: Method users.history.list](https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.history/list)
- [Google API Services User Data Policy (Limited Use)](https://developers.google.com/terms/api-services-user-data-policy)
- [Unipile: Google OAuth refresh token expiration explained (2026)](https://www.unipile.com/google-oauth-refresh-token/)
- [Unipile: Google OAuth 100 user limit (2026)](https://www.unipile.com/google-oauth-100-user-limit/)
- [ICO: guidance for organisations](https://ico.org.uk/for-organisations/)
