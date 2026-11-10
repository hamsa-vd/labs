export interface BadgeProps {
  tone?: 'neutral' | 'accent' | 'success' | 'danger' | 'warning' | 'outline';
  /** 6px leading dot — the system's default status indicator. */
  dot?: boolean;
  /** Phosphor icon name, 12px bold. Use instead of a dot, not with it. */
  icon?: string;
  size?: 'sm' | 'md';
  /** Mono face — for versions, SHAs, and counts. */
  mono?: boolean;
  className?: string;
  children?: React.ReactNode;
}
export declare function Badge(props: BadgeProps): JSX.Element;
