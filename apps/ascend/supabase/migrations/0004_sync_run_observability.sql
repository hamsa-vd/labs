-- Make sync-run telemetry explain the full Gmail-to-event pipeline.
alter table sync_runs
  add column messages_discovered int not null default 0,
  add column candidates_found int not null default 0,
  add column events_created int not null default 0,
  add column duration_ms int,
  add column failure_stage text;
