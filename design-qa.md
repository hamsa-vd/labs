# Ascend welcome visual QA

## Source visual truth

- Source: `apps/ascend/archive/index.html`, signed-out state served at `http://localhost:3200/`.
- Reference capture: `/private/tmp/ascend-welcome-reference.png`.
- Reference viewport: 1512 x 805 CSS pixels, density 1.

## Implementation

- Implementation: `http://localhost:3001/welcome` during local preview.
- Matching top-viewport capture: `/private/tmp/ascend-welcome-implementation-top.png`.
- Full-page capture: `/private/tmp/ascend-welcome-implementation.png`.
- Implementation viewport: 1512 x 805 CSS pixels for the matching capture, density 1.
- Full-page rendered height: 2141 pixels.
- State: dark theme, signed-out/public state, initial sign-in card.

## Comparison

The implementation now matches the archive's signed-out composition: full-width glass navigation, Instrument Sans/Space Mono typography, blue ambient backdrop, decorative lens artwork, centered hero/card proportions, source copy, four-step process panel, local-classification illustration, CTA, and footer.

The implementation preserves production behavior behind the visual layer: `/overview` remains the sign-in destination, `/privacy` and `/status` remain real routes, and the invite request form remains connected to `/api/v1/invite-requests`.

## Findings

- [P2] Browser interaction verification is blocked by a Next.js client-side development/preview error (`Expected a request ID to be defined for the document` in dev and `Connection closed` against the standalone preview). The page renders, but Chrome did not reliably apply the React state change for the invite toggle. This appears to be a local Next.js/browser preview issue; the production build itself succeeds.

## Verification history

1. Initial implementation was compared against the archive at the same viewport.
2. Header horizontal padding was corrected from centered content padding to the archive's fixed 28px edge padding.
3. The revised top viewport was recaptured and visually aligned with the archive.

## Final result

blocked
