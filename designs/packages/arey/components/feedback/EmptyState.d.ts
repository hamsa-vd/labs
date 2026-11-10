export interface EmptyStateProps {
  /** Phosphor icon name, 24px in a 56px inset tile. */
  icon?: string;
  title: React.ReactNode;
  description?: React.ReactNode;
  /** Exactly one action. */
  action?: React.ReactNode;
  compact?: boolean;
  className?: string;
}
export declare function EmptyState(props: EmptyStateProps): JSX.Element;
