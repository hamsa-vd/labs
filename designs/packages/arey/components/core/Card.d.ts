export interface CardProps {
  /** glass = floating layer over content. inset = recessed well. flat = no shadow. */
  variant?: 'default' | 'flat' | 'inset' | 'glass';
  /** Adds hover lift, press scale, and focus ring; renders a <button> unless `as` is set. */
  interactive?: boolean;
  title?: React.ReactNode;
  description?: React.ReactNode;
  /** Trailing element in the header — usually an IconButton or Badge. */
  action?: React.ReactNode;
  /** Footer strip on a subtle fill, separated by a hairline. */
  footer?: React.ReactNode;
  /** Set false for full-bleed content such as a table or image. */
  padded?: boolean;
  as?: keyof JSX.IntrinsicElements;
  className?: string;
  children?: React.ReactNode;
}
export declare function Card(props: CardProps): JSX.Element;
