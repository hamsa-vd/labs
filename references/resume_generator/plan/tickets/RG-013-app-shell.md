# RG-013 — Authenticated app shell

**Epic:** B — Design system · **Depends on:** RG-011, RG-012 · **Estimate:** M · **Labels:** design-system, web

## Product requirement

**Problem.** Six screens need one consistent frame: where am I, how do I get elsewhere, who am I
signed in as, and how do I start a new application from anywhere.

**Acceptance criteria**
- The active screen is unmistakable in the nav.
- "New application" is reachable in one click from every screen.
- Under 940px the sidebar becomes a hamburger sheet; nothing is unreachable at 360px.
- A run in progress shows a persistent indicator in the shell, on any screen.

## Technical plan

### Files
```
apps/web/src/components/shell/AppShell.tsx
apps/web/src/components/shell/Sidebar.tsx        264px, independent scroll, 24px bottom mask
apps/web/src/components/shell/TopBar.tsx         56px sticky, glass
apps/web/src/components/shell/MobileNav.tsx      hamburger → sheet, <940px
apps/web/src/components/shell/UserMenu.tsx       avatar → popover: theme, settings, sign out
apps/web/src/components/shell/ActiveRunBadge.tsx subscribes to the in-flight run (RG-032)
```

### Structure
Sidebar sections, in order: **Pipeline**, **New application** (primary Button, not a nav row),
then a divider, then **Source of truth**, **Templates**, **Settings**. The arey wordmark
(`assets/logo.svg`, `currentColor` stroke) sits at the top; a lowercase `arey` text lockup is
used below the size at which the sketch stays legible.

### Steps
1. `AppShell` is a server component; only `MobileNav`, `UserMenu`, and `ActiveRunBadge` are client.
2. Active state from `usePathname()`: `--bg-selected` fill + `--text-accent` label. No left stripe.
3. Top bar is `position: sticky` with glass — the glass **is** the scroll protection; no gradient
   fade. The sidebar's long list gets the 24px bottom gradient mask.
4. A 1px indeterminate accent bar sits under the top bar during route transitions and while a run
   is active — the arey loading pattern. No skeleton shimmer.
5. Below 940px: hamburger opens a left sheet (`--radius-sheet`, glass, focus-trapped, Escape and
   backdrop close, focus returns to the trigger). Nav rows are ≥44px tall.
6. `ActiveRunBadge` shows `company · role` and the current node name, and links to the run page.
   It is the reason a user can navigate away from a generation and come back.

### Tests
- Playwright: nav to each route marks exactly one row active.
- At 900px the sidebar is absent and the hamburger opens a focus-trapped sheet; Escape closes it
  and returns focus.
- With a mocked in-flight run, the badge appears on the settings screen and links correctly.
- `jest-axe` on the shell: zero violations; skip-to-content link present.

### Definition of done
All four tests green at 360, 940, and 1440px.

### Out of scope
Screen content.
