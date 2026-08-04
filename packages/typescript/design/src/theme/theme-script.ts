import type { Adapter } from './adapter.js';

export interface ThemeScriptOptions {
  /** localStorage key the chosen theme is persisted under. Namespace per app, e.g. "ascend-theme". */
  storageKey: string;
  adapter: Adapter;
}

/**
 * Builds the source of a synchronous, pre-hydration theme-bootstrap script.
 *
 * Design-system agnostic and framework-agnostic on purpose: it must run before React
 * hydrates (as a plain `<script>` in `<head>`) so `data-theme` on `<html>` is correct
 * before first paint — no FOUC. Toggling and icon-sync are wired through the adapter's
 * `toggleAttr` / `iconSync`, not hardcoded to any one design system.
 *
 * React's hydration of the root `<html>` element resets `data-theme` back to its
 * JSX-declared default once, even with `suppressHydrationWarning` (that flag only
 * silences the console warning, it doesn't stop the attribute from being reconciled
 * to the server-rendered value) — with no further React re-render, nothing then
 * corrects it. A `MutationObserver` snaps the attribute back to the script's own
 * source of truth whenever it changes to something else, which self-heals that one
 * hydration reset without fighting the user's own toggle clicks (those update the
 * tracked "current" value and the DOM together, so the observer sees no mismatch).
 *
 * This returns source text, not a tag — render it as an external, same-origin
 * `<script src>` (see `createThemeScriptResponse` / `ThemeScript`), not inline via
 * `dangerouslySetInnerHTML`. Apps commonly ship a `script-src 'self'` CSP with no
 * `'unsafe-inline'`/nonce, which silently blocks inline `<script>` content (and fails
 * without a console error under most CSP report-only setups) while still allowing a
 * same-origin external script.
 */
export function themeScript({ storageKey, adapter }: ThemeScriptOptions): string {
  const toggleAttr = adapter.toggleAttr ?? 'data-theme-toggle';
  const iconSync = adapter.iconSync;

  return `(() => {
  const storageKey = ${JSON.stringify(storageKey)};
  const toggleAttr = ${JSON.stringify(toggleAttr)};
  const defaultTheme = ${JSON.stringify(adapter.defaultTheme)};
  const iconSync = ${iconSync ? JSON.stringify(iconSync) : 'null'};

  function readTheme() {
    try {
      const stored = localStorage.getItem(storageKey);
      if (stored === 'light' || stored === 'dark') return stored;
    } catch {}
    return document.documentElement.dataset.theme === 'light' ? 'light' : defaultTheme;
  }

  function syncIcons(theme) {
    if (!iconSync) return;
    document.querySelectorAll('[' + toggleAttr + '] ' + iconSync.selector).forEach((icon) => {
      icon.classList.toggle(iconSync.darkClass, theme === 'dark');
      icon.classList.toggle(iconSync.lightClass, theme === 'light');
    });
  }

  let current;

  function applyTheme(theme) {
    current = theme;
    document.documentElement.dataset.theme = theme;
    try {
      localStorage.setItem(storageKey, theme);
    } catch {}
    syncIcons(theme);
  }

  applyTheme(readTheme());

  // Self-heal the one-time hydration reset of data-theme (see doc comment above).
  new MutationObserver(() => {
    if (document.documentElement.dataset.theme !== current) {
      document.documentElement.dataset.theme = current;
      syncIcons(current);
    }
  }).observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });

  document.addEventListener('click', (event) => {
    const target = event.target;
    const toggle = target instanceof Element ? target.closest('[' + toggleAttr + ']') : null;
    if (!toggle) return;
    event.preventDefault();
    event.stopPropagation();
    applyTheme(current === 'dark' ? 'light' : 'dark');
  }, true);

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => syncIcons(current), { once: true });
  }
})();`;
}
