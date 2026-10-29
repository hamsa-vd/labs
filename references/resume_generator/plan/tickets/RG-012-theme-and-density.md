# RG-012 — Theming, dark mode, and responsive foundations

**Epic:** B — Design system · **Depends on:** RG-010, RG-005 · **Estimate:** S · **Labels:** design-system, web

## Product requirement

**Problem.** The v1 prototype has a working light/dark toggle and a 940px responsive break. Both
have to be real, persisted, and flash-free.

**User story.** I set dark mode once and every device I sign in on respects it, with no white
flash on load.

**Acceptance criteria**
- Three theme choices: light, dark, system. Persisted to the profile, not just the browser.
- No flash of the wrong theme on first paint, including on a hard refresh.
- Every layout works from 360px to 1920px with no horizontal scroll.

## Technical plan

### Files
```
apps/web/src/lib/theme.tsx                 provider + useTheme
apps/web/src/app/theme-script.tsx          blocking inline script
apps/web/src/styles/breakpoints.ts         sm 600, md 940, lg 1200, xl 1440
apps/api/resume_api/routers/profile.py     PATCH /v1/profile { theme }
```

### Steps
1. Inline script in `<head>` reads `localStorage.theme` (or `matchMedia`) and sets
   `document.documentElement.dataset.theme` before paint. It is the only blocking script.
2. `useTheme().set(t)` writes localStorage, updates the attribute, and fires `PATCH /v1/profile`
   optimistically. On sign-in the server value seeds localStorage.
3. Theme transition is opacity-only at 80ms per the arey guide — never a colour transition on
   every element.
4. **940px is the shell breakpoint** (matching the v1 prototype): above, a persistent 264px
   sidebar; below, a glass top bar with a hamburger opening a sheet. RG-013 implements the chrome;
   this ticket owns the token and the media-query helper.
5. Content caps: `--content-max` 1120px centred; prose at `--prose-max` 68ch.

### Tests
- Playwright: set dark, hard reload, assert the first painted frame is dark (no flash).
- Theme persists across sign-out and sign-in on a second browser context.
- Viewport sweep at 360/600/940/1200/1920 — no horizontal overflow on any route.

### Definition of done
All three tests green.

### Out of scope
Nav chrome (RG-013).
