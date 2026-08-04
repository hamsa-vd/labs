import { registerAdapter, type Adapter } from '../../theme/adapter.js';
import { IconButton } from '@hamsa-designs/arey/react';

export * from '@hamsa-designs/arey/react';

export const areyAdapter: Adapter = registerAdapter({
  name: 'arey',
  defaultTheme: 'dark',
  toggleAttr: 'data-theme-toggle',
  iconSync: {
    selector: '.arey-icon i',
    darkClass: 'ph-sun',
    lightClass: 'ph-moon',
  },
});

/** arey's themed toggle control, wired to the bootstrap script via `data-theme-toggle`. */
export function ThemeToggle() {
  // The global bootstrap script owns the actual toggling so it works before, or without,
  // React hydration — see `themeScript`/`ThemeScript` in `@labs/design`.
  return <IconButton icon="sun" label="Switch theme" data-theme-toggle="true" />;
}
