# arey Mobile — UI kit

iOS-style screens: 375×720 device shell, large-title navigation, grouped inset lists, glass tab bar, bottom sheets.

## Parts (`Phone.jsx`)
`Phone` (neutral bezel, no vendor branding) · `StatusBar` · `NavBar` (compact + large title) · `TabBar` (glass, Phosphor `fill` when selected) · `Group` / `GroupLabel` (grouped inset lists) · `Sheet` (bottom sheet, 20px top radius, grabber) · `HomeIndicator`

## Screens (`Screens.jsx`)
- **Projects** — large title, search, filter chips, two grouped sections.
- **Project detail** — identity header, primary actions, segmented range, usage rows.
- **Settings** — profile card, appearance segmented control, toggle groups, sign out.
- **Activity** — grouped feed by day.

## Interactions to try
- Tap any project row → detail; **Projects** in the nav bar goes back.
- **Deploy** opens a bottom sheet; **+** on Projects opens the "New project" sheet. Tap the scrim to dismiss.
- Tab bar switches screens; the selected glyph swaps to Phosphor `fill`.
- Appearance control in Settings, and the Light/Dark switch above the devices, retheme everything.

## Notes
Controls are ≥44px (`--control-h-lg`) on this surface, per the mobile hit-target rule. The three devices share one component library with Console and Docs — nothing is re-implemented for mobile.
