import { createThemeScriptResponse } from '@labs/design';
import { areyAdapter } from '@labs/design/arey';

// Served same-origin so it satisfies the `script-src 'self'` CSP in next.config.ts
// without an inline-script allowance. Must stay reachable on public pages too —
// see access_zones.bypass in project.yaml.
export function GET() {
  return createThemeScriptResponse({ storageKey: 'ascend-theme', adapter: areyAdapter });
}
