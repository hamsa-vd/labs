# RG-054 — Promote to cloud environments

**Epic:** F — Operations · **Depends on:** RG-009, RG-008 · **Estimate:** L · **Labels:** ops, infra

## Product requirement

**Problem.** Everything up to here runs locally. Going to the cloud is where a working project
quietly acquires a production incident: a leaked service-role key, an unrestricted CORS origin,
a database with no backups, or a LaTeX container reachable from the internet.

**Outcome.** Two real environments — staging and production — that deploy on merge, hold their
secrets properly, and can be restored after a mistake.

**Acceptance criteria**
- Merging to `main` deploys to staging automatically; production is a manual promotion.
- No secret exists in the repository, in a build log, or in a client bundle.
- The LaTeX service is reachable only from the API, never from the internet.
- The database has automated backups and a rehearsed restore.
- A bad deploy can be rolled back in under five minutes.

## Technical plan

### Topology

| Component | Where | Notes |
| --- | --- | --- |
| Web | Vercel | Preview per PR, staging on `main`, production on promotion |
| API | Fly.io app `rg-api` | Public, behind HTTPS, 2 machines minimum in production |
| LaTeX | Fly.io app `rg-latex` | **No public IP.** Private 6PN networking only |
| Worker | Fly.io app `rg-worker` | Only if RG-052 has fired |
| Postgres + Storage + Auth | Supabase | One project per environment, never shared |
| Redis | Upstash | Only if RG-052 has fired |

### Files
```
.github/workflows/deploy-staging.yml
.github/workflows/deploy-production.yml     manual dispatch + environment approval
fly.api.toml  fly.latex.toml  fly.worker.toml
infra/README.md                             runbook: deploy, rollback, restore, rotate
infra/checklist-go-live.md
```

### Steps
1. **Environments.** `staging` and `production` as GitHub Environments, production requiring a
   manual approval. Each holds its own secret set. `.env.example` remains the canonical list of
   names; no environment may define a name absent from it (assert in CI).
2. **Secret discipline.** The Supabase **service-role key exists only in the API's secret store** —
   never in Vercel, never in a `NEXT_PUBLIC_` variable, never in a preview environment. Add a CI
   check that greps the built web bundle for the service-role prefix and for any `sk-` string, and
   fails the build on a hit.
3. **Network.** `rg-latex` gets no public IP; the API reaches it over `rg-latex.internal`.
   API CORS allows exactly the web origins for that environment — no wildcard, in any environment.
   Supabase RLS is verified against staging by running the RG-002 pgTAP suite post-deploy.
4. **Migrations.** Applied by the deploy job before the new API version starts, and required to be
   backward-compatible with the previous release so a rollback does not need a down-migration.
   Expand-then-contract: add a column in one release, stop reading the old one in the next.
5. **Backups.** Supabase daily backups plus point-in-time recovery on production. A restore is
   **rehearsed once into staging** as part of this ticket — an untested backup is not a backup.
6. **Health and rollback.** `/v1/health` drives Fly's checks; a failing deploy does not take
   traffic. Rollback is `fly releases rollback` for the API and a Vercel instant rollback for the
   web, both written into `infra/README.md` with the exact commands.
7. **Cost and limits.** Set a Fly hard scale cap and a Supabase spend cap. A runaway loop should
   fail, not bill.
8. **Go-live checklist** (`infra/checklist-go-live.md`), all items verified before the first
   production promotion: custom domain and TLS, OAuth redirect URLs for the production origin,
   `allowed_emails` seeded, Sentry receiving from both apps, backups confirmed, restore rehearsed,
   secret-scan check green, rate limits on the public interest endpoint, LaTeX container confirmed
   unreachable from the internet.

### Tests
- Staging deploy is green end to end, and a smoke test signs in and completes a fake-mode run.
- The secret-scan CI check fails against a branch that deliberately leaks a key, then is reverted.
- `rg-latex` is unreachable from a public IP (assert from a runner outside the private network).
- A staging restore from backup produces the expected row counts.
- A rollback returns the previous version within five minutes, timed and recorded in the runbook.

### Definition of done
Five checks recorded in `infra/README.md` with dates; the go-live checklist fully ticked.

### Out of scope
Multi-region, autoscaling policy, SOC2-style compliance work.
