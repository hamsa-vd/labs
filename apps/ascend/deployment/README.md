# Deployment

Mac Mini, behind a Cloudflare Tunnel with Access in front. See architecture §8.

## Host preparation

    sudo pmset -a sleep 0 disablesleep 1 autorestart 1 powernap 0

`autorestart 1` matters most: a power cut is the outage you will actually hit.

## Services

| Service | Manager | Notes |
|---|---|---|
| `ascend-web` | launchd | `next start` from the standalone build |
| `ascend-sync` | launchd | Dispatcher every minute; each account remains due every 10 minutes |
| `cloudflared` | launchd | `cloudflared service install`. Exposes localhost only |
| `ollama` | launchd | `OLLAMA_KEEP_ALIVE=24h` so the model stays resident between polls |
| `ascend-backup` | launchd | Nightly custom-format dump encrypted with a key stored outside the repository |
| `ascend-retention` | launchd | Daily metadata and operational-record retention |

`pnpm build` copies `public` and static assets into the standalone output. The
web and Ollama launchd templates bind explicitly to `127.0.0.1`; configure the
Cloudflare Tunnel ingress as `http://127.0.0.1:3000`. Replace every `CHANGEME`
path before loading a plist, and make the service environment available to the
launchd jobs without committing it.

## Cloudflare Access policies

| Path | Policy |
|---|---|
| `/welcome`, `/privacy`, `/status`, `/no-access`, `/api/v1/status`, `/api/v1/invite-requests` | Bypass |
| everything else | Allow authenticated Google identity |

Validate `Cf-Access-Jwt-Assertion` server-side against the team JWKS. Do not
trust the header unverified.

Configure the Access policy to require Google identity for all authenticated
paths. Ascend then checks the verified email against `access_allowlist`; Access
identity is authentication, while the database row is authorization.

Grant access manually with a transaction-safe seat-cap check:

    select (grant_access('friend@gmail.com', 15, 'Personally invited')).*;

Revoking a row sends the user to `/no-access` on their next request:

    update access_allowlist set status='revoked', revoked_at=now()
    where email='friend@gmail.com';

## Restore drill

Set `ASCEND_BACKUP_DIR` and `ASCEND_BACKUP_KEY_FILE` in the launchd environment,
then install `com.ascend.backup.plist`. The key file must be mode `0600` and must
not live in this repository. The backup script only publishes the final file
after `pg_dump` and AES-256 encryption both succeed.

Once per quarter, decrypt the latest dump into a temporary file, restore it into
a temporary database with `pg_restore`, run all migrations, compare row counts
for the core tables, and destroy both temporary targets. Record the date and
counts in the operator log; an untested backup is not a backup.

## After an outage longer than a week

The stored `historyId` will be stale and `users.history.list` returns 404. The
sync falls back to a bounded full backfill automatically. Ingestion is
idempotent on `(account_id, gmail_message_id)`, so this is boring by design.
Test it deliberately: clear `history_id` and confirm zero duplicate events.
