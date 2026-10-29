# Open decisions

Each has a recommendation. The ticket that forces the decision is named. Decide before that
ticket starts; record the outcome by editing this file, not in chat.

## D1 — Where do `.tex` and `.pdf` files live? *(forces RG-006)*

**Recommendation: Supabase Storage**, private bucket `documents`, path
`{user_id}/{application_id}/{run_id}/{resume.tex|resume.pdf|cover_letter.tex|JD.txt}`.

Rationale: Supabase is already the transactional store, so there is one auth model, one
dashboard, and one backup story. Signed URLs (60 s TTL) let the browser download PDFs without
proxying bytes through FastAPI. S3 or R2 would be marginally cheaper at volume and add a second
credential surface — not worth it for a single-tenant-scale product.

Guard against lock-in: all access goes through a `BlobStore` protocol
(`put`, `get`, `signed_url`, `delete`) with the Supabase implementation behind it. Swapping to
S3 later is one class.

## D2 — How is LaTeX compiled? *(forces RG-035)*

**Recommendation: a Tectonic container as a separate service.** Tectonic is a single static
binary, fetches packages on demand, and needs no TeX Live install. Run it as
`services/latex` with a one-route HTTP wrapper (`POST /compile` → PDF bytes), no network egress,
read-only filesystem apart from a tmpfs scratch dir, 20 s timeout, 512 MB memory cap.

Do **not** shell out from the API process as v1 does — user-supplied `.tex` is untrusted input
and `\write18` / `\input` escapes are a real risk. Client-side WASM compilation was considered
and rejected: bundle size and inconsistent output.

## D3 — Invite issuance *(forces RG-003 / RG-051)*

**Recommendation:** `allowed_emails` table, seeded manually via SQL for the first cohort. The
OAuth callback rejects any email not present and shows the register-interest screen. The admin
portal (RG-051) later adds a UI over the same table. No invite codes, no email sending in v2.0.

## D4 — Background worker *(forces RG-032)*

**Recommendation:** start with FastAPI `BackgroundTasks` and a Postgres-backed run state, which
is enough for single-digit concurrency. Because run state is already in `runs`/`run_events`,
moving to arq + Redis is a swap of the enqueue call, not a redesign. Revisit at RG-052.

## D5 — Model defaults and cost ceiling

**Recommendation:** keep v1's split — a strong model for targeting/review (Claude), a
generation model (OpenAI), and a cheap revision model — but make all three user-selectable in
settings with v1's `MAX_*` budgets as editable per-user ceilings. Ship a hard server-side cap
above the user's setting so a misconfiguration cannot run away.
