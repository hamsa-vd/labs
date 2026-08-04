-- One bad message must not wedge an account's sync forever, and discarding the
-- failure reason would make it unfindable and unre-drivable afterward.

alter table raw_messages
  add column processing_error text,
  add column processing_failed_at timestamptz;

alter table sync_runs
  add column messages_failed int not null default 0;
