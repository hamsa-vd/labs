export interface TagProps {
  /** Phosphor icon name, 14px. */
  icon?: string;
  /** Pressed appearance — accent wash and border. Only meaningful with onClick. */
  selected?: boolean;
  /** Renders a trailing remove affordance. */
  onRemove?: (e: React.MouseEvent) => void;
  /** Providing onClick makes the tag a selectable filter chip. */
  onClick?: (e: React.MouseEvent) => void;
  className?: string;
  children?: React.ReactNode;
}
export declare function Tag(props: TagProps): JSX.Element;
