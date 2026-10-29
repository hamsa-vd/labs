# RG-051 — Admin portal: invites and users

**Epic:** F — Operations · **Depends on:** RG-003 · **Estimate:** M · **Labels:** ops

## Product requirement

**Problem.** Access is gated by an `allowed_emails` table seeded with SQL. That is fine for the
first cohort and untenable after it.

**User story.** As the operator I add and revoke invited emails and see who has signed in, from
a UI rather than the Supabase console.

**Acceptance criteria**
- Only an admin can reach the portal; everyone else gets a 404, not a 403.
- I can add emails singly or as a pasted list, and revoke access.
- Revoking access signs the user out and blocks the next sign-in, but does not delete their data.
- I can see registered-interest submissions and invite from that list in one action.

## Technical plan

### Files
```
supabase/migrations/0016_admin_flag.sql       profiles.is_admin bool default false
apps/api/resume_api/routers/admin.py          require_admin dependency
apps/web/src/app/(app)/admin/page.tsx
apps/web/src/components/admin/{InviteList,InterestList}.tsx
```

### Routes
```
GET    /v1/admin/invites          list with redeemed status
POST   /v1/admin/invites          { emails[] } — accepts a pasted, newline-separated list
DELETE /v1/admin/invites/{email}  revoke
GET    /v1/admin/interest         register-interest submissions
GET    /v1/admin/users            email, signed-up, last active, run count
```

### Steps
1. `require_admin` checks `profiles.is_admin`; the first admin is set by SQL. A non-admin hitting
   any `/v1/admin/*` route gets 404 — do not confirm the surface exists.
2. The web route is hidden from the nav entirely for non-admins, and the page itself returns
   `notFound()`.
3. Bulk add parses a pasted list, normalises and deduplicates emails, and reports which were
   already present rather than erroring.
4. Revoke deletes the `allowed_emails` row and invalidates the user's sessions. Data is retained;
   the sign-in gate does the work.

### Tests
- A non-admin gets 404 on every admin route.
- Bulk add of 20 emails with 3 duplicates reports 17 added, 3 skipped.
- Revoke blocks the next sign-in and leaves the user's applications intact.

### Definition of done
Three tests green.

### Out of scope
Impersonation, per-user quotas.
