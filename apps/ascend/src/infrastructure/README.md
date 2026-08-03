# Infrastructure adapters

Implement external boundaries here without leaking vendor SDK types into the domain or application layers.

Expected adapters:

- `cloudflare/` — Access JWT validation
- `database/` — Supabase Postgres repositories and migrations
- `encryption/` — refresh-token envelope encryption
- `gmail/` — OAuth, backfill, and history synchronization
- `ollama/` — local structured extraction

No integration is implemented in the scaffold.
