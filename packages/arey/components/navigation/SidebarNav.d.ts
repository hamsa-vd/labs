export interface SidebarNavItem { value: string; label: React.ReactNode; icon?: string; count?: number | string; href?: string }
export interface SidebarNavProps {
  /** Grouped items; `label` renders as a mono uppercase eyebrow. */
  groups: Array<{ label?: string; items: SidebarNavItem[] }>;
  value?: string;
  onChange?: (value: string) => void;
  className?: string;
}
export declare function SidebarNav(props: SidebarNavProps): JSX.Element;
