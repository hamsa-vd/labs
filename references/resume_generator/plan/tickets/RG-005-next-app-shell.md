# RG-005 — Next.js app skeleton and routing

**Epic:** A — Foundations · **Depends on:** RG-001, RG-003 · **Estimate:** M · **Labels:** foundation, web

## Product requirement

**Problem.** The v1 prototype (`Resume Agent.dc.html`) proved six screens. They need real routes,
real layouts, and real loading and error states.

**Outcome.** Every screen has a URL, a loading state, and an error state, before any of them has
content.

**Acceptance criteria**
- Deep-linking to any screen works; back and forward behave.
- Every route shows a skeleton while loading, never a blank page or a spinner-on-white.
- An API failure shows a recoverable error state with a retry, not a crashed boundary.

## Technical plan

### Files
```
apps/web/src/app/layout.tsx                 fonts, theme attribute, tokens import
apps/web/src/app/page.tsx                   landing (RG-048)
apps/web/src/app/(app)/layout.tsx           authenticated shell (RG-013)
apps/web/src/app/(app)/pipeline/page.tsx
apps/web/src/app/(app)/applications/new/page.tsx
apps/web/src/app/(app)/applications/[id]/page.tsx
apps/web/src/app/(app)/applications/[id]/runs/[runId]/page.tsx
apps/web/src/app/(app)/source-of-truth/page.tsx
apps/web/src/app/(app)/templates/page.tsx
apps/web/src/app/(app)/settings/page.tsx
    …each with loading.tsx and error.tsx
apps/web/src/lib/api.ts                     server-side client with the auth token attached
apps/web/src/lib/query.ts                   TanStack Query provider + defaults
```

### Steps
1. Route group `(app)` carries the authenticated shell; `(auth)` and `/` do not.
2. Server components fetch through `lib/api.ts` (token from the Supabase server client).
   Client components use TanStack Query against the same generated client.
3. Query defaults: `staleTime` 30 s, one retry, no refetch-on-focus for run data (SSE owns that).
4. `loading.tsx` renders static `--bg-inset` skeleton blocks — no shimmer (ADR-002 / arey).
5. `error.tsx` renders the arey `EmptyState` pattern with the error `code` mapped to a sentence
   and a "Try again" button calling `reset()`.
6. Theme: `data-theme` on `<html>`, resolved from `profiles.theme`, with a no-flash inline script
   reading `localStorage` before paint.

### Tests
- Playwright: each route renders its heading for a signed-in user.
- A forced API 500 renders the error state, and the retry re-requests.

### Definition of done
All nine routes reachable with loading and error states; no hydration warnings in the console.

### Out of scope
Screen content (Epic E), nav chrome (RG-013).
