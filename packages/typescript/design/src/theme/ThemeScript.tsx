export interface ThemeScriptProps {
  /** Same-origin URL serving the bootstrap script — see `createThemeScriptResponse`. */
  src: string;
}

/**
 * Renders the pre-hydration theme bootstrap in `<head>`.
 *
 * External `<script src>`, not inline: a `script-src 'self'` CSP with no
 * `'unsafe-inline'`/nonce (a common default) silently blocks inline script content
 * while still allowing a same-origin external script — see the doc comment on
 * `themeScript`. Server-renderable — no `'use client'` needed. The consuming app's
 * root `<html>` element must set `suppressHydrationWarning` since this script
 * mutates `data-theme` before React reconciles.
 */
export function ThemeScript({ src }: ThemeScriptProps) {
  // eslint-disable-next-line @next/next/no-sync-scripts
  return <script src={src} />;
}
