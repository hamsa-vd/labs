# Ascend

Invite-only job-application tracker. Reads Gmail read-only, classifies with a
local model on a Mac Mini, and keeps an append-only event log per application.

The production foundation, authenticated tracker UI, public invite flow,
classification pipeline, Gmail worker, and versioned API are implemented. The
remaining launch work is environment integration and acceptance testing against
real Cloudflare, Google, Postgres, Ollama, and Mac Mini services. Design reference:
`archive/ascend-architecture.md`, and section numbers below point into it.
`archive/index.html` is the Claude Design prototype, a behavioural and visual
reference rather than production code.

## Runtime boundaries

- Next.js serves the web/PWA client and the versioned HTTP API. Route group
  `(public)` bypasses Cloudflare Access; `(authenticated)` sits behind it (§2.5).
- Server modules own domain, application and infrastructure layers.
- Worker commands run outside the request lifecycle, scheduled by `launchd` (§8).
- Supabase Postgres is the durable store. Message bodies are never persisted (§2.6).
- Classification runs locally through Ollama. Sending email content to a hosted
  model would breach Google's Limited Use terms, so this is the compliant
  architecture rather than a cost optimisation (§7).

## Design system

Design-system usage is centralized in `@labs/design` (`packages/typescript/design`),
which wraps `@hamsa-designs/arey` behind the `arey` adapter — `@labs/design/arey`
(components + `ThemeToggle`) and `@labs/design/arey.css` (tokens, vendored icon
fonts, and component CSS, pre-harvested at `@labs/design`'s own build time so SSR
always renders styled HTML; see `packages/typescript/design/scripts/build-arey-css.ts`).
Color-mode switching (`data-theme` on `<html>`, persistence, pre-hydration bootstrap)
is DS-agnostic core in `@labs/design`, rendered via `<ThemeScript adapter={areyAdapter}
storageKey="ascend-theme" />` in `app/layout.tsx`. Both packages ship compiled JS, so
no `transpilePackages` entry is needed.

## Commands

```sh
pnpm dev                  # next dev
pnpm check                # lint, typecheck, test
pnpm sync:backfill        # first import for an account
pnpm sync:incremental     # dispatches jobs every minute; accounts become due after 10 min
pnpm eval                 # score the golden set in evals/fixtures
pnpm audit:persistence    # fail if bodies, evidence text, or plaintext token columns exist
```

Copy `.env.example` to `.env.local` only when integration work begins. Never
commit credentials or Gmail content.

## Launch gates

- Apply `0001_initial_schema.sql` and `0002_production_foundation.sql` to the
  production database, then run `pnpm audit:persistence`.
- Run the opt-in Postgres cases with `TEST_DATABASE_URL=... pnpm test`.
- Set `ASCEND_PRIVATE_GOLDEN_SET` to the gitignored, Mac-Mini-only real fixture
  set and keep `pnpm eval` green at the documented release thresholds.
- Complete and record the Google OAuth day-eight refresh-token experiment before
  granting access to real users.

## Where the risk is

- **OAuth publishing status.** The app must be "In production" and unverified.
  Testing status expires every refresh token after 7 days and kills the product.
  Verify with a throwaway account over 8 days before onboarding anyone (§2.3).
- **Status projection.** Latest event wins, but never regress out of a terminal
  state. Both obvious rules are wrong; see `src/domain/status-projection.ts`.
- **Entity resolution.** The key is `(company, role)`, not company alone. One
  company routinely runs two concurrent applications (§5).
- **Prompt injection.** Every email is attacker-controlled text entering a
  prompt. The classifier has a small blast radius; the overview digest does not,
  and must read structured rows only (§13).
- **Dates.** `scheduled_at` and `deadline_at` are the only data a user can
  genuinely miss. Score them as their own eval category (§11.3.2).
