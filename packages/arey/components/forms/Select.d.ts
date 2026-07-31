export interface SelectOption { value: string; label: string; disabled?: boolean }
export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  /** Strings are used as both value and label. */
  options?: Array<SelectOption | string>;
  size?: 'sm' | 'md' | 'lg';
  /** Renders a leading empty option. */
  placeholder?: string;
  invalid?: boolean;
}
export declare function Select(props: SelectProps): JSX.Element;
