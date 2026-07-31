# arey Console — UI kit

The web-app surface: a 264px sidebar, a sticky glass top bar, and a 1120px content column.

## Screens
- **Overview** (`Overview.jsx`) — usage metrics, project grid, activity and members. The default view.
- **Deployments** (`Deployments.jsx`) — filterable table plus the "New deployment" dialog.
- **Deployment detail** (`Deployments.jsx` → `DeploymentDetail`) — build log, status panel, domain card. Reached by clicking any table row.
- **Settings** (`Settings.jsx`) — row-layout fields, toggle list, API keys, destructive confirm dialog.
- Any other sidebar item renders a deliberate "not part of this kit" empty state rather than an invented screen.

## Shell parts (`Shell.jsx`)
`Sidebar` · `TopBar` · `PageHead` · `Page` · `StatusDot` · `ThemeToggle`

## Interactions to try
- Click a deployment row → detail view → **Deployments** to go back.
- **New deployment** → dialog (Escape or scrim click closes).
- Search and tab filters on Deployments narrow the table live; clearing shows the empty state.
- The sun/moon button in the top bar swaps `data-theme` on `<html>` — every surface, border and shadow re-resolves.
- **Delete project** in Settings opens the type-to-confirm dialog.

## Notes
Composes the published components only — no primitive is re-implemented here. Data lives in `data.jsx`. Everything else is presentational.
