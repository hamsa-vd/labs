# Ascend

Invite-only job-application tracker. Reads Gmail read-only, classifies with a
local model on a Mac Mini, and keeps an append-only event log per application.

Scaffolding only; production UI is not implemented. Design reference:
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

Components come from `@hamsa-designs/arey`. Two things are load-bearing:

- `next.config.ts` sets `transpilePackages`. The package exports raw `.jsx` from
  `node_modules` and SWC skips `node_modules` by default, so without it the
  first component import fails the build.
- `pnpm design-system:css` extracts component CSS to
  `src/generated/arey-components.css`, which the root layout imports. arey
  injects that CSS at runtime and its injector no-ops on the server, so without
  the extraction step SSR ships unstyled HTML that restyles on hydration (§12.1).
  Runs automatically on `predev` and `prebuild`.

## Commands

```sh
pnpm dev                  # extracts design-system CSS, then next dev
pnpm check                # lint, typecheck, test
pnpm sync:backfill        # first import for an account
pnpm sync:incremental     # history-based delta; launchd runs this every 10 min
pnpm eval                 # score the golden set in evals/fixtures
pnpm design-system:css    # regenerate component CSS after an arey upgrade
```

Copy `.env.example` to `.env.local` only when integration work begins. Never
commit credentials or Gmail content.

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
