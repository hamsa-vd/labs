export interface IconButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  /** Phosphor icon name. */
  icon: string;
  /** Required accessible label — icon-only controls always carry one. */
  label: string;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'ghost' | 'bordered';
  /** Pill shape. Used for avatars menus and floating controls. */
  round?: boolean;
  weight?: 'regular' | 'bold' | 'fill';
}
export declare function IconButton(props: IconButtonProps): JSX.Element;
