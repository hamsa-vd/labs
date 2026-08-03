-- Ascend initial schema. See archive/ascend-architecture.md §5.
--
-- Two invariants shape everything here:
--   1. Message bodies are never stored. Headers and derived facts only.
--   2. application_events is append-only. application.current_status is a
--      projection that can be rebuilt from scratch after a prompt change.

create extension if not exists pg_trgm;

-- One row per invited person. Identity is asserted by Cloudflare Access.
create table app_users (
  id         uuid primary key default gen_random_uuid(),
  email      text unique not null,
  timezone   text not null default 'Europe/London',
  created_at timestamptz not null default now(),
  last_seen_at timestamptz
);

create table gmail_accounts (
  id                       uuid primary key default gen_random_uuid(),
  user_id                  uuid not null references app_users(id) on delete cascade,
  gmail_address            text not null,
  -- AES-256-GCM. The key lives on the Mac Mini, never in Supabase, so a full
  -- database compromise yields no usable Gmail access.
  refresh_token_ciphertext bytea not null,
  refresh_token_nonce      bytea not null,
  key_version              int  not null default 1,
  history_id               text,
  last_full_sync_at        timestamptz,
  last_synced_at           timestamptz,
  status                   text not null default 'active'
    check (status in ('active', 'needs_reauth', 'revoked')),
  created_at               timestamptz not null default now(),
  unique (user_id, gmail_address)
);

-- Headers and derived fields. No bodies, ever.
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
  prefilter_reasons text[] not null default '{}',
  -- Derived deterministically from from_domain. Never asked of the model.
  source            text,
  processed_at      timestamptz,
  created_at        timestamptz not null default now(),
  -- Idempotency key: re-running a full sync must be boring, not scary.
  unique (account_id, gmail_message_id)
);

create index raw_messages_unprocessed_idx
  on raw_messages (account_id, internal_date desc)
  where processed_at is null;

create table llm_extractions (
  id                uuid primary key default gen_random_uuid(),
  raw_message_id    uuid not null references raw_messages(id) on delete cascade,
  model             text not null,
  prompt_version    int  not null,
  latency_ms        int,
  output            jsonb not null,
  confidence        numeric(3,2),
  -- Catches hallucination, not injection: the attacker writes the source and
  -- can make any quote appear verbatim. See §13.2.
  evidence_verified boolean not null,
  review_state      text not null
    check (review_state in ('auto_applied', 'needs_review', 'confirmed', 'corrected', 'dismissed')),
  review_failures   text[] not null default '{}',
  created_at        timestamptz not null default now()
);

create index llm_extractions_review_idx
  on llm_extractions (created_at desc)
  where review_state = 'needs_review';

create table applications (
  id              uuid primary key default gen_random_uuid(),
  user_id         uuid not null references app_users(id) on delete cascade,
  company_norm    text not null,
  company_display text not null,
  role_title      text,
  role_norm       text,
  source          text,
  first_seen_at   timestamptz not null,
  -- Projection. Recomputable from application_events; never authoritative.
  current_status  text not null
    check (current_status in ('applied','acknowledged','assessment','interview_invite',
                              'interview_scheduled','offer','rejected','withdrawn')),
  status_as_of    timestamptz not null,
  archived        boolean not null default false,
  created_at      timestamptz not null default now()
);

-- Entity resolution matches on the (company, role) pair, not company alone:
-- one company routinely runs two concurrent applications. See §5.
create index applications_company_trgm_idx on applications using gin (company_norm gin_trgm_ops);
create index applications_role_trgm_idx    on applications using gin (role_norm gin_trgm_ops);
create index applications_user_status_idx  on applications (user_id, current_status) where not archived;

-- Append only. Never updated, never deleted.
create table application_events (
  id             uuid primary key default gen_random_uuid(),
  application_id uuid not null references applications(id) on delete cascade,
  raw_message_id uuid references raw_messages(id) on delete set null,
  event_type     text not null,
  occurred_at    timestamptz not null,
  -- The fields a user can actually miss. See §11.3.2.
  scheduled_at   timestamptz,
  deadline_at    timestamptz,
  source         text not null default 'llm' check (source in ('llm', 'manual')),
  created_at     timestamptz not null default now()
);

create index application_events_application_idx on application_events (application_id, occurred_at);
create index application_events_deadline_idx
  on application_events (deadline_at)
  where deadline_at is not null;

-- User corrections. The eval flywheel: these are promoted into the golden set.
create table corrections (
  id                uuid primary key default gen_random_uuid(),
  llm_extraction_id uuid not null references llm_extractions(id) on delete cascade,
  user_id           uuid not null references app_users(id) on delete cascade,
  corrected         jsonb not null,
  promoted_to_eval  boolean not null default false,
  created_at        timestamptz not null default now()
);

create table user_settings (
  user_id            uuid primary key references app_users(id) on delete cascade,
  model              text not null default 'qwen3:8b',
  prompt_version     int  not null default 1,
  poll_interval_mins int  not null default 10,
  confidence_floor   numeric(3,2) not null default 0.70,
  theme              text not null default 'dark' check (theme in ('dark', 'light'))
);

-- Cached so the overview never waits on Ollama. Structured input only: the
-- digest prompt must not see raw email text. See §13.1.
create table daily_digests (
  id           uuid primary key default gen_random_uuid(),
  user_id      uuid not null references app_users(id) on delete cascade,
  generated_at timestamptz not null default now(),
  covers_since timestamptz not null,
  headline     text not null,
  body         text not null,
  fallback_used boolean not null default false
);

create index daily_digests_user_idx on daily_digests (user_id, generated_at desc);

create table sync_runs (
  id            uuid primary key default gen_random_uuid(),
  account_id    uuid references gmail_accounts(id) on delete cascade,
  mode          text not null check (mode in ('incremental', 'full')),
  status        text not null check (status in ('success', 'recovered', 'failed')),
  started_at    timestamptz not null,
  finished_at   timestamptz,
  messages_seen int,
  llm_calls     int,
  note          text,
  error         text
);

create index sync_runs_recent_idx on sync_runs (started_at desc);

-- The only unauthenticated write. Turnstile and a rate limit sit in front.
create table invite_requests (
  id           uuid primary key default gen_random_uuid(),
  email        text not null,
  note         text,
  status       text not null default 'pending' check (status in ('pending', 'approved', 'declined')),
  requested_at timestamptz not null default now()
);

-- RLS is defence in depth. The server uses the service role and bypasses it,
-- but this is what saves you the day something queries from the browser.
alter table app_users          enable row level security;
alter table gmail_accounts     enable row level security;
alter table raw_messages       enable row level security;
alter table llm_extractions    enable row level security;
alter table applications       enable row level security;
alter table application_events enable row level security;
alter table corrections        enable row level security;
alter table user_settings      enable row level security;
alter table daily_digests      enable row level security;
alter table sync_runs          enable row level security;
alter table invite_requests    enable row level security;
