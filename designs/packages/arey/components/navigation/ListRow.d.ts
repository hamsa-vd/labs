export interface ListRowProps {
  /** Phosphor icon name, 17px. */
  icon?: string;
  /** Custom leading element — an Avatar or status dot. Overrides `icon`. */
  leading?: React.ReactNode;
  title: React.ReactNode;
  subtitle?: React.ReactNode;
  /** Right-aligned secondary value. */
  value?: React.ReactNode;
  /** Mono face for the value — durations, sizes, versions. */
  mono?: boolean;
  /** Trailing control — a Switch, Badge, or IconButton. */
  trailing?: React.ReactNode;
  /** Disclosure caret. Mobile navigation rows. */
  chevron?: boolean;
  /** Providing onClick makes the row a button with hover and press states. */
  onClick?: () => void;
  as?: keyof JSX.IntrinsicElements;
  className?: string;
}
export declare function ListRow(props: ListRowProps): JSX.Element;
export interface ListProps {
  /** Hairline between rows. */
  divided?: boolean;
  /** iOS grouped-card container: card fill, 16px radius, clipped. */
  inset?: boolean;
  className?: string;
  children?: React.ReactNode;
}
export declare function List(props: ListProps): JSX.Element;
