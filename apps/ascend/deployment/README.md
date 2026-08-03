# Deployment

Mac Mini, behind a Cloudflare Tunnel with Access in front. See architecture §8.

## Host preparation

    sudo pmset -a sleep 0 disablesleep 1 autorestart 1 powernap 0

`autorestart 1` matters most: a power cut is the outage you will actually hit.

## Services

| Service | Manager | Notes |
|---|---|---|
| `ascend-web` | launchd | `next start` from the standalone build |
| `ascend-sync` | launchd | `com.ascend.sync.plist`, every 10 minutes |
| `cloudflared` | launchd | `cloudflared service install`. Exposes localhost only |
| `ollama` | launchd | `OLLAMA_KEEP_ALIVE=24h` so the model stays resident between polls |

## Cloudflare Access policies

| Path | Policy |
|---|---|
| `/welcome`, `/privacy`, `/status`, `/api/v1/invite-requests` | Bypass |
| everything else | Allow, email allowlist, Google IdP |

Validate `Cf-Access-Jwt-Assertion` server-side against the team JWKS. Do not
trust the header unverified.

## After an outage longer than a week

The stored `historyId` will be stale and `users.history.list` returns 404. The
sync falls back to a bounded full backfill automatically. Ingestion is
idempotent on `(account_id, gmail_message_id)`, so this is boring by design.
Test it deliberately: clear `history_id` and confirm zero duplicate events.
