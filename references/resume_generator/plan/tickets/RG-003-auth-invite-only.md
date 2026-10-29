# RG-003 — Google sign-in with invite-only access

**Epic:** A — Foundations · **Depends on:** RG-002 · **Estimate:** M · **Labels:** foundation, auth

## Product requirement

**Problem.** v1 has no concept of a user. v2 needs one identity per person, and access is
closed while the product is early.

**User story.** As an invited person I sign in with Google and land in my own workspace. As an
uninvited person I see a register-interest screen instead of an error.

**Acceptance criteria**
- Sign in with Google is the only auth method.
- An email absent from `allowed_emails` is signed straight back out and shown register-interest.
  No half-created account is left behind.
- Session survives a refresh and a server restart.
- Every API route rejects a request with no valid Supabase JWT with `401`.

## Technical plan

### Files
```
apps/web/src/lib/supabase/client.ts        browser client
apps/web/src/lib/supabase/server.ts        RSC/route-handler client (cookie-based)
apps/web/src/middleware.ts                 session refresh + route guard
apps/web/src/app/(auth)/sign-in/page.tsx
apps/web/src/app/(auth)/callback/route.ts  exchanges code, runs the allowlist check
apps/web/src/app/(auth)/no-access/page.tsx register-interest
apps/api/resume_api/auth.py                get_current_user dependency
apps/api/resume_api/middleware/auth.py
supabase/migrations/0011_allowlist_guard.sql
```

### Steps
1. Enable the Google provider in Supabase Auth; redirect URL `/(auth)/callback`.
2. In the callback route: exchange the code, read the session email, `select 1 from allowed_emails
   where email = ...`. If absent → `supabase.auth.signOut()` and redirect `/no-access`. If present
   → stamp `redeemed_at` and redirect `/pipeline`.
3. Also enforce server-side: a Postgres `before insert` trigger on `profiles` raises unless the
   email is allowlisted. The client check is UX; the trigger is the actual gate.
4. `middleware.ts`: refresh the session cookie on every request; redirect unauthenticated users
   away from `/(app)/*` to `/sign-in`.
5. API: `get_current_user` verifies the JWT against the Supabase JWKS, returns `UserContext(id,
   email)`, and is a dependency on the whole authenticated router. Never trust a `user_id` from a
   request body — it always comes from the token.
6. Register-interest form posts to `POST /public/interest` (rate-limited, unauthenticated) which
   inserts into an `interest_requests` table.

### Tests
- API: request with no token → 401; with a token for user A → `UserContext.id == A`.
- API: a request body carrying a foreign `user_id` is ignored, not honoured.
- Web (Playwright): allowlisted email reaches `/pipeline`; non-allowlisted lands on `/no-access`
  with no session cookie remaining.

### Definition of done
Both tests green; no route in `/(app)` renders for an anonymous visitor.

### Out of scope
Admin UI for issuing invites (RG-051). Seed the first cohort with SQL.
