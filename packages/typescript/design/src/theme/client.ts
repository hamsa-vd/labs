export type ThemeName = 'light' | 'dark';

/** Reads the theme currently applied to `<html data-theme>`. Browser-only. */
export function getTheme(): ThemeName {
  return document.documentElement.dataset.theme === 'light' ? 'light' : 'dark';
}

/** Applies a theme and persists it under `storageKey`, mirroring the bootstrap script. */
export function setTheme(theme: ThemeName, storageKey: string): void {
  document.documentElement.dataset.theme = theme;
  try {
    localStorage.setItem(storageKey, theme);
  } catch {
    // storage may be unavailable (private mode, disabled) — theme still applies for this load
  }
}

export function toggleTheme(storageKey: string): ThemeName {
  const next: ThemeName = getTheme() === 'dark' ? 'light' : 'dark';
  setTheme(next, storageKey);
  return next;
}
