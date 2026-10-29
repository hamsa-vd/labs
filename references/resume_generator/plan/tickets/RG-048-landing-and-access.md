# RG-048 — Landing page and access screens

**Epic:** E — Screens · **Depends on:** RG-003, RG-011 · **Estimate:** M · **Labels:** web, product

## Product requirement

**Problem.** The product is invite-only, so most visitors cannot sign in. They still need to
understand what it is and be able to ask for access.

**Acceptance criteria**
- A visitor understands in one screen what the product does and why the evidence gate matters.
- Signing in is one click.
- An uninvited visitor lands on register-interest, not on an error.
- The page is fast: no layout shift, no render-blocking third-party script.

## Technical plan

### Files
```
apps/web/src/app/page.tsx                        single column, full width
apps/web/src/components/landing/Hero.tsx
apps/web/src/components/landing/ProductShot.tsx  static screenshot, cool-neutral, hairline + radius
apps/web/src/components/landing/ValueProps.tsx   three, no icon-in-tinted-square grid
apps/web/src/components/landing/HowItWorks.tsx   four numbered steps
apps/web/src/app/(auth)/no-access/page.tsx       register interest
```

### Copy direction (arey voice — declarative, no selling)
Hero: what it does, in one sentence, plus the honest constraint. Something in the register of
"Tailor a resume to a job description, then score it the way an ATS and a human reviewer would."
Sub-line states the position that makes the product different: it will not add a keyword you
cannot evidence.

Three value props, one line each: tailored generation from a single source of truth; scoring on
both dimensions; an evidence gate that keeps the resume true. No exclamation marks. No emoji.

How it works: paste the job description → the system drafts and reviews → you resolve missing
keywords with evidence → export the PDF.

### Steps
1. Single column, `--content-max`, generous 80px section rhythm. Static — no scroll animation,
   no parallax.
2. `ProductShot` is a real screenshot of the result view, desaturated toward the greyscale
   palette, inset with `--radius-card` and a hairline. Reserve its aspect ratio in CSS so there is
   no layout shift. Use `next/image` with a blur placeholder.
3. One primary action, "Sign in with Google", repeated at the top and bottom. Nothing else competes.
4. `/no-access`: one paragraph explaining invite-only, a short form (email, one line about their
   situation) posting to `POST /public/interest`, and a confirmation that does not promise a date.
5. Lighthouse: performance and accessibility both ≥ 95.

### Tests
- Playwright: the sign-in button starts the OAuth flow.
- Register-interest submits and shows the confirmation state.
- Lighthouse CI thresholds enforced in the pipeline.
- No CLS from the product shot (assert the reserved aspect ratio).

### Definition of done
Four checks green.

### Out of scope
Marketing site, blog, pricing.
