export interface SwitchProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: React.ReactNode;
  description?: React.ReactNode;
  /** success (green, the iOS-flavoured default) or accent (blue). */
  tone?: 'success' | 'accent';
  size?: 'sm' | 'md';
}
export declare function Switch(props: SwitchProps): JSX.Element;
