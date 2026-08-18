alter table gmail_accounts
  add column backfill_days int not null default 365
  check (backfill_days between 30 and 1460);

