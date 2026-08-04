-- Production foundation: database authorization, evidence locations, durable
-- sync jobs, manual applications and reversible merges.

create extension if not exists citext;

create table access_allowlist (
  id          uuid primary key default gen_random_uuid(),
  email       citext unique not null,
  status      text not null default 'active' check (status in ('active', 'revoked')),
  note        text,
  added_at    timestamptz not null default now(),
  revoked_at  timestamptz
);

alter table app_users
  add column privacy_notice_version text,
  add column privacy_accepted_at timestamptz;

alter table raw_messages
  add column content_sha256 text,
  add column sanitizer_version int not null default 1;

alter table llm_extractions
  add column evidence_sha256 text,
  add column evidence_offset int,
  add column evidence_length int;

-- Remove verbatim evidence before output is persisted. The application stores
-- only the structured extraction and the location/hash above.
create or replace function strip_extraction_evidence(value jsonb)
returns jsonb language sql immutable as $$
  select value - 'evidence';
$$;

alter table applications
  add column origin text not null default 'gmail' check (origin in ('gmail', 'manual')),
  add column job_url text,
  add column note text;

alter table application_events
  add column llm_extraction_id uuid references llm_extractions(id) on delete set null,
  add column created_by uuid references app_users(id) on delete set null;

alter table corrections
  add column before_values jsonb not null default '{}'::jsonb,
  add column after_values jsonb not null default '{}'::jsonb,
  add column model text,
  add column prompt_version int;

create unique index application_events_extraction_unique
  on application_events (llm_extraction_id)
  where llm_extraction_id is not null;

create table application_merges (
  id                    uuid primary key default gen_random_uuid(),
  source_application_id uuid not null references applications(id) on delete cascade,
  target_application_id uuid not null references applications(id) on delete cascade,
  created_by            uuid not null references app_users(id) on delete cascade,
  created_at            timestamptz not null default now(),
  undone_at             timestamptz,
  check (source_application_id <> target_application_id)
);
create unique index application_merges_active_source_idx
  on application_merges (source_application_id) where undone_at is null;

create table sync_jobs (
  id                  uuid primary key default gen_random_uuid(),
  account_id          uuid not null references gmail_accounts(id) on delete cascade,
  requested_by        uuid references app_users(id) on delete set null,
  mode                text not null check (mode in ('incremental', 'full')),
  status              text not null default 'queued' check (status in ('queued', 'running', 'completed', 'failed')),
  messages_scanned    int not null default 0,
  candidates_found    int not null default 0,
  events_created      int not null default 0,
  requested_at        timestamptz not null default now(),
  started_at          timestamptz,
  finished_at         timestamptz,
  error               text
);
create index sync_jobs_queue_idx on sync_jobs (requested_at) where status = 'queued';

create table oauth_states (
  state_sha256 text primary key,
  user_id uuid not null references app_users(id) on delete cascade,
  expires_at timestamptz not null,
  used_at timestamptz
);
create index oauth_states_expiry_idx on oauth_states (expires_at);

create table worker_heartbeats (
  worker_name text primary key,
  heartbeat_at timestamptz not null,
  jobs_processed int not null default 0
);

alter table invite_requests add column request_fingerprint text;
create index invite_requests_rate_limit_idx on invite_requests (request_fingerprint, requested_at desc);

alter table access_allowlist enable row level security;
alter table application_merges enable row level security;
alter table sync_jobs enable row level security;
alter table oauth_states enable row level security;
alter table worker_heartbeats enable row level security;

create or replace function grant_access(p_email text, p_seat_limit int default 15, p_note text default null)
returns access_allowlist
language plpgsql
security definer
set search_path = public
as $$
declare
  normalized citext := lower(trim(p_email))::citext;
  result access_allowlist;
begin
  if normalized::text !~ '^[^@[:space:]]+@[^@[:space:]]+\.[^@[:space:]]+$' then
    raise exception 'invalid email';
  end if;
  perform pg_advisory_xact_lock(hashtext('ascend-access-allowlist'));
  if not exists (select 1 from access_allowlist where email = normalized and status = 'active')
     and (select count(*) from access_allowlist where status = 'active') >= p_seat_limit then
    raise exception 'seat limit reached';
  end if;
  insert into access_allowlist(email, status, note, revoked_at)
  values (normalized, 'active', p_note, null)
  on conflict (email) do update set status = 'active', note = excluded.note, revoked_at = null
  returning * into result;
  return result;
end;
$$;

-- Replays the same terminal-state rule used by TypeScript.
create or replace function refresh_application_projection(p_application_id uuid)
returns void
language plpgsql
as $$
declare
  item record;
  projected text := null;
  projected_at timestamptz := null;
begin
  for item in
    select event_type, occurred_at from application_events
    where application_id = p_application_id
      and event_type in ('applied','acknowledged','assessment','interview_invite',
                         'interview_scheduled','offer','rejected','withdrawn')
    order by occurred_at, case when source = 'manual' then 1 else 0 end, created_at
  loop
    if projected in ('offer','rejected','withdrawn')
       and item.event_type not in ('offer','rejected','withdrawn') then
      continue;
    end if;
    projected := item.event_type;
    projected_at := item.occurred_at;
  end loop;
  if projected is not null then
    update applications set current_status = projected, status_as_of = projected_at
    where id = p_application_id;
  end if;
end;
$$;
