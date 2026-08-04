import { themeScript, type ThemeScriptOptions } from './theme-script.js';

/**
 * Builds a `Response` serving the theme bootstrap script, for a route handler:
 *
 * ```ts
 * // app/api/labs-theme/route.ts
 * import { createThemeScriptResponse } from '@labs/design';
 * import { areyAdapter } from '@labs/design/arey';
 *
 * export function GET() {
 *   return createThemeScriptResponse({ storageKey: 'ascend-theme', adapter: areyAdapter });
 * }
 * ```
 *
 * `Content-Type` is set explicitly because apps commonly send
 * `X-Content-Type-Options: nosniff`, under which browsers refuse to execute a
 * `<script src>` whose response isn't a recognized JavaScript MIME type.
 */
export function createThemeScriptResponse(options: ThemeScriptOptions): Response {
  return new Response(themeScript(options), {
    headers: {
      'Content-Type': 'text/javascript; charset=utf-8',
      'Cache-Control': 'public, max-age=300',
    },
  });
}
