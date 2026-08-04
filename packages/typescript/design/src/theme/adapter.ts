/** How a design system's icon marker should react to a theme change. */
export interface IconSync {
  /** CSS selector (relative to document) for icon elements to update on toggle. */
  selector: string;
  /** Class applied to matched icons when the active theme is dark. */
  darkClass: string;
  /** Class applied to matched icons when the active theme is light. */
  lightClass: string;
}

/** Metadata a design-system adapter supplies to the theme bootstrap. */
export interface Adapter {
  name: string;
  defaultTheme: 'light' | 'dark';
  /** Attribute marking elements that toggle the theme on click. */
  toggleAttr?: string;
  iconSync?: IconSync;
}

const registry = new Map<string, Adapter>();

/** Adapters call this at module scope so `@labs/design` can enumerate known design systems. */
export function registerAdapter(adapter: Adapter): Adapter {
  registry.set(adapter.name, adapter);
  return adapter;
}

export function listAdapters(): Adapter[] {
  return Array.from(registry.values());
}
