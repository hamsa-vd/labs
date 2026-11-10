export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  size?: 'sm' | 'md' | 'lg';
  /** Phosphor icon name inset on the left, 16px. */
  icon?: string;
  /** Trailing content — a Kbd, a unit, or an IconButton. */
  suffix?: React.ReactNode;
  /** Mono face for keys, SHAs, URLs and IDs. */
  mono?: boolean;
  invalid?: boolean;
}
export declare function Input(props: InputProps): JSX.Element;
