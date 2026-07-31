/** arey's action control. */
export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  /** primary = the one accented action per view. secondary is the workhorse. */
  variant?: 'primary' | 'secondary' | 'ghost' | 'inverse' | 'danger' | 'link';
  /** 28 / 36 / 44px. lg on mobile and marketing surfaces. */
  size?: 'sm' | 'md' | 'lg';
  /** Phosphor icon name shown before the label. */
  iconLeft?: string;
  /** Phosphor icon name shown after the label. */
  iconRight?: string;
  /** Replaces the leading icon with a spinner and blocks interaction. */
  loading?: boolean;
  /** Fills the container width. */
  block?: boolean;
  disabled?: boolean;
  /** Render as another element, e.g. "a" for a linked button. */
  as?: 'button' | 'a';
  children?: React.ReactNode;
}
export declare function Button(props: ButtonProps): JSX.Element;
